"""
seguimiento_diario.py — Análisis ad hoc para la prueba temporal de corridas diarias.
NO forma parte del flujo semanal oficial (ver CLAUDE.md "Análisis ad hoc": no toca
tools/ principales). Correr DESPUÉS de tools/scraper.py y tools/analyzer.py, una vez
por día, durante la semana de prueba.

Qué hace cada corrida:
1. Archiva el titulares.csv de hoy con la fecha en el nombre, porque el scraper
   sobreescribe ese archivo si se vuelve a correr dentro de la misma semana ISO.
2. Agrega una fila a seguimiento_diario.csv con fecha, titulares scrapeados y matches.
3. Regenera seguimiento_diario.html con un gráfico de línea simple (Chart.js local,
   el mismo archivo que ya usa el dashboard oficial en docs/assets/).
"""

import csv
import json
import shutil
import sys
from datetime import date
from pathlib import Path

# ════ PARÁMETROS EDITABLES ════
RAIZ = Path(__file__).resolve().parent.parent

RUTA_LOG = Path(__file__).resolve().parent / "seguimiento_diario.csv"
# EDITABLE: archivo donde se acumula una fila por día de la prueba. Borrarlo
# reinicia el seguimiento (por ejemplo, para empezar una semana de prueba nueva).

RUTA_HTML = Path(__file__).resolve().parent / "seguimiento_diario.html"
# EDITABLE: gráfico generado a partir de RUTA_LOG. Se reescribe en cada corrida.

RUTA_CHARTJS_RELATIVA = "../docs/assets/chart.v4.min.js"
# EDITABLE: ruta relativa desde este HTML hasta Chart.js. Reutiliza el mismo
# archivo local que carga el dashboard oficial (sin CDN, sin descargar de nuevo).
# ═══════════════════════════════


def semana_iso() -> str:
    año, semana, _ = date.today().isocalendar()
    return f"{año}-W{semana:02d}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    hoy = date.today().isoformat()
    semana = semana_iso()

    ruta_titulares = RAIZ / "datos" / "crudos" / semana / "titulares.csv"
    ruta_snapshot = RAIZ / "datos" / "snapshots" / f"{semana}.csv"

    if not ruta_titulares.exists() or not ruta_snapshot.exists():
        print(f"Error: no se encontraron los archivos de hoy para la semana {semana}.")
        print("Corré primero: python tools/scraper.py && python tools/analyzer.py")
        sys.exit(1)

    # ── Archivar el crudo de hoy antes de que la corrida de mañana lo pise ────
    ruta_archivo = RAIZ / "datos" / "crudos" / semana / f"titulares_{hoy}.csv"
    shutil.copy(ruta_titulares, ruta_archivo)

    with open(ruta_titulares, encoding="utf-8") as f:
        total_titulares = sum(1 for _ in f) - 1  # -1 por el header

    with open(ruta_snapshot, encoding="utf-8-sig") as f:
        matches = list(csv.DictReader(f))
    total_matches = len(matches)

    # ── Registrar la fila de hoy en el log acumulado ──────────────────────────
    existe = RUTA_LOG.exists()
    with open(RUTA_LOG, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["fecha", "semana_iso", "titulares_scrapeados", "matches"])
        writer.writerow([hoy, semana, total_titulares, total_matches])

    print(f"Registrado: {hoy} → {total_matches} matches / {total_titulares} titulares")
    print(f"Crudo del día archivado → {ruta_archivo}")

    generar_grafico()


def generar_grafico() -> None:
    """Lee todo el historial acumulado y regenera el HTML con el gráfico de línea."""
    with open(RUTA_LOG, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))

    fechas     = [r["fecha"] for r in filas]
    matches    = [int(r["matches"]) for r in filas]
    titulares  = [int(r["titulares_scrapeados"]) for r in filas]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Seguimiento diario — prueba de una semana</title>
<script src="{RUTA_CHARTJS_RELATIVA}"></script>
<style>
  body {{ font-family: system-ui, sans-serif; background:#0d0f14; color:#cdd6f4; padding:2rem; max-width:900px; margin:0 auto; }}
  h1 {{ font-size: 1.15rem; font-weight:600; }}
  .nota {{ color:#6c7086; font-size:.82rem; margin-top:1.25rem; line-height:1.6; }}
  table {{ border-collapse: collapse; margin-top:1.5rem; font-size:.85rem; width:100%; }}
  th, td {{ padding: .45rem .8rem; border-bottom: 1px solid #1e2330; text-align:left; }}
  th {{ color:#6c7086; font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; }}
</style>
</head>
<body>
  <h1>Seguimiento diario — prueba de una semana ({len(filas)} corrida{'s' if len(filas) != 1 else ''} registrada{'s' if len(filas) != 1 else ''})</h1>
  <canvas id="c" height="110"></canvas>
  <table>
    <tr><th>Fecha</th><th>Semana</th><th>Titulares scrapeados</th><th>Matches</th></tr>
    {"".join(f"<tr><td>{r['fecha']}</td><td>{r['semana_iso']}</td><td>{r['titulares_scrapeados']}</td><td>{r['matches']}</td></tr>" for r in filas)}
  </table>
  <p class="nota">
    Generado por analisis/seguimiento_diario.py. Esto NO es el dashboard oficial
    (docs/index.html): es una herramienta temporal para evaluar si conviene una
    cadencia de corrida más frecuente que la semanal, antes de fijar día y horario
    definitivos (METODOLOGIA.md §8.4, todavía pendiente).
  </p>
</body>
<script>
new Chart(document.getElementById('c').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(fechas)},
    datasets: [
      {{
        label: 'Matches (palabras clave)',
        data: {json.dumps(matches)},
        borderColor: '#4cc9f0',
        backgroundColor: 'rgba(76,201,240,0.1)',
        fill: true,
        tension: 0.2,
        pointRadius: 4,
      }},
      {{
        label: 'Titulares scrapeados',
        data: {json.dumps(titulares)},
        borderColor: '#6c7086',
        borderDash: [4,4],
        fill: false,
        pointRadius: 3,
        yAxisID: 'y2',
      }}
    ]
  }},
  options: {{
    responsive: true,
    scales: {{
      y:  {{ beginAtZero: true, ticks: {{ color:'#6c7086' }}, grid: {{ color:'#1e2330' }} }},
      y2: {{ position: 'right', beginAtZero: true, ticks: {{ color:'#6c7086' }}, grid: {{ display:false }} }},
      x:  {{ ticks: {{ color:'#6c7086' }}, grid: {{ color:'#1e2330' }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color:'#cdd6f4' }} }} }}
  }}
}});
</script>
</html>"""

    RUTA_HTML.write_text(html, encoding="utf-8")
    print(f"Gráfico → {RUTA_HTML}")


if __name__ == "__main__":
    main()
