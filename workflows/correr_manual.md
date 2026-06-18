# Workflow: Correr los scripts manualmente

Guía de referencia rápida para correr el pipeline a mano. Separa el **flujo
semanal oficial** (producción) del **modo test diario** (prueba temporal).

---

## Primera vez en una máquina nueva

```bash
pip install -r requirements.txt
python tools/descargar_assets.py    # one-shot: Chart.js + GeoJSON de provincias
```

`descargar_assets.py` solo hace falta correrlo una vez (o si se borra `docs/assets/`).

---

## Flujo semanal oficial (producción)

Correr **una vez por semana, mismo día y horario** (METODOLOGIA.md §4.2 — la
regularidad es necesaria para que las series sean comparables).

```bash
python tools/scraper.py              # descarga HTML, extrae titulares
python tools/analyzer.py             # detecta palabras clave, actualiza snapshot + acumulativo
python tools/generar_dashboard.py    # regenera docs/index.html
git add . && git commit -m "Corrida YYYY-Www" && git push
```

### Reprocesar una semana pasada

Si cambió una palabra clave, el filtro de bigramas, o cualquier cosa que afecte
la detección, y hay que recalcular sin volver a scrapear (los HTML crudos ya
están guardados):

```bash
python tools/analyzer.py --semana 2026-W18
python tools/generar_dashboard.py
```

### Pruebas rápidas

```bash
python tools/scraper.py --test              # solo 3 medios por corpus
python tools/scraper.py --corpus nacional    # solo un corpus
python tools/scraper.py --provincia Tucumán  # solo una provincia
```

---

## Modo test diario (temporal — prueba de una semana)

> **Activo solo durante la prueba actual.** El objetivo es ver cómo varían los
> datos día a día antes de fijar la cadencia y el horario definitivos de la
> corrida semanal (METODOLOGIA.md §8.4, todavía pendiente). No reemplaza el
> flujo oficial de arriba.

Correr **todos los días** de la semana de prueba, en este orden:

```bash
python tools/scraper.py
python tools/analyzer.py
python analisis/seguimiento_diario.py
```

El tercer paso es específico de esta prueba:
- Archiva el `titulares.csv` de hoy como `datos/crudos/{semana}/titulares_YYYY-MM-DD.csv`,
  porque si se corre el scraper otra vez dentro de la misma semana ISO, sobreescribe
  el archivo original (comportamiento normal, ver `workflows/correr_scraping.md`).
- Agrega una fila a `analisis/seguimiento_diario.csv` con fecha, titulares
  scrapeados y matches del día.
- Regenera `analisis/seguimiento_diario.html` con un gráfico de línea simple.

**Para ver el resultado:** abrir `analisis/seguimiento_diario.html` en el browser
después de cada corrida. Muestra la evolución día a día.

### Visualización provisoria en el dashboard oficial

Además del HTML standalone, el seguimiento diario aparece **dentro de
`docs/index.html`** mientras dura la prueba: un panel con borde punteado
naranja, etiquetado **"⚠ PRUEBA TEMPORAL · SEGUIMIENTO DIARIO"**, ubicado
justo debajo del resumen automático y antes del mapa. Se regenera solo:
cada `python tools/generar_dashboard.py` lee `analisis/seguimiento_diario.csv`
y agrega el punto del día al gráfico.

**Cómo desaparece al terminar la prueba:** el bloque está condicionado a que
exista `analisis/seguimiento_diario.csv`. Si se borra ese archivo, la próxima
corrida de `generar_dashboard.py` deja de renderizar el panel — no hace falta
tocar el template. Si en cambio se quiere limpiar el código por completo
(no solo dejar de mostrarlo), buscar el comentario `PROVISORIO` en:
- `tools/generar_dashboard.py` — constante `RUTA_SEGUIMIENTO_DIARIO`, función
  `cargar_seguimiento_diario()`, y la clave `seguimiento_diario` del contexto.
- `tools/templates/dashboard.html.j2` — el bloque `{% if seguimiento_diario %}`
  en el HTML y su `new Chart(...)` correspondiente en el `<script>` final.

### Al terminar la semana de prueba

1. Revisar `analisis/seguimiento_diario.csv` — ¿hay variación día a día que
   justifique correr más seguido, o la cadencia semanal alcanza?
2. Documentar la decisión y el día/horario elegido en `METODOLOGIA.md` §8.4
   y en `CHANGELOG.md`.
3. `analisis/seguimiento_diario.py` y sus archivos generados quedan como
   registro de la prueba, pero no se integran al dashboard oficial.

---

## Publicar cambios

```bash
git add .
git commit -m "..."
git push
```

Si `git push` falla con error 403 de permisos, las credenciales de git en la
máquina no tienen acceso de escritura al repo — hay que resolverlo desde GitHub
(agregar colaborador) o reconfigurar las credenciales locales, no es un problema
del código.
