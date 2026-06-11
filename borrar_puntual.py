"""
BORRADO PUNTUAL (un solo uso) - Elimina de Shopify los 81 productos
sacados de la categoria GEEKO. Cruza por codigo de barras o SKU.
Tras usarlo, puedes borrar este archivo y borrar_puntual.yml del repositorio.
"""
import os, time, requests

SHOPIFY_TOKEN = os.environ["SHOPIFY_TOKEN"]
SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]
SH_BASE = f"https://{SHOPIFY_STORE}/admin/api/2024-10"
H = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}

TARGETS = [
 {
  "name": "CARTAS SUELTAS",
  "barcode": "",
  "sku": "10668"
 },
 {
  "name": "COLLAR - RELOJ HOT WHEELS BARBIE",
  "barcode": "8435477911689",
  "sku": "8435477911689"
 },
 {
  "name": "DENTIFRICO INFANTIL MICKEY",
  "barcode": "8480000469977",
  "sku": "007880"
 },
 {
  "name": "DIAMOND STITCH",
  "barcode": "8719668033146",
  "sku": "8719668033146"
 },
 {
  "name": "Display 12 Dundun Baby (precio unitario)",
  "barcode": "8437024269182",
  "sku": "display-dundun-baby"
 },
 {
  "name": "Display 12 Monster Jam Mini (precio unitario)",
  "barcode": "8432752033609",
  "sku": "display-monster-jam-mini"
 },
 {
  "name": "Display 12 Sobres Dun Dun Unicorns (precio unitario)",
  "barcode": "8437024269380",
  "sku": "display-dun-dun-unicorns"
 },
 {
  "name": "Display 8 Dundun Pijama Party (precio unitario)",
  "barcode": "8437024269731",
  "sku": "display-dundun-pijama-party"
 },
 {
  "name": "Display 8 Sobres Squishy Donut & Shake (precio unitario)",
  "barcode": "8437027545146",
  "sku": "display-squishy-donut-shake"
 },
 {
  "name": "Display 8 Squishy Animals (precio unitario)",
  "barcode": "8437027545153",
  "sku": "display-squishy-animals"
 },
 {
  "name": "Display 8 Squishy Dundun Animals (precio unitario)",
  "barcode": "8437027545511",
  "sku": "display-squishy-dundun-animals"
 },
 {
  "name": "DUNDUN PIJAMA PARTY",
  "barcode": "8437024269731",
  "sku": "10183"
 },
 {
  "name": "FIGURA PAPA NOEL M&M",
  "barcode": "50166398",
  "sku": "50166398"
 },
 {
  "name": "FIGURA YESO STITCH PINTAR",
  "barcode": "8719668033153",
  "sku": "8719668033153"
 },
 {
  "name": "FLIP N DIP PUSH POP",
  "barcode": "5011053022647",
  "sku": "5011053022647"
 },
 {
  "name": "FRESA POP",
  "barcode": "5904917030318",
  "sku": "5904917030318"
 },
 {
  "name": "Fundas Card Covers Top Loading 35 PT Pack 25 uds",
  "barcode": "4056133023368",
  "sku": "fundas-card-covers-top-loading-35pt"
 },
 {
  "name": "FUNKO DESPERFECTO - NO CAMBIO",
  "barcode": "",
  "sku": "10530"
 },
 {
  "name": "GELATINA NEUTRA ROYAL SOBRE",
  "barcode": "",
  "sku": "007184"
 },
 {
  "name": "HOT WHEELS",
  "barcode": "74299057854",
  "sku": "074299057854"
 },
 {
  "name": "HOT WHEELS 2022 PORSCHE 911 GT3 RS",
  "barcode": "194735337149",
  "sku": "10566"
 },
 {
  "name": "HOT WHEELS BATMAN SURTIDO",
  "barcode": "",
  "sku": "10471"
 },
 {
  "name": "HOT WHEELS CAMION TRANSPORTE",
  "barcode": "",
  "sku": "camiontransport"
 },
 {
  "name": "HOT WHEELS CLASICO SURTIDO",
  "barcode": "194735348015",
  "sku": "10618"
 },
 {
  "name": "HOT WHEELS COLOR SHIFTERS SURTIDO",
  "barcode": "746775345716",
  "sku": "10619"
 },
 {
  "name": "HOT WHEELS FAST AND FURIOUS SURTIDO",
  "barcode": "194735358366",
  "sku": "10645"
 },
 {
  "name": "HOT WHEELS MARIO KART SURTIDO",
  "barcode": "887961908459",
  "sku": "10634"
 },
 {
  "name": "HOT WHEELS NEON SURTIDO",
  "barcode": "",
  "sku": "10474"
 },
 {
  "name": "HOT WHEELS PACK 5",
  "barcode": "74299018060",
  "sku": "hot-wheels-pack-5-coches"
 },
 {
  "name": "HOT WHEELS POP CULTURE",
  "barcode": "",
  "sku": "10472"
 },
 {
  "name": "HOT WHEELS POP CULTURE REGRESO AL FUTURO 3",
  "barcode": "194735337224",
  "sku": "194735337224"
 },
 {
  "name": "HOT WHEELS PREMIUM",
  "barcode": "194735263745",
  "sku": "hot-wheels-f1"
 },
 {
  "name": "HOT WHEELS PREMIUM FORMULA 1",
  "barcode": "",
  "sku": "10403"
 },
 {
  "name": "HOT WHEELS REGULAR - MAINLINE",
  "barcode": "74299057854",
  "sku": "hot-wheels-blister-uno"
 },
 {
  "name": "HOT WHEELS SILVER SERIES",
  "barcode": "",
  "sku": "hot-wheels-fast-furious"
 },
 {
  "name": "HOT WHEELS VINTAGE",
  "barcode": "",
  "sku": "10598"
 },
 {
  "name": "HOTWHEELS PACK 2 NISSAN GTR NISMO GT3",
  "barcode": "194735262656",
  "sku": "10760"
 },
 {
  "name": "JUEGO DE AGUA",
  "barcode": "8032780951366",
  "sku": "8032780951366"
 },
 {
  "name": "JUEGO LANZA Y ATRAPA",
  "barcode": "8032780951151",
  "sku": "8032780951151"
 },
 {
  "name": "JUGUETE PERRO CON CHUPACHUP",
  "barcode": "8435124855052",
  "sku": "8435124855052"
 },
 {
  "name": "KOJAK POP CEREZA",
  "barcode": "8411402192309",
  "sku": "007176"
 },
 {
  "name": "LIBRETA PLUSH",
  "barcode": "8435507889889",
  "sku": "8435507889889"
 },
 {
  "name": "LLAVERO DIAMOND STITCH",
  "barcode": "8719668035546",
  "sku": "10072"
 },
 {
  "name": "LST0871 COMBA PARA SALTAR STITCH",
  "barcode": "8032780969190",
  "sku": "LST0871"
 },
 {
  "name": "LST0923 PINBALL STITCH (48x3)",
  "barcode": "8032780969057",
  "sku": "LST0923"
 },
 {
  "name": "LT0876 PUZZLE ROMPECABEZAS STITCH (48x3)",
  "barcode": "8032780951243",
  "sku": "LT0876"
 },
 {
  "name": "MD37-03HK SANRIO HELLO KITTY MONEDERO KUROMI",
  "barcode": "8426842112503",
  "sku": "MD37-03HK"
 },
 {
  "name": "MINI BOWLING",
  "barcode": "8032780953063",
  "sku": "8032780953063"
 },
 {
  "name": "MINI GUMBALL",
  "barcode": "4004641007776",
  "sku": "4004641007776"
 },
 {
  "name": "MINI SET COLOREAR STICH",
  "barcode": "8719668034853",
  "sku": "10071"
 },
 {
  "name": "PACK 2 HONDA HOTWHEELS PREMIUM",
  "barcode": "194735262571",
  "sku": "10690"
 },
 {
  "name": "PACK 2 VOLKSWAGEN HOTWHEELS PREMIUM",
  "barcode": "194735336760",
  "sku": "10689"
 },
 {
  "name": "PEONZA STITCH",
  "barcode": "8032780969040",
  "sku": "8032780969040"
 },
 {
  "name": "PINBALL STITCH",
  "barcode": "8032780969057",
  "sku": "8032780969057"
 },
 {
  "name": "Pinta con diamantes Disney surtido",
  "barcode": "18719668033266",
  "sku": "pinta-con-diamantes-disney"
 },
 {
  "name": "PINTA LABIOS HELLO KITTY",
  "barcode": "8435477911856",
  "sku": "8435477911856"
 },
 {
  "name": "PISTOLA DE AGUA FOAM 38CM",
  "barcode": "8435631901181",
  "sku": "8435631901181"
 },
 {
  "name": "POMPAS JABÓN MICKEY",
  "barcode": "8007315410021",
  "sku": "8007315410021"
 },
 {
  "name": "PONCHO STITCH",
  "barcode": "8435631356936",
  "sku": "007685"
 },
 {
  "name": "POP STAR DIPPER JOHNYBEE",
  "barcode": "5904917032633",
  "sku": "5904917032633"
 },
 {
  "name": "SET DE COLOREAR",
  "barcode": "8435507877299",
  "sku": "8435507877299"
 },
 {
  "name": "SET DE PEGATINAS",
  "barcode": "8435507889841",
  "sku": "8435507889841"
 },
 {
  "name": "SET STITCH ESCAYOLA MOLDEAR",
  "barcode": "5056816643165",
  "sku": "5056816643165"
 },
 {
  "name": "SETS DIARIO STITCH",
  "barcode": "8719668033061",
  "sku": "8719668033061"
 },
 {
  "name": "SKATE HOTWHEELS",
  "barcode": "194735205714",
  "sku": "10344"
 },
 {
  "name": "SOBRE COREANO POKEMON RAYQUAZA",
  "barcode": "8809581508521",
  "sku": "10751"
 },
 {
  "name": "Sobre de Refuerzo Pokemon TCG Noviembre 2025",
  "barcode": "196214126176",
  "sku": "pokemon-tcg-sobre-refuerzo"
 },
 {
  "name": "SOBRE DRAGON BALL",
  "barcode": "811039035495",
  "sku": "811039034221"
 },
 {
  "name": "Sobres de Mejora de Megaevolución",
  "barcode": "196214115989",
  "sku": "pokemon-expositor-sobres-megaevolucion"
 },
 {
  "name": "SPRAY POP JOHNY BEE",
  "barcode": "5904310231077",
  "sku": "5904310231077"
 },
 {
  "name": "SQUISHY ANIMALS",
  "barcode": "8437027545153",
  "sku": "10182"
 },
 {
  "name": "ST23346V POSTER RASCA Y DESCUBRE STITCH X2",
  "barcode": "8719668030855",
  "sku": "ST23346V"
 },
 {
  "name": "ST251382 Llavero Diamantes Lilo&Stitch Disney",
  "barcode": "8719668035546",
  "sku": "ST251382"
 },
 {
  "name": "ST251383 CANVA PINTA CON DIAMANTES 19X19CM LILO&STITCH",
  "barcode": "8719668035607",
  "sku": "ST251383"
 },
 {
  "name": "ST252500 MINI SET COLOREAR Y ACTIVIDADES LILO&STITCH",
  "barcode": "8719668034853",
  "sku": "ST252500"
 },
 {
  "name": "TOALLA POKEMON",
  "barcode": "8435631359005",
  "sku": "8435631359005"
 },
 {
  "name": "Toalla Pokemon algodon",
  "barcode": "8436580114622",
  "sku": "10516"
 },
 {
  "name": "TOALLA SONIC",
  "barcode": "8435631356820",
  "sku": "8435631356820"
 },
 {
  "name": "TOALLA SPIDEY",
  "barcode": "8435631356868",
  "sku": "8435631356868"
 },
 {
  "name": "TOALLA STITCH",
  "barcode": "8435631358381",
  "sku": "8435631358381"
 },
 {
  "name": "TOY BRIKZ LUZ",
  "barcode": "8435124855939",
  "sku": "8435124855939"
 }
]

def sh(method, path, **kw):
    for _ in range(5):
        r = requests.request(method, f"{SH_BASE}{path}", headers=H, **kw)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 2))); continue
        r.raise_for_status(); time.sleep(0.55); return r
    raise RuntimeError(f"rate limit en {path}")

barcodes = {t["barcode"] for t in TARGETS if t["barcode"]}
skus = {t["sku"] for t in TARGETS if t["sku"]}

print(f"Buscando {len(TARGETS)} productos en Shopify...")
to_delete = {}
params = {"limit": 250, "fields": "id,title,variants,status"}
url = "/products.json"
while True:
    r = sh("GET", url, params=params)
    for p in r.json().get("products", []):
        for v in p.get("variants", []):
            bc = (v.get("barcode") or "").strip()
            sku = (v.get("sku") or "").strip()
            if (bc and bc in barcodes) or (sku and sku in skus):
                to_delete[p["id"]] = p["title"]
    link = r.headers.get("Link", ""); nxt = None
    for part in link.split(","):
        if 'rel="next"' in part:
            nxt = part.split(";")[0].strip().strip("<>").split("/admin/api/2024-10")[1]
    if not nxt: break
    url, params = nxt, None

print(f"Encontrados {len(to_delete)} productos para eliminar:")
for pid, title in to_delete.items():
    print(f"  - {title}")

if len(to_delete) > 100:
    raise SystemExit("ABORTADO: demasiados productos, revisar antes de borrar")

deleted = 0
for pid, title in to_delete.items():
    sh("DELETE", f"/products/{pid}.json")
    print(f"  X Eliminado: {title}")
    deleted += 1

print(f"\nEliminados: {deleted} de {len(TARGETS)} objetivos")
missing = len(TARGETS) - deleted
if missing > 0:
    print(f"Nota: {missing} objetivos no estaban en Shopify (quiza nunca se subieron o ya se borraron)")
