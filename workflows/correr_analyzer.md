# Workflow: Correr el analyzer

## Cuándo correr

Inmediatamente después de `tools/scraper.py`, en la misma sesión semanal.
El analyzer necesita el `titulares.csv` generado por el scraper.

Orden obligatorio:
```
1. python tools/scraper.py       ← genera titulares.csv
2. python tools/analyzer.py      ← genera conflictos.csv y snapshot
3. python tools/generar_dashboard.py  ← (pendiente de implementar)
```

---

## Comandos

```bash
# Procesa la semana en curso (detecta automáticamente YYYY-Www)
python tools/analyzer.py

# Reprocesa una semana específica (útil si cambió palabras_clave.csv o el método)
python tools/analyzer.py --semana 2026-W18
```

---

## Qué genera el analyzer

```
datos/
├── procesados/
│   └── conflictos.csv         ← acumulativo histórico (crece cada semana)
├── snapshots/
│   └── 2026-W18.csv           ← foto de la semana procesada
crudos/2026-W18/
│   └── analyzer.log           ← log de la corrida
```

### `conflictos.csv` (acumulativo)

Contiene todos los titulares con al menos una palabra clave, de todas las
semanas procesadas hasta la fecha. Columnas:

```
fecha, semana_iso, corpus, diario, provincia, region,
ciudad_origen, url_medio, titular, palabras_encontradas, cantidad_palabras
```

Si se reprocesa una semana, sus filas anteriores se reemplazan (no se duplican).

### `{semana}.csv` (snapshot)

Idéntico en formato a `conflictos.csv`, pero solo contiene la semana indicada.
Útil para revisar los datos de una semana sin abrir el acumulativo completo.

---

## Cómo interpretar el output por consola

```
Analizando semana: 2026-W18
Palabras clave: huelga, paro, movilización, represión, piquete, protesta, marcha, reclamo
Titulares cargados: 3589
Snapshot → .../datos/snapshots/2026-W18.csv (247 filas)
Acumulativo → .../datos/procesados/conflictos.csv (247 filas totales, 247 de esta semana)
============================================================
Titulares leídos:  3589
Matches totales:   247  (6.9% de detección)
────────────────────────────────────────
Menciones por palabra clave:
  reclamo          87
  marcha           54
  protesta         48
  paro             36
  movilización     22
  ...
────────────────────────────────────────
Menciones por corpus:
  provincial       198
  nacional          49
────────────────────────────────────────
Top 5 medios con más menciones:
   18  LA GACETA
   15  EL DÍA
   ...
============================================================
```

*(Los números son ilustrativos, no de una corrida real)*

**Tasa de detección esperada:** entre 5% y 15% dependiendo de la semana.
Valores por fuera de ese rango merecen revisión:
- Muy baja (< 2%): verificar que `palabras_clave.csv` tenga tildes correctas
- Muy alta (> 25%): posible problema de selectores capturando contenido no-noticioso

---

## Qué hacer con los archivos generados

1. **Revisar el snapshot**: abrir `datos/snapshots/{semana}.csv` en Excel o similar
   - ¿Los titulares parecen conflictos reales? (spot check de 10-15 filas)
   - ¿Hay falsos positivos evidentes? (ej. "paro cardíaco", "marcha de la economía")
   - Si hay muchos falsos positivos: documentar en CHANGELOG.md para la decisión 8.2
2. **Verificar el acumulativo**: confirmar que el total de filas creció correctamente
3. Continuar con el dashboard: `python tools/generar_dashboard.py` (próxima fase)

---

## Notas metodológicas

- **No hay deduplicación**: si "Paro de la CGT" aparece en 50 medios, se cuentan
  50 menciones. Mide eco mediático, no cantidad de eventos (METODOLOGIA.md §8.6).
- **No hay filtrado de falsos positivos**: "paro cardíaco" y "paro laboral" cuentan
  igual. Se asume ruido constante que no distorsiona tendencias (METODOLOGIA.md §8.2).
- **Un titular con múltiples palabras clave genera 1 fila**, no N filas. La columna
  `palabras_encontradas` lista todas las palabras encontradas separadas por coma
  (METODOLOGIA.md §8.5).
- **Reproceso**: si cambian las palabras clave o el método de detección, correr
  `--semana YYYY-Www` sobre las semanas históricas rehace los resultados desde los
  HTML crudos (via titulares.csv). Documentar el reproceso en CHANGELOG.md.
