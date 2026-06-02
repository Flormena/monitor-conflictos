# CHANGELOG

> Bitácora de cambios al método y al sistema. Cada entrada registra qué cambió, cuándo y por qué.
> Cualquier modificación a `METODOLOGIA.md`, al corpus de medios o a las palabras clave debe registrarse aquí.

---

## [No publicado]

### Dashboard v2 (2026-06-01)
- **Paleta Okabe-Ito apta para daltónicos**: reemplaza la paleta anterior. Rojo `#CC0000`
  reservado para "represión"; el resto usa Okabe-Ito (distinguible para deuteranopía,
  protanopía y tritanopía).
- **Tendencia semanal**: reemplaza el gráfico de barras CSS por una línea Chart.js.
- **Small multiples**: 8 mini-gráficos SVG (uno por palabra) con la misma escala Y para
  comparación directa. Generados por Jinja2 en Python, sin librería JS.
- **Mapa de símbolos proporcionales**: círculos por provincia, radio = √menciones, color =
  palabra dominante. Paths SVG horneados en Python desde GeoJSON GADM 4.1. Sin librería
  de mapas en el browser. El mapa muestra menciones (eco mediático), no eventos verificados.
  Ponderación igual por provincia (3 medios cada una). Ver METODOLOGIA.md §7.2.
- **Composición del conflicto**: barra apilada Chart.js por semana.
- **Sin CDN**: Chart.js servido localmente desde `docs/assets/chart.v4.min.js`.
  Script one-shot `tools/descargar_assets.py` descarga Chart.js y el GeoJSON.
- **Streamgraph**: bloque comentado en el template para activar cuando haya ≥6 meses de datos.
  Requerirá D3 v7 cuando se active.
- **METODOLOGIA.md §7.1 y §7.2** actualizados para reflejar la arquitectura de activos locales
  y las nuevas visualizaciones.

### Decisiones metodológicas
- **Filtro de bigramas para "marcha" (§8.2 resuelta)**: se adopta Opción B —
  lista de exclusión por bigramas. Análisis de W18 y W23 mostró tasa de FP del 22%
  en "marcha" (umbral para Opción B: >15%). Lista inicial: `en marcha`,
  `marcha atras`, `marcha blanca`, `marcha de la economia`, `marcha de los precios`.
  Implementada en `BIGRAMAS_EXCLUIDOS` en `tools/analyzer.py`. Ver METODOLOGIA.md §8.2.
- **Categorización de medios nacionales**: los medios del corpus 2 (nacional) se
  registran con `provincia = "Nacional"`, `region = "Nacional"` y
  `ciudad_origen = "Nacional"` en lugar de vacío. Permite agruparlos coherentemente
  junto a las regiones provinciales (AMBA, Centro, Cuyo, NOA, NEA, Patagonia) en
  gráficos comparativos sin mezclarlos en agregaciones provinciales.
  Ver METODOLOGIA.md §5.4.
- **Tolerancia de bajadas/copetes como titulares**: los selectores CSS capturan
  ocasionalmente copetes o sumarios además de títulos estrictos. Se asume como ruido
  de fondo constante y no se filtra. Consistente con el objetivo de detectar
  tendencias temporales, no eventos individuales (METODOLOGIA.md §1.2).

### Corridas
#### [2026-04-30] · Primera corrida completa del scraper
- 79 medios procesados, 75 exitosos, 4 fallidos
- 3589 titulares extraídos en `datos/crudos/2026-W18/`
- Medios fallidos a revisar más adelante:
  * RAFAELA NOTICIAS (Santa Fe) — ConnectionError
  * CONTEXTO (Tucumán) — ConnectionError
  * MINUTO FUEGUINO (Tierra del Fuego) — ConnectionError
  * PUNTO UNO (Salta) — Conectó pero extrajo 0 titulares (probable problema de selectores)
- Casos con baja extracción a monitorear:
  * RIOJA VIRTUAL (8 titulares)
  * CUTRAL CO AL INSTANTE (25 titulares)
  * FORMOSA AHORA (19 titulares)

### Añadido
- Dependencia `pyyaml` agregada al stack. Necesaria para que el scraper lea
  `config/parametros.yaml`.
- Estructura de carpetas del proyecto (`workflows/`, `tools/`, `config/`,
  `datos/`, `docs/`).
- Configuración base: `config/palabras_clave.csv`, `config/medios_provinciales.csv`,
  `config/medios_nacionales.csv`, `config/parametros.yaml`.
- `tools/scraper.py`: primer tool funcional. Descarga HTML y extrae titulares.
  Solo responsabilidad de datos crudos; no analiza palabras clave.
- `workflows/correr_scraping.md`: SOP para la corrida semanal.

---

## [2026-04-29] · Inicio del proyecto

### Añadido
- `CLAUDE.md`: instrucciones operativas del proyecto (framework WAT)
- `METODOLOGIA.md`: documento metodológico inicial con 7 decisiones pendientes
- `README.md`: presentación pública del proyecto
- `CHANGELOG.md`: este archivo

### Decisiones tomadas en la fundación
- **Marco conceptual**: inspiración en Beverly Silver (*Forces of Labor*, 2003)
- **Objetivo**: detección de tendencias temporales, no documentación de eventos individuales
- **Corpus**: dos corpus separados (provincial y nacional)
- **Palabras clave iniciales**: huelga, paro, movilización, represión, piquete, protesta, marcha, reclamo
- **Frecuencia**: scraping semanal, manual en esta primera fase
- **Alcance del scraping**: solo home pages (sin secciones internas)
- **Hosting**: GitHub + GitHub Pages, publicación manual

### Decisiones pendientes
Ver sección 8 de `METODOLOGIA.md`. Se difieren a las primeras 4-8 semanas de operación.
