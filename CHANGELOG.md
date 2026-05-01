# CHANGELOG

> Bitácora de cambios al método y al sistema. Cada entrada registra qué cambió, cuándo y por qué.
> Cualquier modificación a `METODOLOGIA.md`, al corpus de medios o a las palabras clave debe registrarse aquí.

---

## [No publicado]

### Decisiones metodológicas
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
