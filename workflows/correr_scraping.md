# Workflow: Correr el scraping semanal

## Cuándo correr

Una vez por semana, **mismo día y misma hora** (ver METODOLOGIA.md §8.4 — día/hora
todavía pendiente de definir). La regularidad temporal es condición necesaria para
que las series sean comparables.

---

## Comandos

```bash
# Prueba rápida antes de la corrida completa (3 medios por corpus)
python tools/scraper.py --test

# Corrida completa (todos los medios activos, ambos corpus)
python tools/scraper.py

# Solo corpus nacional
python tools/scraper.py --corpus nacional

# Solo corpus provincial
python tools/scraper.py --corpus provincial

# Solo una provincia
python tools/scraper.py --provincia Tucumán
```

---

## Qué genera el scraper

```
datos/crudos/YYYY-Www/
├── provincial/
│   ├── la-voz-del-interior-cordoba.html
│   ├── el-dia-buenos-aires.html
│   └── ...
├── nacional/
│   ├── infobae.html
│   ├── la-nacion.html
│   └── ...
├── titulares.csv          ← input para el analyzer
└── scraping.log           ← registro de la corrida
```

El archivo `titulares.csv` tiene las columnas:
`fecha, semana_iso, corpus, diario, provincia, region, ciudad_origen, url_medio, titular`

Los HTML crudos **no se descartan nunca** (ver METODOLOGIA.md §4.5 y CLAUDE.md).

---

## Cómo interpretar el output por consola

Cada medio imprime una línea de dos partes:

```
[PROVINCIAL] LA GACETA (Tucumán) — https://www.lagaceta.com.ar
  → OK | 47 titulares extraídos
```

Los estados posibles son:

| Estado | Significado |
|---|---|
| `OK` | Descarga exitosa |
| `TIMEOUT` | El medio no respondió en el tiempo límite (TIMEOUT en parametros.yaml) |
| `HTTP 403` / `HTTP 404` | El servidor rechazó o no encontró la página |
| `FALLO (ConnectionError)` | Sin conexión o DNS no resolvió |

Al final se imprime el resumen:

```
Resumen: 80 medios procesados | 74 exitosos | 6 fallidos | 3210 titulares totales
```

---

## Qué hacer si fallan medios

### 1–3 medios fallando → normal, ignorar

Fallas aisladas son esperables (sitios caídos, mantenimiento, sobrecarga). No afectan
las tendencias mientras sean pocas y distribuidas aleatoriamente.

### El mismo medio falla semanas seguidas → investigar

1. Probá la URL manualmente en el navegador
2. Si carga en el browser pero falla el scraper → el medio probablemente bloquea bots
3. Estrategia de escalada (ver METODOLOGIA.md §4.3):
   - Primero: probar con headers más completos
   - Después: buscar RSS feed
   - Último recurso: Playwright (consultar antes de implementar)
4. Si no tiene solución: marcar `activo = False` en el CSV correspondiente y
   documentar en CHANGELOG.md con fecha y razón

### Corpus entero falla → problema de red

Verificar conexión a internet antes de asumir un problema del scraper.

---

## Después de la corrida

1. Revisar el `scraping.log` — buscar medios con 0 titulares o estados de error
2. Abrir `datos/crudos/YYYY-Www/titulares.csv` y hacer una revisión rápida:
   - ¿Los titulares parecen reales y en español?
   - ¿Hay medios con muy pocos titulares (< 5)?
3. Continuar con el analyzer: `python tools/analyzer.py` (próxima fase)

---

## Parámetros ajustables

Todos en `config/parametros.yaml`:

| Parámetro | Default | Cuándo cambiar |
|---|---|---|
| `TIMEOUT` | 15 | Aumentar si muchos medios dan TIMEOUT en red lenta |
| `DELAY` | 2 | Aumentar si se sospecha bloqueo por velocidad |
| `MAX_TITULARES` | 50 | Ajustar tras ver distribución real (ver METODOLOGIA.md §8.7) |

---

## Notas metodológicas

- El scraper captura la **home en el momento de la corrida**. Noticias rotadas antes
  o después no quedan registradas (ver METODOLOGIA.md §4.1).
- Si se necesita re-procesar, los HTML crudos permiten volver a extraer titulares
  con una versión nueva del analyzer sin volver a scrapear.
- Cualquier cambio en `config/medios_*.csv` (alta, baja, modificación de URL)
  genera un **punto de quiebre en las series temporales** y debe registrarse en
  CHANGELOG.md (ver METODOLOGIA.md §2.4).
