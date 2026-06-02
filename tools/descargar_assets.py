"""
descargar_assets.py — Descarga y guarda los activos estáticos del dashboard.
Correr UNA SOLA VEZ antes de la primera generación del dashboard.
No es parte del flujo semanal; solo hay que volver a correrlo si se actualizan
las librerías o se quiere regenerar el GeoJSON.
"""

import json
import sys
from pathlib import Path

import requests

# ════ PARÁMETROS EDITABLES ════
RAIZ = Path(__file__).resolve().parent.parent

RUTA_ASSETS = RAIZ / "docs" / "assets"
# EDITABLE: carpeta donde se guardan Chart.js y el GeoJSON.
# Debe coincidir con las rutas referenciadas en dashboard.html.j2 y generar_dashboard.py.

URL_CHARTJS = "https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"
# EDITABLE: URL de Chart.js. Actualizar versión si sale una nueva compatible (4.x).
# Evitar saltar de 4.x a 5.x sin revisar el template del dashboard.

URL_GEOJSON = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_ARG_1.json"
# EDITABLE: URL del GeoJSON de provincias argentinas con límites poligonales.
# Fuente: GADM 4.1 (Database of Global Administrative Areas, UC Davis).
# Propiedad de nombre de provincia: "NAME_1".
# Alternativas documentadas si esta URL falla:
#   Natural Earth: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
#   (archivo global, filtrar por adm0_a3 == "ARG" en descargar_assets.py)

DECIMALES_SIMPLIFICACION = 2
# EDITABLE: precisión de las coordenadas geográficas guardadas en el GeoJSON.
# 2 decimales = ~1 km de precisión, suficiente para un mapa de referencia.
# Subir a 3 si se quiere más detalle geográfico (archivo más pesado).

TDF_LAT_MIN = -57.0
# EDITABLE: latitud mínima (más sur) para conservar un polígono de Tierra del Fuego.
# Polígonos cuyo centroide esté por debajo de este valor se descartan (Antártida Argentina).
# La isla principal de TdF tiene centroide alrededor de lat -54; la Antártida, lat < -70.
# ═══════════════════════════════


def simplificar_anillo(anillo: list, decimales: int) -> list:
    """
    Redondea coordenadas y elimina puntos duplicados consecutivos resultantes.
    Reduce significativamente el tamaño del GeoJSON sin pérdida perceptible de forma.
    """
    redondeado = [[round(pt[0], decimales), round(pt[1], decimales)] for pt in anillo]
    sin_dup = [redondeado[0]]
    for pt in redondeado[1:]:
        if pt != sin_dup[-1]:
            sin_dup.append(pt)
    return sin_dup


def filtrar_poligonos_tdf(coordenadas_multipol: list) -> list:
    """
    Conserva solo los polígonos de TdF cuyo centroide esté sobre TDF_LAT_MIN.
    Descarta el sector antártico (polígonos muy al sur) para que no distorsione el mapa.
    """
    resultado = []
    for poligono in coordenadas_multipol:
        anillo_ext = poligono[0]
        if not anillo_ext:
            continue
        lats = [p[1] for p in anillo_ext]
        centroide_lat = sum(lats) / len(lats)
        if centroide_lat > TDF_LAT_MIN:
            resultado.append(poligono)
    return resultado


def simplificar_feature(feature: dict, decimales: int) -> dict:
    """
    Simplifica la geometría de un feature GeoJSON.
    Para TdF aplica además el filtro de polígonos antárticos.
    """
    geom = feature["geometry"]
    tipo = geom["type"]
    nombre = feature["properties"].get("nombre", "")

    if tipo == "MultiPolygon":
        coords = geom["coordinates"]
        if "Tierra del Fuego" in nombre:
            coords = filtrar_poligonos_tdf(coords)
        feature["geometry"]["coordinates"] = [
            [simplificar_anillo(anillo, decimales) for anillo in poligono]
            for poligono in coords
        ]
    elif tipo == "Polygon":
        feature["geometry"]["coordinates"] = [
            simplificar_anillo(anillo, decimales)
            for anillo in geom["coordinates"]
        ]

    return feature


def descargar(url: str, descripcion: str, timeout: int = 30) -> bytes:
    """Descarga una URL con manejo de errores claro."""
    print(f"Descargando {descripcion} ...")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except requests.exceptions.Timeout:
        print(f"  Error: timeout al descargar {url}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        sys.exit(1)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    RUTA_ASSETS.mkdir(parents=True, exist_ok=True)

    # ── Descargar Chart.js ────────────────────────────────────────────────────
    # Chart.js se descarga una sola vez y queda en docs/assets/. El dashboard
    # lo carga desde ahí, sin depender de ningún CDN en producción.
    contenido_chartjs = descargar(URL_CHARTJS, "Chart.js v4")
    ruta_chartjs = RUTA_ASSETS / "chart.v4.min.js"
    ruta_chartjs.write_bytes(contenido_chartjs)
    print(f"  → {ruta_chartjs} ({len(contenido_chartjs) // 1024} KB)")

    # ── Descargar GeoJSON de provincias (georef-ar) ───────────────────────────
    # El GeoJSON oficial tiene alta resolución. Se simplifica aquí para reducir
    # el tamaño del archivo y la memoria necesaria al generar el mapa SVG.
    contenido_geojson = descargar(URL_GEOJSON, "GeoJSON de provincias (georef-ar)")
    geojson = json.loads(contenido_geojson.decode("utf-8"))

    n_original = len(geojson["features"])
    geojson["features"] = [
        simplificar_feature(f, DECIMALES_SIMPLIFICACION)
        for f in geojson["features"]
    ]

    ruta_geojson = RUTA_ASSETS / "provincias.geojson"
    ruta_geojson.write_text(
        json.dumps(geojson, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size_kb = ruta_geojson.stat().st_size // 1024
    print(f"  → {ruta_geojson} ({size_kb} KB, {n_original} provincias)")

    print()
    print("Listo. Ahora podés correr: python tools/generar_dashboard.py")


if __name__ == "__main__":
    main()
