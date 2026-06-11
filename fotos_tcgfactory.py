"""
Extractor de imágenes desde tcgfactory.com para Geeko Kollector (v2)
---------------------------------------------------------------------
Estrategia: busca por NOMBRE en el buscador público de TCG Factory
(su buscador no indexa EANs) y valida la coincidencia comparando títulos.
Solo procesa productos de Shopify SIN ninguna imagen.

Variables de entorno:
  SHOPIFY_TOKEN, SHOPIFY_STORE
  DRY_RUN      "true" (default) = solo mirar | "false" = subir imágenes
  MAX_LOOKUPS  máximo de productos por pasada (default 40)
"""

import os
import re
import time
import unicodedata
import requests

SHOPIFY_TOKEN = os.environ["SHOPIFY_TOKEN"]
SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"
MAX_LOOKUPS = int(os.environ.get("MAX_LOOKUPS", "40"))

SH_BASE = f"https://{SHOPIFY_STORE}/admin/api/2024-10"
sh_headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


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


def normalize(text):
    """minúsculas, sin acentos ni símbolos, para comparar títulos"""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return [w for w in text.split() if len(w) > 1]


def title_match(words_a, words_b):
    """proporción de palabras del título A presentes en el B"""
    if not words_a:
        return 0.0
    setb = set(words_b)
    return sum(1 for w in words_a if w in setb) / len(words_a)


def tcg_get(url, params=None):
    time.sleep(2)  # cortesía con su servidor
    try:
        r = requests.get(url, headers=UA, params=params, timeout=20)
    except requests.RequestException as e:
        print(f"    [red] {e}")
        return None
    if r.status_code != 200:
        print(f"    [HTTP {r.status_code}]")
        return None
    return r.text


def search_tcg(name):
    """Busca por nombre y devuelve lista de (url_ficha, titulo)."""
    html = tcg_get("https://tcgfactory.com/es/buscar",
                   params={"controller": "search", "s": name})
    if not html:
        return []
    results = []
    # PrestaShop: fichas con enlaces .html; capturamos enlace + texto cercano
    for m in re.finditer(
            r'<a[^>]+href="(https://tcgfactory\.com/es/[^"]+?\.html)"[^>]*>([^<]{5,120})</a>',
            html):
        url, text = m.group(1), m.group(2).strip()
        if text and (url, text) not in results:
            results.append((url, text))
    return results[:5]


def extract_image(product_url):
    html = tcg_get(product_url)
    if not html:
        return None, None
    title = ""
    mt = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if mt:
        title = mt.group(1)
    mi = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
    if mi:
        return mi.group(1), title
    mi = re.search(r'(https://tcgfactory\.com/\d+-(?:home|large)_default/[^"\s]+\.jpg)', html)
    if mi:
        return mi.group(1), title
    return None, title


def main():
    print(f"Modo: {'PRUEBA (no sube nada)' if DRY_RUN else 'SUBIDA ACTIVA'} | "
          f"Límite por pasada: {MAX_LOOKUPS}\n")

    print("→ Buscando productos sin imagen en Shopify...")
    candidates = []
    params = {"limit": 250, "fields": "id,title,images"}
    url = "/products.json"
    while True:
        r = sh_request("GET", url, params=params)
        for p in r.json().get("products", []):
            if not p.get("images"):
                candidates.append({"id": p["id"], "title": p.get("title", "")})
        link = r.headers.get("Link", "")
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                nxt = part.split(";")[0].strip().strip("<>").split("/admin/api/2024-10")[1]
        if not nxt:
            break
        url, params = nxt, None
    print(f"  {len(candidates)} productos sin imagen\n")

    found, uploaded, misses = 0, 0, 0
    for c in candidates[:MAX_LOOKUPS]:
        my_words = normalize(c["title"])
        query = " ".join(my_words[:7])  # primeras palabras significativas
        results = search_tcg(query)
        best = None
        for purl, text in results:
            score = title_match(my_words, normalize(text))
            if score >= 0.6 and (best is None or score > best[0]):
                best = (score, purl)
        if not best:
            misses += 1
            print(f"  ✗ {c['title'][:55]:55} [sin resultados fiables "
                  f"({len(results)} candidatos)]")
            continue
        img, page_title = extract_image(best[1])
        if not img:
            misses += 1
            print(f"  ✗ {c['title'][:55]:55} [ficha sin imagen]")
            continue
        # verificación final contra el título de la ficha
        if page_title and title_match(my_words, normalize(page_title)) < 0.5:
            misses += 1
            print(f"  ✗ {c['title'][:55]:55} [ficha no coincide: {page_title[:40]}]")
            continue
        found += 1
        if DRY_RUN:
            print(f"  ✓ {c['title'][:55]:55} → {img[:60]}")
        else:
            try:
                sh_request("POST", f"/products/{c['id']}/images.json",
                           json={"image": {"src": img}})
                uploaded += 1
                print(f"  🖼 {c['title'][:55]:55} [imagen subida]")
            except requests.HTTPError as e:
                print(f"  ⚠ {c['title'][:55]:55} [error al subir: {e}]")

    print(f"\n→ Procesados: {min(len(candidates), MAX_LOOKUPS)} | "
          f"Encontrados: {found} | "
          f"{'Subidos: ' + str(uploaded) if not DRY_RUN else 'Modo prueba, nada subido'} | "
          f"Sin coincidencia: {misses}")
    rem = len(candidates) - MAX_LOOKUPS
    if rem > 0:
        print(f"→ Quedan {rem} productos para próximas pasadas")
    print("\n✔ Terminado")


if __name__ == "__main__":
    main()
