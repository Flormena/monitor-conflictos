"""
generar_dashboard.py — Genera docs/index.html a partir de datos/procesados/conflictos.csv.
Lee el CSV acumulativo, calcula todas las agregaciones en Python y renderiza con Jinja2.
NO modifica el CSV ni corre el scraper ni el analyzer.
"""

import json
import math
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

# ════ PARÁMETROS EDITABLES ════
RAIZ = Path(__file__).resolve().parent.parent

RUTA_CONFLICTOS = RAIZ / "datos" / "procesados" / "conflictos.csv"
# EDITABLE: ruta del CSV acumulativo de conflictos generado por analyzer.py.
# Cambiar solo si se reorganiza la estructura de carpetas del proyecto.

RUTA_TEMPLATES = Path(__file__).resolve().parent / "templates"
# EDITABLE: carpeta donde vive la plantilla Jinja2 del dashboard.

RUTA_OUTPUT = RAIZ / "docs" / "index.html"
# EDITABLE: destino del HTML generado. Debe coincidir con la carpeta configurada
# en GitHub Pages (Settings → Pages → Source). Típicamente "docs/" en rama main.

RUTA_ASSETS = RAIZ / "docs" / "assets"
# EDITABLE: carpeta de activos estáticos (Chart.js, GeoJSON).
# Debe coincidir con la ruta en dashboard.html.j2 y en descargar_assets.py.

RUTA_GEOJSON = RUTA_ASSETS / "provincias.geojson"
# EDITABLE: GeoJSON de provincias argentinas generado por tools/descargar_assets.py.
# Si no existe, el mapa aparece vacío con un mensaje. No detiene la generación.

TITULO = "Monitor de Conflictividad Social · Argentina"
# EDITABLE: título en la pestaña del browser y en el encabezado del dashboard.

SUBTITULO = "Rastreo semanal de palabras clave en titulares de medios locales y nacionales"
# EDITABLE: descripción breve visible debajo del título.

COLORES_PALABRAS = {
    "paro":         "#0072B2",
    "marcha":       "#56B4E9",
    "reclamo":      "#E69F00",
    "protesta":     "#009E73",
    "movilización": "#CC79A7",
    "huelga":       "#8B4513",
    "piquete":      "#7F7F7F",
    "represión":    "#CC0000",
}
# EDITABLE: paleta Okabe-Ito apta para daltónicos. El rojo (#CC0000) está reservado
# para "represión". Afecta barras, badges, circles del mapa y gráficos de línea.
# Si se agrega una palabra nueva en config/palabras_clave.csv, agregar su color aquí.

COLOR_FALLBACK = "#bdc3c7"
# EDITABLE: color para palabras sin entrada en COLORES_PALABRAS (caso excepcional).

COLOR_REGION = "#3d5a80"
# EDITABLE: color de las barras del gráfico de distribución por región.

# ── Parámetros del mapa SVG ───────────────────────────────────────────────────
MAPA_ANCHO = 520
# EDITABLE: ancho del SVG del mapa en píxeles. Argentina es estrecha; no subir mucho.

MAPA_ALTO = 720
# EDITABLE: alto del SVG del mapa en píxeles. Mantener ALTO > ANCHO (país elongado).

MAPA_PADDING = 24
# EDITABLE: margen interior del SVG en píxeles.
# Aumentar si los círculos de provincias costeras quedan cortados.

MAPA_RADIO_MIN = 4
# EDITABLE: radio mínimo de círculo (provincias con 0 menciones).
# Poner en 0 para ocultar completamente las provincias sin datos.

MAPA_RADIO_FACTOR = 9
# EDITABLE: radio = sqrt(menciones) × factor.
# Subir si los círculos se ven pequeños; bajar si se solapan en zonas densas.

MAPA_RADIO_MAX = 38
# EDITABLE: radio máximo de círculo en píxeles (evita que una provincia domine visualmente).

MAPA_LON_MIN, MAPA_LON_MAX = -74.0, -52.0
# EDITABLE: longitud oeste y este del área visible del mapa (grados decimales).

MAPA_LAT_MIN, MAPA_LAT_MAX = -57.0, -21.0
# EDITABLE: latitud sur y norte del área visible del mapa (grados decimales).

# ── Parámetros de small multiples (mini-gráficos por palabra) ────────────────
MINI_W, MINI_H, MINI_PAD = 160, 80, 12
# EDITABLE: dimensiones del viewBox de cada mini-gráfico (W, H) y margen interior (PAD).
# Son unidades SVG, no píxeles de pantalla; el tamaño real lo controla el CSS.

MAPEO_NOMBRES_PROVINCIA = {}
# EDITABLE: mapeo de nombre en conflictos.csv (clave) → nombre exacto en el GeoJSON (valor).
# Con la fuente click_that_hood los nombres coinciden directamente.
# Si una provincia no aparece en el mapa, agregar aquí la discrepancia de nombre.
# Ejemplos de entradas que podrían ser necesarias con otras fuentes:
#   "Tierra del Fuego": "Tierra del Fuego, Antártida e Islas del Atlántico Sur"
# ═══════════════════════════════


# ── Funciones de proyección cartográfica ─────────────────────────────────────

def _y_merc(lat_deg: float) -> float:
    """Calcula la coordenada Y en proyección Web Mercator para una latitud dada."""
    lat_rad = math.radians(max(min(lat_deg, 89.9), -89.9))
    return -math.log(math.tan(math.pi / 4 + lat_rad / 2))


# Pre-calcular los extremos Mercator una sola vez para toda la corrida
_Y_MERC_NORTE = _y_merc(MAPA_LAT_MAX)
_Y_MERC_SUR   = _y_merc(MAPA_LAT_MIN)


def proyectar_punto(lon: float, lat: float) -> tuple[float, float]:
    """Proyecta un punto lon/lat a coordenadas SVG (píxeles) con proyección Web Mercator."""
    frac_x = (lon - MAPA_LON_MIN) / (MAPA_LON_MAX - MAPA_LON_MIN)
    frac_y = (_y_merc(lat) - _Y_MERC_NORTE) / (_Y_MERC_SUR - _Y_MERC_NORTE)
    x_px = MAPA_PADDING + frac_x * (MAPA_ANCHO - 2 * MAPA_PADDING)
    y_px = MAPA_PADDING + frac_y * (MAPA_ALTO  - 2 * MAPA_PADDING)
    return round(x_px, 1), round(y_px, 1)


def anillo_a_path_d(anillo: list) -> str:
    """Convierte un anillo de coordenadas [[lon, lat], ...] a subcomando de path SVG."""
    if len(anillo) < 2:
        return ""
    pts = [proyectar_punto(lon, lat) for lon, lat in anillo]
    return "M " + " L ".join(f"{x},{y}" for x, y in pts) + " Z"


def geometria_a_path_d(geom: dict) -> str:
    """Convierte un objeto geometry GeoJSON completo a un string 'd' de path SVG."""
    tipo = geom["type"]
    partes = []
    if tipo == "Polygon":
        partes.append(anillo_a_path_d(geom["coordinates"][0]))
    elif tipo == "MultiPolygon":
        for pol in geom["coordinates"]:
            if pol:
                partes.append(anillo_a_path_d(pol[0]))
    return " ".join(p for p in partes if p)


def centroide_geom(geom: dict) -> tuple[float, float]:
    """Calcula el centroide como promedio de vértices del anillo exterior principal."""
    tipo = geom["type"]
    if tipo == "Polygon":
        anillo = geom["coordinates"][0]
    else:  # MultiPolygon: usar el polígono con más vértices
        anillo = max(geom["coordinates"], key=lambda pol: len(pol[0]))[0]
    avg_lon = sum(p[0] for p in anillo) / len(anillo)
    avg_lat = sum(p[1] for p in anillo) / len(anillo)
    return proyectar_punto(avg_lon, avg_lat)


# ── Función principal del mapa ────────────────────────────────────────────────

def preparar_datos_mapa(df: pd.DataFrame) -> list[dict]:
    """
    Lee el GeoJSON, proyecta formas de provincias a SVG y calcula círculos proporcionales.
    Devuelve lista de dicts listos para el template. Lista vacía si falta el GeoJSON.
    Cada dict incluye: path_d (forma SVG), cx/cy (centroide), radio, color y datos tooltip.
    """
    if not RUTA_GEOJSON.exists():
        return []

    with open(RUTA_GEOJSON, encoding="utf-8") as f:
        geojson = json.load(f)

    # Invertir MAPEO para buscar por nombre GeoJSON → nombre CSV
    mapa_inverso = {v: k for k, v in MAPEO_NOMBRES_PROVINCIA.items()}

    # Calcular menciones y palabra dominante por provincia (solo corpus provincial)
    df_prov = df[df["corpus"] == "provincial"].copy()
    menciones_por_prov = df_prov.groupby("provincia").size().to_dict() if not df_prov.empty else {}

    if not df_prov.empty:
        df_exp_prov = df_prov.copy()
        df_exp_prov["palabra"] = df_exp_prov["palabras_encontradas"].str.split(r",\s*")
        df_exp_prov = df_exp_prov.explode("palabra")
        df_exp_prov["palabra"] = df_exp_prov["palabra"].str.strip()
        dom = (
            df_exp_prov.groupby(["provincia", "palabra"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .groupby("provincia")
            .first()["palabra"]
            .to_dict()
        )
    else:
        dom = {}

    resultado = []
    for feat in geojson["features"]:
        # Soporta múltiples fuentes: "NAME_1" (GADM), "nombre" (georef-ar), "name" (otros)
        props = feat["properties"]
        nombre_geojson = props.get("NAME_1") or props.get("nombre") or props.get("name", "")
        nombre_csv = mapa_inverso.get(nombre_geojson, nombre_geojson)

        geom = feat["geometry"]
        path_d = geometria_a_path_d(geom)
        cx, cy = centroide_geom(geom)

        menciones = menciones_por_prov.get(nombre_csv, 0)
        palabra_dom = dom.get(nombre_csv, "")
        sin_datos = menciones == 0

        if sin_datos:
            radio = MAPA_RADIO_MIN
            color = "#bdc3c7"
        else:
            radio = min(round(math.sqrt(menciones) * MAPA_RADIO_FACTOR, 1), MAPA_RADIO_MAX)
            color = COLORES_PALABRAS.get(palabra_dom, COLOR_FALLBACK)

        resultado.append({
            "nombre":            nombre_csv,
            "path_d":            path_d,
            "cx":                cx,
            "cy":                cy,
            "menciones":         menciones,
            "radio":             radio,
            "color":             color,
            "palabra_dominante": palabra_dom if not sin_datos else "—",
            "sin_datos":         sin_datos,
        })

    return resultado


# ── Funciones de small multiples ─────────────────────────────────────────────

def puntos_minigrafico(valores: list[int], max_global: int) -> list[tuple[float, float]]:
    """
    Convierte lista de valores enteros a coordenadas SVG para el mini-gráfico de una palabra.
    Todos los mini-gráficos usan el mismo max_global para comparar con la misma escala Y.
    """
    n = len(valores)
    if n == 0:
        return []
    puntos = []
    for i, val in enumerate(valores):
        x = MINI_PAD + (i / max(n - 1, 1)) * (MINI_W - 2 * MINI_PAD)
        if max_global > 0:
            y = MINI_PAD + (1 - val / max_global) * (MINI_H - 2 * MINI_PAD)
        else:
            y = float(MINI_H - MINI_PAD)
        puntos.append((round(x, 1), round(y, 1)))
    return puntos


def formato_semana(semana_iso: str) -> str:
    """Convierte '2026-W18' en 'W18' para etiquetas cortas en gráficos."""
    return semana_iso.split("-", 1)[1]


def calcular_tendencia(total_por_semana: list[int]) -> dict:
    """
    Compara la última semana contra la anterior. Devuelve dirección (alza/baja/estable)
    y porcentaje de variación, usados para la flecha de tendencia junto al KPI principal.
    """
    if len(total_por_semana) < 2:
        return {"direccion": None, "delta": 0, "pct": 0}
    actual, anterior = total_por_semana[-1], total_por_semana[-2]
    delta = actual - anterior
    pct = round(abs(delta) / anterior * 100) if anterior > 0 else 0
    if delta > 0:
        direccion = "alza"
    elif delta < 0:
        direccion = "baja"
    else:
        direccion = "estable"
    return {"direccion": direccion, "delta": delta, "pct": pct}


def generar_resumen_automatico(
    tendencia: dict,
    palabra_top: str, palabra_top_count: int,
    region_top: str, region_top_count: int,
) -> str:
    """
    Construye una oración de resumen en lenguaje natural a partir de los datos calculados.
    Da contexto inmediato al lector antes de que explore los gráficos en detalle.
    """
    partes = []
    if tendencia["direccion"] == "alza":
        partes.append(f"Las menciones subieron {tendencia['pct']}% respecto a la semana anterior")
    elif tendencia["direccion"] == "baja":
        partes.append(f"Las menciones bajaron {tendencia['pct']}% respecto a la semana anterior")
    elif tendencia["direccion"] == "estable":
        partes.append("Las menciones se mantuvieron estables respecto a la semana anterior")

    partes.append(f"&ldquo;{palabra_top}&rdquo; fue la palabra más mencionada ({palabra_top_count} veces)")

    if region_top != "—":
        partes.append(f"{region_top} concentra la mayor actividad provincial ({region_top_count} menciones)")

    return ". ".join(partes) + "."


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    # ── Verificar que existe el CSV de conflictos ─────────────────────────────
    # Si no existe, el usuario todavía no corrió el analyzer.
    if not RUTA_CONFLICTOS.exists():
        print(f"Error: no se encontró {RUTA_CONFLICTOS}")
        print("Corré primero: python tools/analyzer.py")
        sys.exit(1)

    print(f"Leyendo {RUTA_CONFLICTOS} ...")
    df = pd.read_csv(RUTA_CONFLICTOS, encoding="utf-8-sig")

    if df.empty:
        print("Error: conflictos.csv está vacío. No hay datos para mostrar.")
        sys.exit(1)

    # ── Expandir filas con múltiples palabras clave ───────────────────────────
    # "paro, marcha" → dos filas separadas para poder contar por palabra.
    # El df_exp solo se usa para conteos; el df original no se modifica.
    df_exp = df.copy()
    df_exp["palabra"] = df_exp["palabras_encontradas"].str.split(r",\s*")
    df_exp = df_exp.explode("palabra")
    df_exp["palabra"] = df_exp["palabra"].str.strip()

    # ── KPIs: cuatro métricas de cabecera ─────────────────────────────────────
    # Representan el estado global del monitor desde la primera semana hasta hoy.
    total_menciones = len(df)
    semanas_sorted = sorted(df["semana_iso"].unique().tolist())
    semanas_cubiertas = len(semanas_sorted)
    ultima_semana = semanas_sorted[-1]

    conteo_palabras = df_exp.groupby("palabra").size().sort_values(ascending=False)
    palabra_top       = conteo_palabras.index[0]
    palabra_top_count = int(conteo_palabras.iloc[0])

    df_prov = df[df["corpus"] == "provincial"]
    if not df_prov.empty:
        conteo_reg_kpi  = df_prov.groupby("region").size().sort_values(ascending=False)
        region_top       = conteo_reg_kpi.index[0]
        region_top_count = int(conteo_reg_kpi.iloc[0])
    else:
        region_top, region_top_count = "—", 0

    # ── Serie temporal: totales por semana (para Chart.js line) ──────────────
    # Una lista de enteros: menciones totales en cada semana en orden cronológico.
    total_por_semana = [int((df["semana_iso"] == s).sum()) for s in semanas_sorted]

    # ── Conteo por semana × palabra (para small multiples y composición) ──────
    # Diccionario anidado {semana: {palabra: count}} que alimenta dos visualizaciones.
    conteo_sem_pal: dict[str, dict[str, int]] = {}
    for semana in semanas_sorted:
        df_sem = df_exp[df_exp["semana_iso"] == semana]
        conteo_sem_pal[semana] = df_sem.groupby("palabra").size().to_dict()

    # ── Small multiples: un mini-gráfico por palabra clave ───────────────────
    # Todos usan la misma escala Y (max_global) para ser comparables entre sí.
    # DECISIÓN METODOLÓGICA: el orden sigue COLORES_PALABRAS (no por frecuencia),
    # para que la posición de cada palabra sea consistente entre dashboards.
    max_global_sm = max(
        (conteo_sem_pal[s].get(p, 0) for s in semanas_sorted for p in COLORES_PALABRAS),
        default=1,
    ) or 1

    small_multiples = []
    for palabra in COLORES_PALABRAS:
        valores = [conteo_sem_pal[s].get(palabra, 0) for s in semanas_sorted]
        small_multiples.append({
            "palabra":    palabra,
            "color":      COLORES_PALABRAS[palabra],
            "valores":    valores,
            "puntos":     puntos_minigrafico(valores, max_global_sm),
            "max_val":    max(valores) if valores else 0,
        })

    # ── Composición: datasets para Chart.js stacked bar ──────────────────────
    # Una serie por palabra; el mismo orden que COLORES_PALABRAS.
    composicion_datasets = [
        {
            "label": palabra,
            "color": COLORES_PALABRAS[palabra],
            "data":  [conteo_sem_pal[s].get(palabra, 0) for s in semanas_sorted],
        }
        for palabra in COLORES_PALABRAS
    ]

    # ── Distribución acumulada por palabra (barras horizontales) ─────────────
    total_palabras_sum = int(conteo_palabras.sum())
    dist_palabras = [
        {
            "palabra":    p,
            "total":      int(conteo_palabras[p]),
            "porcentaje": round(float(conteo_palabras[p]) / total_palabras_sum * 100, 1),
            "color":      COLORES_PALABRAS.get(p, COLOR_FALLBACK),
        }
        for p in conteo_palabras.index
    ]
    max_palabra = int(conteo_palabras.iloc[0]) if not conteo_palabras.empty else 1

    # ── Distribución por región (solo corpus provincial) ─────────────────────
    # El corpus nacional se reporta por separado (METODOLOGIA.md §2.2).
    if not df_prov.empty:
        conteo_reg  = df_prov.groupby("region").size().sort_values(ascending=False)
        dist_regiones = [{"region": r, "total": int(conteo_reg[r])} for r in conteo_reg.index]
        max_region    = int(conteo_reg.iloc[0])
    else:
        dist_regiones = []
        max_region    = 1

    total_nacional = int((df["corpus"] == "nacional").sum())

    # ── Tendencia y resumen automático ────────────────────────────────────────
    # Compara la última semana contra la anterior y redacta una oración de contexto.
    # Da una lectura inmediata antes de que el usuario explore los gráficos en detalle.
    tendencia = calcular_tendencia(total_por_semana)
    resumen_automatico = generar_resumen_automatico(
        tendencia, palabra_top, palabra_top_count, region_top, region_top_count
    )

    # ── Mapa SVG: paths y círculos por provincia ──────────────────────────────
    # El GeoJSON se proyecta a SVG en Python; el HTML final no carga ninguna librería de mapas.
    if not RUTA_GEOJSON.exists():
        print("Advertencia: GeoJSON no encontrado → el mapa no se generará.")
        print("  Corré: python tools/descargar_assets.py")
    provincias_mapa = preparar_datos_mapa(df)

    # ── Ranking de provincias: top 10 con menciones, para la lista junto al mapa ─
    # El mapa y esta lista están vinculados en el browser: clic en una provincia
    # filtra ambos (ver JS al final del template).
    provincias_ranking = sorted(
        (p for p in provincias_mapa if not p["sin_datos"]),
        key=lambda p: -p["menciones"],
    )[:10]

    # ── Tabla filtrable: todas las filas del CSV ──────────────────────────────
    # Ordenadas de más reciente a más antiguo; el filtrado ocurre en el browser con JS.
    # Incluye "provincia" para que el clic en el mapa pueda filtrar la tabla.
    columnas_tabla = ["semana_iso", "corpus", "diario", "provincia", "region", "titular", "palabras_encontradas"]
    filas_tabla = (
        df.sort_values("fecha", ascending=False)[columnas_tabla]
        .fillna("")
        .to_dict("records")
    )

    # ── Opciones para los selectores de filtro ────────────────────────────────
    corpus_opciones    = sorted(df["corpus"].unique().tolist())
    regiones_opciones  = sorted(df[df["region"] != "Nacional"]["region"].unique().tolist())
    palabras_opciones  = sorted(df_exp["palabra"].unique().tolist())

    # ── Renderizar con Jinja2 ─────────────────────────────────────────────────
    # La plantilla recibe todos los datos ya calculados. No hay lógica de negocio
    # en el template: todo llega listo para renderizar.
    env = Environment(
        loader=FileSystemLoader(str(RUTA_TEMPLATES)),
        autoescape=True,
    )
    # Filtro tojson: convierte objetos Python a JSON embebible en <script> con | tojson | safe
    env.filters["tojson"] = lambda obj: json.dumps(obj, ensure_ascii=False)

    template = env.get_template("dashboard.html.j2")

    contexto = {
        "titulo":               TITULO,
        "subtitulo":            SUBTITULO,
        "fecha_generacion":     date.today().strftime("%d/%m/%Y"),
        # KPIs
        "total_menciones":      total_menciones,
        "semanas_cubiertas":    semanas_cubiertas,
        "ultima_semana":        ultima_semana,
        "palabra_top":          palabra_top,
        "palabra_top_count":    palabra_top_count,
        "region_top":           region_top,
        "region_top_count":     region_top_count,
        "tendencia":            tendencia,
        "resumen_automatico":   resumen_automatico,
        # Serie temporal
        "semanas":              semanas_sorted,
        "semanas_cortas":       [formato_semana(s) for s in semanas_sorted],
        "total_por_semana":     total_por_semana,
        # Small multiples
        "small_multiples":      small_multiples,
        "mini_w":               MINI_W,
        "mini_h":               MINI_H,
        "mini_pad":             MINI_PAD,
        # Distribuciones
        "dist_palabras":        dist_palabras,
        "max_palabra":          max_palabra,
        "dist_regiones":        dist_regiones,
        "max_region":           max_region,
        "total_nacional":       total_nacional,
        # Mapa
        "provincias_mapa":      provincias_mapa,
        "provincias_ranking":   provincias_ranking,
        "mapa_ancho":           MAPA_ANCHO,
        "mapa_alto":            MAPA_ALTO,
        # Composición
        "composicion_datasets": composicion_datasets,
        # Tabla
        "filas_tabla":          filas_tabla,
        "corpus_opciones":      corpus_opciones,
        "regiones_opciones":    regiones_opciones,
        "palabras_opciones":    palabras_opciones,
        "semanas_opciones":     semanas_sorted,
        # Colores
        "colores":              COLORES_PALABRAS,
        "color_fallback":       COLOR_FALLBACK,
        "color_region":         COLOR_REGION,
    }

    # ── Escribir docs/index.html ──────────────────────────────────────────────
    # GitHub Pages publica todo lo que está en docs/. No editar index.html a mano:
    # siempre regenerar con este script para que los datos estén al día.
    RUTA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RUTA_OUTPUT.write_text(template.render(**contexto), encoding="utf-8")

    n_mapa = len(provincias_mapa)
    print(f"Dashboard generado → {RUTA_OUTPUT}")
    print(f"  {total_menciones} menciones · {semanas_cubiertas} semanas · "
          f"{len(filas_tabla)} titulares · {n_mapa} provincias en mapa")


if __name__ == "__main__":
    main()
