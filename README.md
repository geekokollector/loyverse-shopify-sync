# Sync Loyverse → Shopify (Geeko Kollector)

Sincroniza el stock de Loyverse con Shopify cada 15 minutos usando GitHub Actions (gratis).

**Qué hace:**
1. Lee artículos y stock de Loyverse
2. Cruza con Shopify por **código de barras** (si no hay, usa el SKU)
3. Actualiza el inventario en Shopify solo cuando hay cambios
4. Los productos nuevos de Loyverse que no existen en Shopify se crean como **borrador** (con nombre, precio, barcode y stock) — tú solo añades foto/descripción y publicas

---

## Instalación (una sola vez)

### 1. Crear el repositorio
1. Entra en github.com → **New repository**
2. Nombre: `loyverse-shopify-sync` → marca **Private** → Create
3. Sube estos archivos manteniendo la estructura:
   - `sync.py`
   - `.github/workflows/sync.yml`

   (Puedes hacerlo desde la web: **Add file → Upload files**. Para la carpeta
   `.github/workflows`, usa **Add file → Create new file** y escribe
   `.github/workflows/sync.yml` como nombre, pegando el contenido.)

### 2. Añadir los secretos
En el repositorio: **Settings → Secrets and variables → Actions → New repository secret**

| Nombre | Valor |
|---|---|
| `LOYVERSE_TOKEN` | Tu token de Loyverse |
| `SHOPIFY_TOKEN` | Tu Admin API token (`shpat_...`) |
| `SHOPIFY_STORE` | Tu dominio myshopify, ej: `geekollector.myshopify.com` |
| `LOYVERSE_STORE_ID` | (Opcional) Solo si tienes varias tiendas en Loyverse |

### 3. Probar
1. Pestaña **Actions** → workflow "Sync Loyverse → Shopify" → **Run workflow**
2. Abre la ejecución y revisa el log: verás qué productos se actualizan,
   cuáles coinciden y qué borradores se crean

A partir de ahí se ejecuta solo cada 15 minutos.

---

## Opciones (en `.github/workflows/sync.yml`)

- `SAFETY_BUFFER`: unidades de seguridad. Con `"1"`, si en tienda queda 1 unidad,
  la web muestra 0 (evita vender online lo que se acaba de vender en tienda).
- `CREATE_DRAFTS`: `"true"` crea borradores de productos nuevos; `"false"` solo
  los lista en el log sin crear nada.
- Frecuencia: cambia `*/15` por `*/30` (cada 30 min) o `0 * * * *` (cada hora).

## Notas

- La primera ejecución puede tardar varios minutos (revisa todo el catálogo).
- GitHub puede retrasar los crons unos minutos en horas punta; es normal.
- Si un token caduca o falla, la ejecución sale en rojo en la pestaña Actions
  y GitHub te puede avisar por email.
