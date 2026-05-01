# Monitor de Conflictos Sociales · Argentina

Rastreo automatizado de palabras clave en titulares de medios digitales argentinos para detectar **tendencias temporales** en la conflictividad social.

Inspirado metodológicamente en el trabajo de [Beverly Silver](https://en.wikipedia.org/wiki/Beverly_Silver) (*Forces of Labor*, Cambridge University Press, 2003), que rastreó menciones de conflictos laborales en diarios británicos desde el siglo XIX para construir series temporales largas.



---

## 🌐 Dashboard en vivo

→ **[Ver dashboard](https://TU_USUARIO.github.io/monitoreo-conflictos/)**

---

## ¿Qué hace?

Cada semana, el sistema:

1. Descarga las páginas de inicio de medios digitales de todas las provincias argentinas
2. Busca **8 palabras clave** asociadas a conflicto social en los titulares
3. Registra los hallazgos en una base de datos versionada
4. Genera un dashboard interactivo con tendencias por palabra, provincia y región

**Las 8 palabras clave:**
`huelga` · `paro` · `movilización` · `represión` · `piquete` · `protesta` · `marcha` · `reclamo`

---

## ¿Por qué?

La conflictividad social cotidiana —los paros, piquetes, marchas y reclamos que constituyen la lucha de clases en su forma efectiva— suele quedar fuera del radar mediático nacional o ser cubierta de manera fragmentada. Los grandes diarios porteños tienden a sobre-representar lo que pasa en CABA y subestimar lo que pasa en el interior.

Este proyecto busca:

- **Capilaridad nacional**: 3 medios por provincia, todas las provincias pesan igual
- **Lectura temporal**: detectar variaciones (semana a semana, mes a mes) más que eventos individuales
- **Rigurosidad metodológica**: cada decisión está documentada y es auditable
- **Transparencia**: todo el código, los datos y la metodología son públicos

---

## Estructura del proyecto

```
monitoreo-conflictos/
│
├── CLAUDE.md            Instrucciones para asistencia con Claude Code
├── METODOLOGIA.md       Documento metodológico completo
├── CHANGELOG.md         Bitácora de cambios al método
│
├── workflows/           SOPs en lenguaje claro
├── tools/               Scripts Python
├── config/              Parámetros editables (medios, palabras clave)
│
├── datos/
│   ├── crudos/          HTML scrapeado por semana (versionado)
│   ├── procesados/      conflictos.csv acumulativo
│   └── snapshots/       Una foto por semana
│
└── docs/                Dashboard publicado en GitHub Pages
```

---

## Metodología

El proyecto mantiene **dos corpus separados** que se reportan de forma independiente:

| Corpus | Composición | Función |
|---|---|---|
| **Provincial** | 3 medios locales × 24 provincias | Capturar conflictividad tal como la cubren los medios del lugar donde ocurre |
| **Nacional** | ~10 grandes diarios con sede en CABA | Capturar qué conflictos escalan a la agenda nacional |

La **métrica principal** es la **densidad** de menciones (proporción de titulares con palabras clave sobre el total scrapeado), no el volumen absoluto. Esto hace robusto al sistema frente a cambios en la cobertura editorial general.

📄 Ver [`METODOLOGIA.md`](./METODOLOGIA.md) para el detalle completo: corpus, palabras clave, procedimiento de scraping, análisis, normalización, limitaciones reconocidas y decisiones metodológicas pendientes.

---

## Limitaciones

El proyecto reconoce explícitamente estos límites:

- **Sesgo de cobertura**: conflictos no cubiertos por la prensa local no aparecen
- **Sesgo editorial**: cada medio decide qué destacar en su home
- **Falsos positivos**: no todo "paro" es un paro laboral (hay "paros cardíacos")
- **No verificación**: los datos son menciones en titulares, no eventos verificados
- **Métricas, no análisis**: el proyecto cuenta apariciones, no analiza el contenido de las notas

Estas limitaciones se asumen conscientemente. La cobertura mediática funciona como **proxy razonable de tendencias** cuando se mantiene una metodología consistente, no como espejo perfecto de la conflictividad real.

---

## Uso del repositorio

### Para reproducir los datos

```bash
git clone https://github.com/TU_USUARIO/monitoreo-conflictos.git
cd monitoreo-conflictos

pip install -r requirements.txt

python tools/runner.py --test         # prueba con 3 medios
python tools/runner.py                # corrida completa
python tools/generar_dashboard.py     # regenera el dashboard
```

### Para auditar la metodología

- [`METODOLOGIA.md`](./METODOLOGIA.md) explica todas las decisiones tomadas
- [`CHANGELOG.md`](./CHANGELOG.md) registra cambios al método con fecha y razón
- [`config/`](./config/) contiene los parámetros editables (medios, palabras clave)
- [`datos/crudos/`](./datos/) conserva los HTML originales para reprocesamiento

### Para colaborar

Cualquier propuesta de cambio en el corpus de medios o en las palabras clave se discute primero como cuestión metodológica (en `METODOLOGIA.md`) antes de implementarse.

---

## Estado del proyecto

🚧 **En construcción.** Etapa actual: implementación inicial, sin datos acumulados todavía.

Próximos hitos:
- [x] Documentación metodológica
- [ ] Implementación del scraper
- [ ] Primera corrida de prueba
- [ ] Publicación del dashboard
- [ ] Acumulación de datos semanales

---

## Inspiración y referencias

- Silver, B. (2003). *Forces of Labor: Workers' Movements and Globalization since 1870*. Cambridge University Press.
- [ACLED Conflict Index](https://acleddata.com/series/acled-conflict-index) — Armed Conflict Location & Event Data Project
- [MOVES Database](https://depts.washington.edu/moves/) — Mass Mobilization in Authoritarian Regimes
- [ITUC Global Rights Index](https://www.ituc-csi.org) — International Trade Union Confederation
- [ILO STAT](https://ilostat.ilo.org/data/) — International Labour Organization

---

## Licencia

Proyecto de divulgación e investigación. Uso libre con atribución.

---

*"El uso de data scrapping, usar códigos para generar datos que nos sirvan para detectar o vislumbrar tendencias en la lucha de clases es una apuesta que puede o no generar frutos. Es jardinería experimental."*

— De la propuesta original del proyecto
