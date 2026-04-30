# Metodología

> Documento metodológico del Monitor de Conflictos Sociales · Argentina.
> Fuente de verdad para todas las decisiones del proyecto.
> Cualquier cambio aquí debe registrarse en `CHANGELOG.md`.

---

## 1. Marco conceptual

### 1.1 Inspiración

El proyecto se inspira en la metodología desarrollada por **Beverly Silver** y su equipo en *Forces of Labor* (Cambridge University Press, 2003). Silver y colaboradores rastrearon menciones de conflictos laborales en diarios británicos desde el siglo XIX, construyendo series temporales largas para detectar **ciclos de conflictividad** y **olas de movilización** asociadas a transformaciones del capitalismo global.

La hipótesis subyacente es que la cobertura mediática, aunque imperfecta, **funciona como un proxy razonable de la frecuencia real de conflictos**, especialmente cuando se mantiene una metodología consistente a lo largo del tiempo.

### 1.2 Objetivo del proyecto

**Detectar tendencias temporales** en la conflictividad social argentina mediante el rastreo automatizado de palabras clave en titulares de medios digitales. El énfasis es en **variaciones relativas** (semana a semana, mes a mes, año a año, entre regiones, entre provincias con distinto signo político) y no en la documentación precisa de eventos individuales.

### 1.3 Lo que el proyecto NO es

- No es un registro exhaustivo de conflictos (para eso existen otros instrumentos: ACLED, MOVES, CELS).
- No es una base de datos de eventos verificados.
- No reemplaza el conocimiento cualitativo aportado por militantes, organizaciones y redes territoriales.
- No pretende capturar conflictos que no llegan a la cobertura mediática.

### 1.4 Supuesto metodológico central

> **El aumento o disminución de menciones de palabras clave en medios funciona como proxy de variaciones en la frecuencia real de conflictos**, siempre que se mantenga constante el método (mismo corpus, mismas palabras, misma frecuencia, misma normalización).

Este supuesto es discutible y se asume con prudencia. La ventaja de explicitarlo es que **cualquier crítica al proyecto puede dirigirse contra el supuesto, no contra los datos**.

---

## 2. Corpus de medios

### 2.1 Estructura de dos corpus separados

El proyecto mantiene **dos corpus que se procesan y reportan por separado**:

**Corpus 1 — Provincial (capilaridad territorial)**
- 3 medios locales por provincia argentina (24 provincias × 3 = 72 medios)
- Objetivo: capturar conflictividad tal como la cubren los medios locales del lugar donde ocurre
- Cada provincia pesa igual estadísticamente, sin importar volumen poblacional

**Corpus 2 — Nacional (agenda nacional)**
- ~10 grandes diarios con sede en CABA y proyección nacional
- Objetivo: capturar qué conflictos escalan a la agenda nacional
- Se reporta como serie temporal independiente

### 2.2 Por qué dos corpus

Mezclar ambos distorsiona los datos: un paro nacional aparecería simultáneamente en los 72 medios provinciales y en los 10 nacionales (82 menciones), aplastando estadísticamente a un conflicto local que solo aparece en 3 medios provinciales (3 menciones). La separación permite leer cada serie en su lógica propia y, eventualmente, cruzarlas.

### 2.3 Criterios de selección de medios

**Para el corpus provincial:**
- Cobertura local efectiva (no replicadores de cables nacionales)
- Estabilidad (medios con presencia digital sostenida)
- Diversidad editorial dentro de cada provincia cuando es posible
- Lista base disponible en `config/medios_provinciales.csv`

**Para el corpus nacional:**
- Lista base provista en `config/medios_nacionales.csv`
- 🔶 **DECISIÓN PENDIENTE — Sección 8.1**

### 2.4 Versionado del corpus

**Cualquier cambio en la lista de medios** (alta, baja, modificación) constituye un **punto de quiebre en las series temporales**. La serie antes y después no es estrictamente comparable.

Cuando se modifique el corpus:
1. Documentar el cambio en `CHANGELOG.md` con fecha y razón
2. Marcar el punto de quiebre visualmente en el dashboard (línea vertical)
3. Reportar las series como segmentadas (antes/después del cambio)

---

## 3. Palabras clave

### 3.1 Lista actual

Las 8 palabras clave en uso son:

| Palabra | Conflicto rastreado |
|---|---|
| huelga | Suspensión organizada del trabajo |
| paro | Cese de actividad (sentido laboral o de protesta) |
| movilización | Acción colectiva en espacio público |
| represión | Acción coercitiva del Estado o fuerzas privadas |
| piquete | Bloqueo de calles, rutas o accesos |
| protesta | Manifestación pública de oposición |
| marcha | Desplazamiento colectivo con finalidad reivindicativa |
| reclamo | Demanda explícita ante instituciones o empresas |

Lista canónica en `config/palabras_clave.csv`.

### 3.2 Justificación

Las 8 palabras provienen de la propuesta original del proyecto y cubren las principales formas de **acción colectiva contenciosa** en la tradición argentina: desde la huelga clásica (movimiento obrero) hasta el piquete (movimientos territoriales post-2001), pasando por la marcha y la movilización (formas más amplias).

Se incluye "represión" como categoría asimétrica: rastrea **respuestas estatales o patronales** al conflicto, no el conflicto en sí. Esto permite analizar la relación entre conflictividad y respuesta represiva.

### 3.3 Normalización lingüística

Las palabras se buscan en el titular después de:
- Pasar todo a minúsculas
- Eliminar tildes (`huelga` matchea `huélga` y viceversa)
- Eliminar caracteres no alfanuméricos para el matching
- Detección por **palabra completa** (regex `\b...\b`), no substring

**Esto significa que "movilización" no matchea "automovilización" ni "desmovilización".** Decisión consciente para evitar falsos positivos.

### 3.4 Falsos positivos conocidos

Casos en que una palabra clave aparece sin referirse a un conflicto:

- **"paro"** → "paro cardíaco", "paro de motor", "tiro al paro"
- **"marcha"** → "la marcha de la economía", "ponerse en marcha", "Marcha (banda)"
- **"protesta"** → "objeto de protesta" (en contextos no políticos)
- **"reclamo"** → "reclamo publicitario", "reclamo de seguros"

🔶 **DECISIÓN PENDIENTE — Sección 8.2:** estrategia de filtrado de falsos positivos.

### 3.5 Versionado de la lista

Igual que el corpus de medios: agregar o quitar palabras genera **puntos de quiebre** en las series. Documentar siempre en `CHANGELOG.md`.

---

## 4. Procedimiento de scraping

### 4.1 Qué se scrapea (fase actual)

**Solo la home page de cada medio.** No se scrapean secciones internas (Política, Locales, Provincia, etc.).

**Justificación de esta decisión inicial:**
- Simplicidad técnica y mantenibilidad
- La home refleja la decisión editorial del medio sobre qué destacar
- Estandarización entre medios (todos tienen home; las secciones varían)
- Permite empezar a acumular datos rápido

**Limitaciones reconocidas:**
- Conflictos cubiertos pero relegados a secciones internas no se capturan
- La home cambia varias veces al día; el scraper captura solo el momento de la corrida
- Sesgo editorial del medio: lo que jerarquiza vs. lo que oculta

🔶 **DECISIÓN PENDIENTE — Sección 8.3:** evaluar incorporación de secciones internas tras primeras semanas de datos.

### 4.2 Frecuencia y regularidad

**El scraping se ejecuta de forma manual, una vez por semana, en día y horario fijos** definidos por el usuario.

Justificación: la regularidad temporal es **condición necesaria** para que las series sean comparables. Si una semana se corre el lunes 9am y otra el miércoles 18hs, se introducen ciclos artificiales (lunes vs. miércoles tienen distinta intensidad noticiosa, mañana vs. tarde también).

🔶 **DECISIÓN PENDIENTE — Sección 8.4:** definir día y horario fijos de corrida tras primeras pruebas.

### 4.3 Estrategia técnica

Para cada medio, en orden:

1. **Request HTTP con headers de navegador** (User-Agent realista)
2. Parseo del HTML con BeautifulSoup
3. Extracción de texto de elementos con selectores priorizados (`h1`, `h2`, `h3`, `.title`, etc.)
4. Filtrado por longitud (entre 15 y 300 caracteres) para descartar fragmentos
5. Deduplicación local (mismo titular dentro del mismo medio)

Para diarios que bloqueen el método 1, se evaluará después:
- RSS feed (cuando exista)
- Request con headers más completos
- Playwright (último recurso, requiere consulta previa)

### 4.4 Manejo de errores

- Timeout por medio: 15 segundos
- Delay entre medios: 2 segundos (cortesía de scraping)
- Si un medio falla, se loggea pero no detiene la corrida
- Los HTML crudos se guardan en `datos/crudos/YYYY-Www/` para reprocesamiento futuro

### 4.5 Datos crudos vs. procesados

**Los HTML scrapeados se conservan versionados.** Si en el futuro se cambia la lógica de detección, los crudos permiten reprocesar sin volver a scrapear (lo que sería imposible: la web cambia constantemente).

---

## 5. Análisis y conteo

### 5.1 Detección de palabras clave en titulares

Para cada titular extraído:
1. Normalización lingüística (sección 3.3)
2. Búsqueda de cada palabra clave por palabra completa
3. Si matchea ≥1 palabra, el titular se registra como conflicto detectado
4. Las palabras encontradas se listan en el campo `palabras_clave`

### 5.2 Conteo

Cada titular detectado genera un registro en el CSV con:

```
fecha, diario, provincia, region, titular, palabras_clave, cantidad_palabras, url_medio
```

🔶 **DECISIÓN PENDIENTE — Sección 8.5:** conteo de palabras múltiples en un mismo titular.

### 5.3 Deduplicación entre medios

🔶 **DECISIÓN PENDIENTE — Sección 8.6:** estrategia de deduplicación cuando una misma noticia aparece en múltiples medios.

### 5.4 Agregaciones

A partir del CSV procesado se generan:

- Conteos por palabra / fecha / provincia / región
- Conteo de titulares totales scrapeados (denominador para normalización)
- Series temporales por palabra y por agrupación geográfica

Mapeo provincia → región:

| Región | Provincias |
|---|---|
| AMBA | Buenos Aires, CABA |
| Centro | Córdoba, Santa Fe, Entre Ríos |
| Cuyo | Mendoza, San Juan, San Luis |
| NOA | Tucumán, Salta, Jujuy, Santiago del Estero, Catamarca, La Rioja |
| NEA | Chaco, Corrientes, Misiones, Formosa |
| Patagonia | Neuquén, Río Negro, Chubut, Santa Cruz, Tierra del Fuego, La Pampa |

---

## 6. Normalización

### 6.1 El problema

Distintos medios publican distinta cantidad de noticias por día. Un medio con 200 titulares en home y otro con 30 titulares no son comparables en bruto: el primero "casi seguro" va a tener más menciones de cualquier palabra simplemente por volumen.

### 6.2 Estrategia propuesta

Reportar la métrica principal como **densidad**:

```
densidad = menciones de palabra clave / titulares totales scrapeados
```

Esto mide qué proporción del flujo informativo se ocupa de conflictos, no el volumen absoluto. Es robusto a cambios en cobertura editorial general.

🔶 **DECISIÓN PENDIENTE — Sección 8.7:** validar tras primeras semanas si la densidad es la métrica principal o si se reportan ambas (densidad + volumen) en paralelo.

### 6.3 Niveles de agregación para normalización

La normalización puede aplicarse a distintos niveles:
- Por medio
- Por provincia
- Por región
- Nacional (todo el corpus)

Todos los niveles se mantendrán disponibles en el dashboard.

---

## 7. Output: dashboard y publicación

### 7.1 Formato del dashboard

HTML autocontenido (un solo archivo) con datos embebidos como JSON. Sin dependencias de servidor: se publica como sitio estático en GitHub Pages.

### 7.2 Visualizaciones incluidas

- KPIs: menciones totales, medios cubiertos, provincias activas, palabra y región más frecuentes
- Serie temporal con media móvil
- Distribución por palabra clave
- Heatmap provincia × palabra
- Ranking de provincias
- Tabla de titulares filtrable

### 7.3 Filtros del dashboard

- Por región
- Por provincia
- Por palabra clave
- Por rango de fechas

### 7.4 Publicación

**Fase actual: manual.** El usuario corre los scripts localmente, revisa los datos, hace `git push` cuando los datos están conformes. GitHub Pages publica automáticamente.

**No se contempla automatización en esta fase.** Cuando el sistema esté maduro y los datos sean confiables se evaluará GitHub Actions.

---

## 8. Decisiones pendientes

> Estas decisiones se difieren deliberadamente. Se resolverán **con datos en mano** tras las primeras semanas de corridas, no a priori. Cada una se moverá a la sección correspondiente del documento cuando se tome.

### 8.1 Composición final del corpus nacional

**Pregunta:** ¿qué medios incluir en el Corpus 2?

**Propuesta inicial a evaluar:**

| Medio | Línea editorial estimada |
|---|---|
| La Nación | Centro-derecha, mainstream |
| Clarín | Centro-derecha, mainstream |
| Infobae | Centro-derecha, generalista |
| Perfil | Centro, generalista |
| Crónica | Popular, generalista |
| Página 12 | Centro-izquierda, oficialismo K |
| El Destape | Centro-izquierda, oficialismo K |
| Tiempo Argentino | Centro-izquierda |
| Ámbito | Centro-derecha, económico |
| El Cronista | Económico |

**Criterios para decidir:**
- ¿La selección cubre el espectro político-editorial razonablemente?
- ¿Hay medios que técnicamente no son scrapeables y conviene excluir?
- ¿Se incluye Olé (deportivo) o medios temáticos similares?
- ¿BAE Negocios suma o duplica con Cronista/Ámbito?

**Cuándo decidir:** después de primera corrida de prueba sobre los 10 candidatos. Excluir los que no respondan al scraping básico y evaluar el equilibrio editorial resultante.

### 8.2 Filtrado de falsos positivos

**Pregunta:** ¿cómo manejar falsos positivos como "paro cardíaco" o "la marcha de la economía"?

**Opciones:**

- **A) No filtrar.** Asumir el ruido como ruido de fondo constante. Si los falsos positivos representan ~2-5% del total y son estables en el tiempo, no afectan tendencias.
- **B) Lista de exclusión por bigramas.** Mantener una lista de combinaciones que cancelan el match: `paro cardíaco`, `paro de motor`, `marcha de la economía`. Si el titular contiene un bigrama de exclusión, no cuenta.
- **C) Filtrado contextual.** Análisis más sofisticado del contexto de la palabra (palabras circundantes). Más complejo, requiere reglas o modelo NLP.

**Criterios para decidir:**
- Estimar magnitud real de falsos positivos en una muestra de las primeras semanas
- Si <5% y constantes: opción A
- Si 5-15%: opción B con lista mantenida en `config/`
- Si >15% o creciente: revisar opción C

**Cuándo decidir:** tras 4-6 semanas de datos, cuando se pueda muestrear y cuantificar.

### 8.3 Incorporación de secciones internas

**Pregunta:** ¿scrapear solo home o sumar secciones (Política, Provincia, Locales)?

**Opciones:**

- **A) Mantener solo home.** Simplicidad y consistencia, asumiendo que se pierden conflictos secundarios.
- **B) Sumar 1 sección política/provincial estandarizada por medio.** Más cobertura, pero requiere mapear URLs por medio y mantener actualizadas.
- **C) Estrategia adaptativa por medio.** Cada medio según su estructura. Máxima cobertura, máxima fragilidad técnica.

**Criterios para decidir:**
- ¿La cobertura de la home es suficiente para detectar tendencias?
- ¿Hay conflictos importantes que claramente no estamos capturando?
- ¿El esfuerzo de mantener secciones se justifica por el aporte adicional?

**Cuándo decidir:** tras 6-8 semanas de datos. Comparar muestralmente con cobertura de eventos conocidos (ej. paros generales documentados) para evaluar tasas de captura.

### 8.4 Día y horario de corrida fija

**Pregunta:** ¿qué día y a qué hora correr el scraping semanal?

**Consideraciones:**
- Lunes mañana captura el fin de semana, suele ser día con muchos conflictos políticos
- Miércoles/jueves es más representativo del flujo informativo "normal"
- Viernes captura toda la semana laboral
- Mañana temprano (8-9hs) vs. tarde (18-19hs) cambia qué noticias están en home

**Cuándo decidir:** tras primeras pruebas técnicas, cuando el sistema esté listo para entrar en operación regular.

### 8.5 Conteo de palabras múltiples por titular

**Pregunta:** un titular como "Paro y movilización frente al Congreso" contiene 2 palabras clave. ¿Cómo contarlo?

**Opciones:**

- **A) Cuenta como 1 menc** ión "compuesta", con campo `palabras_clave` listando ambas.
- **B) Cuenta como 2 menciones independientes** (una por palabra), generando 2 filas en el CSV.
- **C) Cuenta como 1 mención por palabra**: la palabra "paro" suma +1 a su serie y "movilización" suma +1 a la suya, pero el titular se registra como 1 evento.

La opción C es la más sensata teóricamente y la que el script actual implementa. Pero implica que la suma de menciones por palabra ≠ cantidad de titulares con conflicto. Hay que comunicarlo bien en el dashboard.

**Cuándo decidir:** ya está implementado como C, pero validar con datos si genera confusión interpretativa.

### 8.6 Deduplicación entre medios

**Pregunta:** si "Paro general convocado por la CGT" aparece en 50 medios el mismo día, ¿cómo lo contamos?

**Opciones:**

- **A) Cuenta como 50 menciones.** Mide eco mediático / magnitud de cobertura.
- **B) Cuenta como 1 mención del evento.** Mide cantidad de eventos distintos. Requiere detectar similitud de titulares (algoritmos como difflib, embeddings).
- **C) Ambas métricas en paralelo.** Reportar volumen mediático Y cantidad de eventos únicos.

La opción A es la más simple y es lo que el script actual hace. La B y C requieren más desarrollo.

**Criterios para decidir:**
- Si el dashboard solo mostrara A, ¿se distorsionarían las tendencias por paros generales?
- ¿La deduplicación automática es confiable o introduce más error que el que resuelve?

**Cuándo decidir:** tras 4-6 semanas de datos. Si se observa que pocos eventos masivos dominan las series, vale la pena implementar B o C.

### 8.7 Métrica principal: densidad vs. volumen

**Pregunta:** ¿la métrica principal del dashboard es densidad (proporcional) o volumen absoluto?

**Opciones:**

- **A) Solo densidad** (menciones / titulares totales). Robusta, comparable entre medios y períodos.
- **B) Solo volumen absoluto.** Más intuitivo, pero sesgado por cambios en cobertura general.
- **C) Densidad como métrica principal, volumen como secundaria.** Reportar ambas, destacar la densidad.

**Cuándo decidir:** tras 4-6 semanas. Probar visualizaciones de ambas y ver cuál comunica mejor las tendencias reales.

---

## 9. Limitaciones reconocidas

Lista no exhaustiva de limitaciones que el proyecto **asume conscientemente** y que cualquier interpretación de los datos debe tener en cuenta:

1. **Sesgo de cobertura mediática.** Conflictos no cubiertos por la prensa local no aparecen.
2. **Sesgo editorial.** Cada medio decide qué destacar. La línea editorial afecta qué queda en home.
3. **Sesgo geográfico.** Provincias con menos medios digitales activos tienen menor "resolución" en los datos.
4. **Sesgo temporal del scraping.** Solo se ve la home en el momento de la corrida. Noticias rotativas pueden perderse.
5. **Falsos positivos lingüísticos.** No todo "paro" es un paro laboral.
6. **Falsos negativos lingüísticos.** Conflictos que no usen las 8 palabras clave (ej. "movilizamiento", "huelguista", "manifestación") no se detectan.
7. **No verificación.** Los datos son menciones en titulares, no eventos verificados.
8. **No análisis de contenido.** El proyecto cuenta apariciones, no analiza qué dice la nota.

---

## 10. Reproducibilidad

Para que cualquier persona pueda reproducir o auditar los datos:

1. Todo el código está en GitHub
2. La metodología está documentada en este archivo
3. Los HTML crudos se versionan en `datos/crudos/`
4. Los cambios se registran en `CHANGELOG.md`
5. El corpus y las palabras clave están en archivos CSV en `config/`

Cualquiera con acceso al repositorio puede:
- Ver qué medios y palabras se usaron en cada momento histórico
- Re-procesar HTML crudos con métodos alternativos
- Replicar las series temporales

---

## 11. Referencias

- Silver, B. (2003). *Forces of Labor: Workers' Movements and Globalization since 1870*. Cambridge University Press.
- ACLED Conflict Index — https://acleddata.com/series/acled-conflict-index
- MOVES Database, University of Washington — https://depts.washington.edu/moves/
- ITUC Global Rights Index — https://www.ituc-csi.org
- ILO STAT — https://ilostat.ilo.org/data/

---

*Última actualización: ver `CHANGELOG.md`*
