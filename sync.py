"""
Sincronización Loyverse → Shopify para Geeko Kollector
--------------------------------------------------------
1. Lee artículos y stock de Loyverse
2. Cruza con variantes de Shopify por CÓDIGO DE BARRAS (respaldo: SKU)
3. Actualiza el inventario en Shopify solo si hay cambios
4. Crea como BORRADOR los productos de Loyverse que no existan en Shopify

Variables de entorno necesarias (GitHub Secrets):
  LOYVERSE_TOKEN      Token de acceso de Loyverse
  SHOPIFY_TOKEN       Admin API token de Shopify (shpat_...)
  SHOPIFY_STORE       Dominio de la tienda, ej: geekollector.myshopify.com
Opcionales:
  LOYVERSE_STORE_ID   ID de la tienda en Loyverse (si tienes varias)
  SAFETY_BUFFER       Unidades de seguridad (ej: 1 → si queda 1, web muestra 0). Default: 0
  CREATE_DRAFTS       "true"/"false" para crear borradores de productos nuevos. Default: true
"""

import os
import sys
import time
import requests

LOYVERSE_TOKEN = os.environ["LOYVERSE_TOKEN"]
SHOPIFY_TOKEN = os.environ["SHOPIFY_TOKEN"]
SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]  # ej: geekollector.myshopify.com
LOYVERSE_STORE_ID = os.environ.get("LOYVERSE_STORE_ID", "")
LOYVERSE_CATEGORIES = [
    c.strip().lower()
    for c in os.environ.get("LOYVERSE_CATEGORIES", "").split(",")
    if c.strip()
]
SAFETY_BUFFER = int(os.environ.get("SAFETY_BUFFER", "0"))
CREATE_DRAFTS = os.environ.get("CREATE_DRAFTS", "true").lower() == "true"

LV_BASE = "https://api.loyverse.com/v1.0"
SH_BASE = f"https://{SHOPIFY_STORE}/admin/api/2024-10"

lv_headers = {"Authorization": f"Bearer {LOYVERSE_TOKEN}"}
sh_headers = {
    "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    "Content-Type": "application/json",
}


def lv_get(path, params=None):
    """GET a Loyverse con reintentos y diagnóstico de errores."""
    last_detail = ""
    for attempt in range(4):
        r = requests.get(f"{LV_BASE}{path}", headers=lv_headers, params=params or {})
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 * (attempt + 1))
            last_detail = f"HTTP {r.status_code}"
            continue
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            last_detail = (f"HTTP {r.status_code}, respuesta no-JSON: "
                           f"{r.text[:200]!r}")
            time.sleep(2 * (attempt + 1))
            continue
    raise RuntimeError(f"Loyverse fallo persistente en {path}: {last_detail}")


def sh_request(method, path, json=None, params=None):
    """Petición a Shopify respetando el rate limit (2 req/s)."""
    for attempt in range(5):
        r = requests.request(
            method, f"{SH_BASE}{path}", headers=sh_headers, json=json, params=params or {}
        )
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        r.raise_for_status()
        time.sleep(0.55)  # ~2 peticiones/segundo máx en plan básico
        return r
    raise RuntimeError(f"Shopify rate limit persistente en {path}")


def set_inventory(location_id, inventory_item_id, qty, label=""):
    """Fija el stock de forma robusta:
    - Si Shopify devuelve 422 (variante sin seguimiento o no conectada a la
      ubicación), activa el seguimiento, conecta la ubicación y reintenta.
    - Si aun así falla, lo registra y continúa sin parar el sync."""
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": qty,
    }
    try:
        sh_request("POST", "/inventory_levels/set.json", json=payload)
        return True
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 422:
            try:
                # 1) activar seguimiento de inventario
                sh_request("PUT", f"/inventory_items/{inventory_item_id}.json", json={
                    "inventory_item": {"id": inventory_item_id, "tracked": True}
                })
                # 2) conectar el artículo a la ubicación
                try:
                    sh_request("POST", "/inventory_levels/connect.json", json={
                        "location_id": location_id,
                        "inventory_item_id": inventory_item_id,
                    })
                except requests.HTTPError:
                    pass  # ya estaba conectado
                # 3) reintentar
                sh_request("POST", "/inventory_levels/set.json", json=payload)
                return True
            except requests.HTTPError as e2:
                print(f"  ⚠ No se pudo fijar stock de '{label}': {e2}")
                return False
        print(f"  ⚠ Error al fijar stock de '{label}': {e}")
        return False


# ---------------------------------------------------------------------------
# 1. LOYVERSE: artículos + stock
# ---------------------------------------------------------------------------

def get_loyverse_category_ids():
    """Devuelve los IDs de las categorías cuyo nombre está en LOYVERSE_CATEGORIES."""
    if not LOYVERSE_CATEGORIES:
        return None
    ids = set()
    cursor = None
    while True:
        params = {"limit": 250}
        if cursor:
            params["cursor"] = cursor
        data = lv_get("/categories", params)
        for c in data.get("categories", []):
            if c.get("name", "").strip().lower() in LOYVERSE_CATEGORIES:
                ids.add(c["id"])
        cursor = data.get("cursor")
        if not cursor:
            break
    if not ids:
        raise RuntimeError(
            f"No se encontró ninguna categoría llamada {LOYVERSE_CATEGORIES} en Loyverse"
        )
    return ids


def get_loyverse_items():
    """Devuelve lista de variantes filtradas por categoría (si LOYVERSE_CATEGORIES
    está definido) y por disponibilidad en la tienda (si LOYVERSE_STORE_ID está
    definido)."""
    category_ids = get_loyverse_category_ids()
    items = []
    cursor = None
    while True:
        params = {"limit": 250}
        if cursor:
            params["cursor"] = cursor
        data = lv_get("/items", params)
        for item in data.get("items", []):
            if category_ids is not None and item.get("category_id") not in category_ids:
                continue  # no es de las categorías Geeko → se ignora
            for v in item.get("variants", []):
                if LOYVERSE_STORE_ID:
                    store_cfg = next(
                        (s for s in v.get("stores", [])
                         if s.get("store_id") == LOYVERSE_STORE_ID),
                        None,
                    )
                    if not store_cfg or not store_cfg.get("available_for_sale", False):
                        continue  # no está activo en la tienda Geeko → se ignora
                items.append({
                    "variant_id": v["variant_id"],
                    "item_name": item.get("item_name", ""),
                    "variant_name": " / ".join(
                        x for x in [v.get("option1_value"), v.get("option2_value"), v.get("option3_value")] if x
                    ),
                    "barcode": (v.get("barcode") or "").strip(),
                    "sku": (v.get("sku") or "").strip(),
                    "price": v.get("default_price"),
                })
        cursor = data.get("cursor")
        if not cursor:
            break
    return items


def get_loyverse_stock():
    """Devuelve dict variant_id -> stock (sumado entre tiendas o filtrado por LOYVERSE_STORE_ID)."""
    stock = {}
    cursor = None
    while True:
        params = {"limit": 250}
        if LOYVERSE_STORE_ID:
            params["store_ids"] = LOYVERSE_STORE_ID
        if cursor:
            params["cursor"] = cursor
        data = lv_get("/inventory", params)
        for lvl in data.get("inventory_levels", []):
            vid = lvl["variant_id"]
            stock[vid] = stock.get(vid, 0) + int(lvl.get("in_stock", 0))
        cursor = data.get("cursor")
        if not cursor:
            break
    return stock


# ---------------------------------------------------------------------------
# 2. SHOPIFY: variantes existentes + location
# ---------------------------------------------------------------------------

def get_shopify_location_id():
    r = sh_request("GET", "/locations.json")
    locations = r.json()["locations"]
    active = [l for l in locations if l.get("active")]
    return (active or locations)[0]["id"]


def get_shopify_variants():
    """Devuelve listas indexadas por barcode y por sku:
       {barcode: {inventory_item_id, variant_id, product_id, inventory_quantity}}"""
    by_barcode, by_sku = {}, {}
    params = {"limit": 250, "fields": "id,title,variants,status"}
    url = "/products.json"
    while True:
        r = sh_request("GET", url, params=params)
        for p in r.json().get("products", []):
            for v in p.get("variants", []):
                entry = {
                    "inventory_item_id": v["inventory_item_id"],
                    "variant_id": v["id"],
                    "product_id": p["id"],
                    "qty": v.get("inventory_quantity", 0),
                    "title": p.get("title", ""),
                }
                bc = (v.get("barcode") or "").strip()
                sku = (v.get("sku") or "").strip()
                if bc:
                    by_barcode[bc] = entry
                if sku:
                    by_sku[sku] = entry
        # Paginación por Link header
        link = r.headers.get("Link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                raw = part.split(";")[0].strip().strip("<>")
                next_url = raw.split("/admin/api/2024-10")[1]
        if not next_url:
            break
        url = next_url
        params = None
    return by_barcode, by_sku


# ---------------------------------------------------------------------------
# 3. SYNC
# ---------------------------------------------------------------------------

def main():
    print("→ Leyendo Loyverse...")
    lv_items = get_loyverse_items()
    lv_stock = get_loyverse_stock()
    print(f"  {len(lv_items)} variantes en Loyverse")

    print("→ Leyendo Shopify...")
    location_id = get_shopify_location_id()
    by_barcode, by_sku = get_shopify_variants()
    print(f"  {len(by_barcode)} variantes con barcode, {len(by_sku)} con SKU en Shopify")

    updated, skipped, not_found, drafts = 0, 0, [], 0

    for item in lv_items:
        lv_qty = lv_stock.get(item["variant_id"], 0)
        target_qty = max(0, lv_qty - SAFETY_BUFFER)

        match = None
        if item["barcode"] and item["barcode"] in by_barcode:
            match = by_barcode[item["barcode"]]
        elif item["sku"] and item["sku"] in by_sku:
            match = by_sku[item["sku"]]

        if match:
            if match["qty"] != target_qty:
                ok = set_inventory(location_id, match["inventory_item_id"],
                                   target_qty, item["item_name"])
                if ok:
                    print(f"  ✓ {item['item_name'][:40]:40} {match['qty']} → {target_qty}")
                    updated += 1
            else:
                skipped += 1
        else:
            not_found.append(item)

    print(f"\n→ Actualizados: {updated} | Sin cambios: {skipped} | No encontrados: {len(not_found)}")

    # ------------------------------------------------------------------
    # 4. Crear borradores para productos nuevos
    # ------------------------------------------------------------------
    if CREATE_DRAFTS and not_found:
        print("\n→ Creando borradores en Shopify...")
        for item in not_found:
            lv_qty = lv_stock.get(item["variant_id"], 0)
            if lv_qty <= 0 and not item["barcode"] and not item["sku"]:
                continue  # sin identificadores ni stock, lo ignoramos
            title = item["item_name"]
            if item["variant_name"]:
                title += f" - {item['variant_name']}"
            payload = {
                "product": {
                    "title": title,
                    "status": "draft",
                    "variants": [{
                        "price": str(item["price"] or 0),
                        "sku": item["sku"],
                        "barcode": item["barcode"],
                        "inventory_management": "shopify",
                    }],
                }
            }
            r = sh_request("POST", "/products.json", json=payload)
            new_product = r.json()["product"]
            inv_item = new_product["variants"][0]["inventory_item_id"]
            target_qty = max(0, lv_qty - SAFETY_BUFFER)
            set_inventory(location_id, inv_item, target_qty, title)
            print(f"  ＋ Borrador: {title[:50]} (stock {target_qty})")
            drafts += 1
        print(f"→ Borradores creados: {drafts}")
    elif not_found:
        import csv
        with open("no_encontrados.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Producto", "Codigo de barras", "SKU", "Precio", "Stock Geeko"])
            for item in not_found:
                w.writerow([
                    item["item_name"] + (f" - {item['variant_name']}" if item["variant_name"] else ""),
                    item["barcode"],
                    item["sku"],
                    item["price"],
                    lv_stock.get(item["variant_id"], 0),
                ])
        print(f"\n→ Lista completa de {len(not_found)} productos sin coincidencia "
              f"guardada en no_encontrados.csv")

    print("\n✔ Sincronización completada")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✖ ERROR: {e}")
        sys.exit(1)
