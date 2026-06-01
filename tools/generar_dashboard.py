"""
generar_dashboard.py — Genera docs/index.html a partir de datos/procesados/conflictos.csv.
Lee el CSV acumulativo, calcula todas las agregaciones en Python y renderiza con Jinja2.
NO modifica el CSV ni corre el scraper ni el analyzer.
"""

import sys
from datetime import date
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

# ════ PARÁMETROS EDITABLES ════
RAIZ = Path(__file__).resolve().parent.parent

RUTA_CONFLICTOS = RAIZ / "datos" / "procesados" / "conflictos.csv"
# EDITABLE: ruta del CSV acumulativo de conflictos generado por analyzer.py.
# Cambiarlo solo si se reorganiza la estructura de carpetas del proyecto.

RUTA_TEMPLATES = Path(__file__).resolve().parent / "templates"
# EDITABLE: carpeta donde vive la plantilla Jinja2 del dashboard.
# Si se mueve tools/templates/, actualizar esta ruta en consecuencia.

RUTA_OUTPUT = RAIZ / "docs" / "index.html"
# EDITABLE: destino del HTML generado. Debe coincidir con la carpeta configurada
# en GitHub Pages (Settings → Pages → Source). Típicamente "docs/" en rama main.

TITULO = "Monitor de Conflictividad Social · Argentina"
# EDITABLE: título que aparece en la pestaña del browser y en el encabezado.

SUBTITULO = "Rastreo semanal de palabras clave en titulares de medios locales y nacionales"
# EDITABLE: descripción breve visible debajo del título en el encabezado.

COLORES_PALABRAS = {
    "marcha":       "#3498db",
    "paro":         "#e74c3c",
    "protesta":     "#e67e22",
    "reclamo":      "#f39c12",
    "movilización": "#27ae60",
    "huelga":       "#8e44ad",
    "represión":    "#16a085",
    "piquete":      "#7f8c8d",
}
# EDITABLE: color CSS de cada palabra clave. Afecta barras, leyendas y badges en
# toda la interfaz. Si se agrega una nueva palabra en config/palabras_clave.csv,
# agregar aquí su color. Formato: hex (#rrggbb) o nombre CSS válido.

COLOR_FALLBACK = "#bdc3c7"
# EDITABLE: color para palabras sin entrada en COLORES_PALABRAS.
# En uso normal no debería activarse; sirve como resguardo si se agrega una
# nueva palabra clave sin actualizar el diccionario de colores.

COLOR_REGION = "#3d5a80"
# EDITABLE: color de las barras del gráfico de regiones.
# Cambiarlo si se quiere destacar las regiones con un color diferente al de las palabras.
# ═══════════════════════════════


def formato_semana(semana_iso: str) -> str:
    """Convierte '2026-W18' en 'W18' para etiquetas cortas en gráficos."""
    return semana_iso.split("-", 1)[1]


def main() -> None:

    # ── Verificar que existe el CSV antes de hacer cualquier cálculo ─────────
    # Si el archivo no existe, el usuario olvidó correr el analyzer primero.
    sys.stdout.reconfigure(encoding="utf-8")

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
    # Un titular como "Paro y marcha en Mendoza" tiene palabras_encontradas = "paro, marcha".
    # Se desdobla en filas separadas para poder contar por palabra individualmente.
    # Este DataFrame expandido solo se usa para los conteos; el df original
    # se usa para el resto para no inflar totales de titulares.
    df_exp = df.copy()
    df_exp["palabra"] = df_exp["palabras_encontradas"].str.split(r",\s*")
    df_exp = df_exp.explode("palabra")
    df_exp["palabra"] = df_exp["palabra"].str.strip()

    # ── Calcular KPIs: los cuatro números grandes de la cabecera ─────────────
    # Representan el estado global del monitor desde la primera semana hasta hoy.
    total_menciones = len(df)
    semanas_sorted = sorted(df["semana_iso"].unique().tolist())
    semanas_cubiertas = len(semanas_sorted)
    ultima_semana = semanas_sorted[-1]

    conteo_palabras = df_exp.groupby("palabra").size().sort_values(ascending=False)
    palabra_top = conteo_palabras.index[0]
    palabra_top_count = int(conteo_palabras.iloc[0])

    df_prov = df[df["corpus"] == "provincial"]
    if not df_prov.empty:
        conteo_regiones_kpi = df_prov.groupby("region").size().sort_values(ascending=False)
        region_top = conteo_regiones_kpi.index[0]
        region_top_count = int(conteo_regiones_kpi.iloc[0])
    else:
        region_top, region_top_count = "—", 0

    # ── Serie temporal: menciones por semana para el gráfico de barras ───────
    # Cada barra representa el total de titulares con al menos una palabra clave
    # en esa semana. La altura de la barra se calcula como porcentaje del máximo.
    total_por_semana = [int((df["semana_iso"] == s).sum()) for s in semanas_sorted]
    max_semanal = max(total_por_semana) if total_por_semana else 1

    # ── Distribución acumulada por palabra clave ──────────────────────────────
    # Suma de todas las menciones por palabra en todo el histórico.
    # Se usa para las barras horizontales de la sección "por palabra".
    total_palabras_sum = int(conteo_palabras.sum())
    dist_palabras = [
        {
            "palabra": p,
            "total": int(conteo_palabras[p]),
            "porcentaje": round(float(conteo_palabras[p]) / total_palabras_sum * 100, 1),
            "color": COLORES_PALABRAS.get(p, COLOR_FALLBACK),
        }
        for p in conteo_palabras.index
    ]
    max_palabra = int(conteo_palabras.iloc[0]) if not conteo_palabras.empty else 1

    # ── Distribución por región (solo corpus provincial) ──────────────────────
    # El corpus nacional se reporta por separado para no mezclar escalas.
    # Ver METODOLOGIA.md §2.2 sobre por qué los dos corpus no se mezclan.
    if not df_prov.empty:
        conteo_reg = df_prov.groupby("region").size().sort_values(ascending=False)
        dist_regiones = [
            {"region": r, "total": int(conteo_reg[r])}
            for r in conteo_reg.index
        ]
        max_region = int(conteo_reg.iloc[0])
    else:
        dist_regiones = []
        max_region = 1

    total_nacional = int((df["corpus"] == "nacional").sum())

    # ── Preparar filas para la tabla filtrable ────────────────────────────────
    # Todas las filas del CSV, ordenadas de más reciente a más antiguo.
    # Los data-attributes en el HTML permiten que el filtrado se haga en el browser
    # con JS puro, sin necesidad de servidor ni recarga de página.
    columnas_tabla = [
        "semana_iso", "corpus", "diario", "region", "titular", "palabras_encontradas"
    ]
    filas_tabla = (
        df.sort_values("fecha", ascending=False)[columnas_tabla]
        .fillna("")
        .to_dict("records")
    )

    # ── Opciones para los selectores de filtro del browser ───────────────────
    # Se calculan en Python para garantizar que reflejen exactamente los datos presentes.
    corpus_opciones = sorted(df["corpus"].unique().tolist())
    regiones_opciones = sorted(df[df["region"] != "Nacional"]["region"].unique().tolist())
    palabras_opciones = sorted(df_exp["palabra"].unique().tolist())

    # ── Renderizar la plantilla Jinja2 con todos los datos calculados ─────────
    # La plantilla recibe los datos ya procesados y genera el HTML autocontenido.
    # No hay lógica de negocio en la plantilla: todo viene calculado desde aquí.
    env = Environment(
        loader=FileSystemLoader(str(RUTA_TEMPLATES)),
        autoescape=True,
    )
    template = env.get_template("dashboard.html.j2")

    contexto = {
        "titulo":              TITULO,
        "subtitulo":           SUBTITULO,
        "fecha_generacion":    date.today().strftime("%d/%m/%Y"),
        "total_menciones":     total_menciones,
        "semanas_cubiertas":   semanas_cubiertas,
        "ultima_semana":       ultima_semana,
        "palabra_top":         palabra_top,
        "palabra_top_count":   palabra_top_count,
        "region_top":          region_top,
        "region_top_count":    region_top_count,
        "semanas":             semanas_sorted,
        "semanas_cortas":      [formato_semana(s) for s in semanas_sorted],
        "total_por_semana":    total_por_semana,
        "max_semanal":         max_semanal,
        "dist_palabras":       dist_palabras,
        "max_palabra":         max_palabra,
        "dist_regiones":       dist_regiones,
        "max_region":          max_region,
        "total_nacional":      total_nacional,
        "filas_tabla":         filas_tabla,
        "corpus_opciones":     corpus_opciones,
        "regiones_opciones":   regiones_opciones,
        "palabras_opciones":   palabras_opciones,
        "colores":             COLORES_PALABRAS,
        "color_fallback":      COLOR_FALLBACK,
        "color_region":        COLOR_REGION,
    }

    # ── Escribir el archivo HTML en docs/ ─────────────────────────────────────
    # La carpeta docs/ es la que GitHub Pages publica. No editar index.html
    # a mano: siempre regenerar con este script para que los datos estén al día.
    RUTA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RUTA_OUTPUT.write_text(template.render(**contexto), encoding="utf-8")

    print(f"Dashboard generado → {RUTA_OUTPUT}")
    print(f"  {total_menciones} menciones · {semanas_cubiertas} semanas · {len(filas_tabla)} titulares en tabla")


if __name__ == "__main__":
    main()
