# CLAUDE.md

Monitor de conflictividad social en Argentina. Rastreo semanal de palabras clave en titulares de medios locales y nacionales. Detección de **tendencias temporales**, no eventos individuales.

## Framework: WAT

- **Workflows** (`workflows/*.md`): SOPs en lenguaje claro. Leer el correspondiente antes de actuar.
- **Tools** (`tools/*.py`): scripts deterministas. Buscar uno existente antes de crear nuevo.
- **Agent** (vos): coordinás. No ejecutás directamente lo que un tool puede hacer.

Si un workflow falla: arreglar tool, verificar, actualizar workflow. No sobrescribir workflows sin pedir.

## Estructura

```
CLAUDE.md  README.md  METODOLOGIA.md  CHANGELOG.md
workflows/         SOPs en markdown
tools/             scripts Python
config/            CSV/YAML editables (palabras_clave, medios_*, parametros)
datos/crudos/      HTML scrapeado por semana (versionado, NO descartable)
datos/procesados/  conflictos.csv acumulativo
datos/snapshots/   YYYY-Www.csv por semana
docs/              dashboard publicado en GitHub Pages
```

## Convenciones de código

Cada script en `tools/` debe tener al inicio:

```python
# ════ PARÁMETROS EDITABLES ════
TIMEOUT = 15
DELAY = 2
# ═══════════════════════════════
```

Decisiones metodológicas hardcodeadas se marcan así:

```python
# DECISIÓN METODOLÓGICA: ver METODOLOGIA.md §4.2
```

Comentarios, variables, logs y mensajes en **español**. Excepción: términos técnicos universales (`url`, `timeout`, `parse`).

## Regla de oro

**El código sigue al método.** Antes de modificar `config/palabras_clave.csv`, `config/medios_*.csv`, `tools/analyzer.py` o `tools/normalizer.py`:

1. Discutir implicancia metodológica con el usuario
2. Actualizar `METODOLOGIA.md`
3. Anotar en `CHANGELOG.md` (fecha, qué, por qué)
4. Recién después: tocar código

Si el usuario pide saltarse pasos, recordáselo.

## Restricciones

- No agregar dependencias sin avisar (stack actual: requests, beautifulsoup4, pandas, lxml, jinja2)
- No automatizar (GitHub Actions, cron) hasta que el usuario lo indique. Fase actual: manual.
- No borrar `datos/crudos/`. Permiten reprocesar si cambia el método.
- No editar `docs/index.html` a mano: regenerarlo con `tools/generar_dashboard.py`
- No usar Playwright sin consultar. Para diarios que bloquean: primero RSS, después request con headers, recién después escalar.

## Flujo manual (fase actual)

```bash
python tools/runner.py --test               # 3 medios, prueba rápida
python tools/runner.py                       # corrida completa
python tools/generar_dashboard.py            # regenera docs/index.html
# revisar datos y dashboard
git add . && git commit -m "..." && git push # publicación a GitHub Pages
```

## Análisis ad hoc

Si el usuario pide un gráfico nuevo o exploración puntual: **no tocar tools principales**. Crear script en `analisis/` o usar notebook.

## Criterios metodológicos clave

Recordatorios. Fuente de verdad: `METODOLOGIA.md`.

- Dos corpus separados (provincial / nacional). No se mezclan.
- Cada provincia pesa igual en el corpus provincial.
- Métrica principal: densidad (menciones / titulares totales), no volumen absoluto.
- Regularidad: mismo día y hora cada semana.
- Cualquier cambio en corpus o palabras = punto de quiebre en serie temporal. Documentar.
