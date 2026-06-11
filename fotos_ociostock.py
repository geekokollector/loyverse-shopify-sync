"""
Carga masiva de imágenes y descripciones desde el catálogo de OcioStock
------------------------------------------------------------------------
Lee catalogo_ociostock.csv (ean;imagen;descripcion) y lo cruza por EAN con
los productos de Shopify:
- Si el producto NO tiene ninguna imagen → sube la imagen oficial
- Si el producto es BORRADOR y no tiene descripción → añade la descripción

Variables de entorno:
  SHOPIFY_TOKEN, SHOPIFY_STORE
  DRY_RUN  "true" (default) = solo informa | "false" = aplica los cambios
"""

import csv
import os
import time
import requests

SHOPIFY_TOKEN = os.environ["SHOPIFY_TOKEN"]
SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"

SH_BASE = f"https://{SHOPIFY_STORE}/admin/api/2024-10"
sh_headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}


def sh_request(method, path, json=None, params=None):
    for _ in range(5):
        r = requests.request(method, f"{SH_BASE}{path}", headers=sh_headers,
                             json=json, params=params or {})
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 2)))
            continue
        r.raise_for_status()
        time.sleep(0.55)
        return r
    raise RuntimeError(f"Shopify rate limit persistente en {path}")


def main():
    print(f"Modo: {'PRUEBA (no cambia nada)' if DRY_RUN else 'APLICANDO CAMBIOS'}\n")

    # 1. Catálogo OcioStock
    catalog = {}
    with open("catalogo_ociostock.csv", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            catalog[row["ean"].strip()] = (row["imagen"].strip(),
                                           row["descripcion"].strip())
    print(f"→ Catálogo OcioStock: {len(catalog)} productos con imagen\n")

    # 2. Productos de Shopify
    print("→ Recorriendo productos de Shopify...")
    img_added, desc_added, no_match = 0, 0, 0
    params = {"limit": 250, "fields": "id,title,images,variants,status,body_html"}
    url = "/products.json"
    while True:
        r = sh_request("GET", url, params=params)
        for p in r.json().get("products", []):
            barcode = ""
            for v in p.get("variants", []):
                if v.get("barcode"):
                    barcode = v["barcode"].strip()
                    break
            if not barcode or barcode not in catalog:
                if not p.get("images"):
                    no_match += 1
                continue
            img_url, desc = catalog[barcode]
            title = p.get("title", "")[:55]
            # Imagen: solo si no tiene ninguna
            if not p.get("images") and img_url:
                if DRY_RUN:
                    print(f"  ✓ [imagen]      {title}")
                else:
                    try:
                        sh_request("POST", f"/products/{p['id']}/images.json",
                                   json={"image": {"src": img_url}})
                        print(f"  🖼 [imagen]      {title}")
                    except requests.HTTPError as e:
                        print(f"  ⚠ [imagen]      {title} → {e}")
                        continue
                img_added += 1
            # Descripción: solo en borradores sin descripción
            if (p.get("status") == "draft"
                    and not (p.get("body_html") or "").strip() and desc):
                if DRY_RUN:
                    print(f"  ✓ [descripción] {title}")
                else:
                    try:
                        sh_request("PUT", f"/products/{p['id']}.json", json={
                            "product": {"id": p["id"],
                                        "body_html": f"<p>{desc}</p>"}
                        })
                        print(f"  📝 [descripción] {title}")
                    except requests.HTTPError as e:
                        print(f"  ⚠ [descripción] {title} → {e}")
                        continue
                desc_added += 1
        link = r.headers.get("Link", "")
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                nxt = part.split(";")[0].strip().strip("<>").split("/admin/api/2024-10")[1]
        if not nxt:
            break
        url, params = nxt, None

    accion = "se añadirían" if DRY_RUN else "añadidas"
    print(f"\n→ Imágenes {accion}: {img_added} | Descripciones {accion}: {desc_added}")
    print(f"→ Productos sin foto que NO están en el catálogo OcioStock: {no_match}")
    print("\n✔ Terminado")


if __name__ == "__main__":
    main()
