"""
Extractor de imágenes desde tcgfactory.com para Geeko Kollector
----------------------------------------------------------------
Recorre los productos de Shopify SIN ninguna imagen, busca su EAN en el
buscador público de TCG Factory y, si encuentra la ficha del producto,
copia la imagen principal al producto de Shopify (Shopify la descarga
y la aloja en su propio CDN de forma permanente).

Seguridad y cortesía:
- Verifica que el EAN aparece en la ficha antes de dar la coincidencia por buena
- Pausa de 2 segundos entre peticiones a TCG Factory
- Límite de productos procesados por pasada (MAX_LOOKUPS)
- Modo prueba (DRY_RUN=true): solo informa, no sube nada

Variables de entorno:
  SHOPIFY_TOKEN, SHOPIFY_STORE   (las de siempre)
  DRY_RUN      "true" (default) = solo mirar | "false" = subir imágenes
  MAX_LOOKUPS  máximo de productos a procesar por pasada (default 40)
"""

import os
import re
import time
import requests

SHOPIFY_TOKEN = os.environ["SHOPIFY_TOKEN"]
SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"
MAX_LOOKUPS = int(os.environ.get("MAX_LOOKUPS", "40"))

SH_BASE = f"https://{SHOPIFY_STORE}/admin/api/2024-10"
sh_headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}

TCG_SEARCH = "https://tcgfactory.com/es/buscar?controller=search&s={ean}"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GeekoKollector-ImageBot/1.0"}


def sh_request(method, path, json=None, params=None):
    for attempt in range(5):
        r = requests.request(method, f"{SH_BASE}{path}", headers=sh_headers,
                             json=json, params=params or {})
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 2)))
            continue
        r.raise_for_status()
        time.sleep(0.55)
        return r
    raise RuntimeError(f"Shopify rate limit persistente en {path}")


def tcg_get(url):
    time.sleep(2)  # cortesía con su servidor
    r = requests.get(url, headers=UA, timeout=20)
    if r.status_code != 200:
        return None
    return r.text


def find_product_url(ean):
    """Busca el EAN en TCG Factory y devuelve la URL de la primera ficha."""
    html = tcg_get(TCG_SEARCH.format(ean=ean))
    if not html:
        return None
    # Enlaces de fichas de producto en los resultados (PrestaShop)
    links = re.findall(r'href="(https://tcgfactory\.com/es/[^"]+?\.html)"', html)
    if not links:
        links = re.findall(
            r'<h\d[^>]*class="[^"]*product[^"]*"[^>]*>\s*<a\s+href="([^"]+)"', html)
    return links[0] if links else None


def extract_image(product_url, ean):
    """Abre la ficha, verifica que contiene el EAN y devuelve la imagen principal."""
    html = tcg_get(product_url)
    if not html:
        return None
    if ean not in html:
        return None  # la ficha no menciona ese EAN → coincidencia dudosa, se descarta
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
    if not m:
        m = re.search(r'"large_default"[^}]*?"url":"([^"]+)"', html)
        if m:
            return m.group(1).replace("\\/", "/")
        return None
    return m.group(1)


def main():
    print(f"Modo: {'PRUEBA (no sube nada)' if DRY_RUN else 'SUBIDA ACTIVA'} | "
          f"Límite por pasada: {MAX_LOOKUPS}\n")

    # 1. Productos de Shopify sin ninguna imagen
    print("→ Buscando productos sin imagen en Shopify...")
    candidates = []
    params = {"limit": 250, "fields": "id,title,images,variants"}
    url = "/products.json"
    while True:
        r = sh_request("GET", url, params=params)
        for p in r.json().get("products", []):
            if p.get("images"):
                continue
            barcode = ""
            for v in p.get("variants", []):
                if v.get("barcode"):
                    barcode = v["barcode"].strip()
                    break
            if barcode:
                candidates.append({"id": p["id"], "title": p.get("title", ""),
                                   "barcode": barcode})
        link = r.headers.get("Link", "")
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                nxt = part.split(";")[0].strip().strip("<>").split("/admin/api/2024-10")[1]
        if not nxt:
            break
        url, params = nxt, None

    print(f"  {len(candidates)} productos sin imagen (con EAN)\n")

    # 2. Buscar en TCG Factory
    found, uploaded, misses = 0, 0, 0
    for c in candidates[:MAX_LOOKUPS]:
        purl = find_product_url(c["barcode"])
        if not purl:
            misses += 1
            print(f"  ✗ {c['title'][:55]:55} [no encontrado]")
            continue
        img = extract_image(purl, c["barcode"])
        if not img:
            misses += 1
            print(f"  ✗ {c['title'][:55]:55} [ficha sin EAN verificable o sin imagen]")
            continue
        found += 1
        if DRY_RUN:
            print(f"  ✓ {c['title'][:55]:55} → {img[:60]}...")
        else:
            try:
                sh_request("POST", f"/products/{c['id']}/images.json",
                           json={"image": {"src": img}})
                uploaded += 1
                print(f"  🖼 {c['title'][:55]:55} [imagen subida]")
            except requests.HTTPError as e:
                print(f"  ⚠ {c['title'][:55]:55} [error al subir: {e}]")

    print(f"\n→ Procesados: {min(len(candidates), MAX_LOOKUPS)} | "
          f"Encontrados en TCG Factory: {found} | "
          f"{'Subidos: ' + str(uploaded) if not DRY_RUN else 'Modo prueba, nada subido'} | "
          f"Sin coincidencia: {misses}")
    remaining = len(candidates) - MAX_LOOKUPS
    if remaining > 0:
        print(f"→ Quedan {remaining} productos para próximas pasadas")
    print("\n✔ Terminado")


if __name__ == "__main__":
    main()
