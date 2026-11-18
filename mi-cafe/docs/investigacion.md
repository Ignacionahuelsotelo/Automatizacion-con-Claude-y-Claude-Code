# Mi Café: cómo armar un resumen de noticias argentinas que se lea en 3 minutos (noviembre 2026)

Para que Mi Café funcione, separá los números de las noticias. Los indicadores tienen que salir de APIs, no de lo que escriba la IA: DolarApi para el dólar, ArgentinaDatos para el riesgo país y la inflación, el BCRA para las reservas, Rava para el MSCI Merval y data912 para las acciones. Las noticias, de los RSS de medios gratuitos y bien calificados (Infobae, Página/12, Ámbito, Olé, elDiarioAR, y TN y La Nación como contraste). Todo tiene que entrar en unas 600 palabras: un bloque de indicadores y 8 o 9 noticias de 50 a 60 palabras, cada una con su enlace y su fecha.

## TL;DR

- **Fuentes:** el eje gratuito y con RSS es Infobae, Página/12, Ámbito, Olé y elDiarioAR. Clarín (647.000 suscriptores digitales) y La Nación (386.000), según el Digital News Report 2026, tienen muro de pago medido: sirven para contrastar, pero no conviene que sean el único enlace de una nota. Según el Digital News Report 2026 del Reuters Institute, la confianza en "las noticias en general" en Argentina cayó al 26%, aunque TN (55%), Infobae (53%) y La Nación (50%) siguen por encima del 50% de confianza como marcas.
- **Indicadores:** DolarApi (sin clave) para oficial, blue, MEP, CCL, mayorista, tarjeta y cripto; ArgentinaDatos para riesgo país, inflación e históricos; BCRA v4.0 (sin clave) para reservas; la API de Series de Tiempo de datos.gob.ar o la del INDEC para el IPC; Rava (cierre diario) para el Merval y data912 para las acciones (sin respaldo para el índice: ver Caveats). El índice, desde el 19 de octubre de 2026, se llama **MSCI Merval** (ticker MMSCI).
- **Formato y controles:** en español se leen 218 palabras por minuto según el estudio IReST (Trauzettel-Klosinski y Dietz, 2012), así que 3 minutos equivalen a unas 650 palabras. Hay que apuntar a 550–650. Según el estudio de la EBU y la BBC, el 45% de las respuestas de los asistentes de IA sobre noticias tuvo al menos un problema significativo. Por eso: ningún número que no venga de una API con fecha, enlace obligatorio en cada nota, filtro por fecha de publicación y un agente "corrector" antes de publicar.

## Key Findings

### 1. Fuentes por sección: confianza, acceso y RSS

**Cómo está la confianza.** El Digital News Report 2026 del Reuters Institute (publicado el 16 de junio de 2026, con 2.036 encuestas en Argentina) muestra que la confianza en las noticias bajó seis puntos y quedó en 26%, el nivel más bajo de la década. El promedio global es 37%. La confianza en marcas concretas se sostiene mejor: Telefe Noticias 61%, TN 55%, Infobae 53%, El Trece 52%, LN+ 52% y La Nación online 50%. En la edición 2025, Clarín tenía 44% de confianza y 29% de desconfianza, y Página/12 un 31% de desconfianza. Conclusión: ningún medio alcanza para todo. Conviene mezclar marcas de distinta línea editorial y, en temas polémicos, citar dos fuentes.

**Acceso y feeds (verificado con directorios de terceros a octubre–noviembre de 2026):**

| Medio | Acceso | RSS público | Uso recomendado en Mi Café |
|---|---|---|---|
| Infobae | Gratis | https://www.infobae.com/arc/outboundfeeds/rss/ (feed con artículos completos; unas 1.144 publicaciones por día). Por sección: /arc/outboundfeeds/rss/category/{sección}/ | Fuente base para política, economía, internacional y tecnología |
| Página/12 | Gratis | Página oficial de feeds: …/arc/outboundfeeds/rss/portada, /secciones/el-pais/notas, /secciones/economia/notas, /secciones/el-mundo/notas | Contraste editorial en política y economía |
| Ámbito | Gratis (según el directorio Inkline) | https://www.ambito.com/rss/ultimas-noticias.xml, /rss/home.xml, /rss/economia.xml, /rss/pages/finanzas.xml. Probados el 18/11/2026 y en uso: /rss/politica.xml, /rss/mundo.xml, /rss/pages/deportes.xml, /rss/tecnologia.xml. Sin sección (no se usan): ultimas-noticias (0 de ayer) y home | Economía y mercados; también política, internacional, deportes y tecnología |
| elDiarioAR | Gratis | https://www.eldiarioar.com/rss/ | Política y sociedad |
| Olé | Acceso no confirmado (puede tener algún tipo de restricción) | https://www.ole.com.ar/rss/ultimas-noticias/ (unas 73 publicaciones por día; hay feeds por club) | Deportes |
| Clarín | Muro de pago medido con registro. Al lanzarlo, en 2017, daba 10 notas gratis más 30 con registro; hoy el conteo es dinámico | https://www.clarin.com/rss/lo-ultimo/, /rss/politica/, /rss/mundo/, /rss/economia/ (solo resúmenes) | Para detectar temas; evitar que sea el único enlace |
| La Nación | Muro de pago medido que se ajusta al lector | https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml (unas 256 publicaciones por día) | Para detectar temas y contrastar |
| Perfil | Gratis | Probado el 18/11/2026: https://www.perfil.com/feed/{internacional,deportes,tecnologia} (50 ítems, pubDate en GMT). En uso | Internacional, Deportes y Tecnología |
| iProfesional | Gratis | Probado el 18/11/2026: https://www.iprofesional.com/rss/{politica,tecnologia} (22 y 18 ítems). /rss/economia anda pero con 0 notas de ayer; /rss/internacional da 404. En uso: política y tecnología | Tecnología y política |
| El Cronista | Muro medido | Probado el 18/11/2026: https://www.cronista.com/arc/outboundfeeds/rss/category/economia-politica/?outputType=xml (48 ítems, 21 de ayer). La categoría tecnología trae 0 ítems. En uso | Economía, como contraste |
| TN | Gratis | Probado el 18/11/2026: https://tn.com.ar/rss.xml (100 ítems) trae `pubDate` en ISO 8601 (no RFC 822) y no hay feeds por sección: **no se usa** (la lectura exige fecha RFC 822 y no se tocó) | Descartado |
| Chequeado | Gratis | Sin sección de las cinco: no se probó | Verificar datos |

**Prioridad por sección:**
- **Política:** Infobae y elDiarioAR, con Página/12 o La Nación como contraste según el tema.
- **Economía:** Ámbito e Infobae, con Página/12 (incluido el suplemento Cash) como contraste. Las cifras salen siempre de las APIs.
- **Deportes:** Olé y la sección deportes de Infobae.
- **Tecnología:** la categoría tecnología de Infobae e iProfesional. Ningún medio argentino se destaca claramente en esta sección.
- **Internacional:** "El Mundo" de Página/12, Infobae y "Mundo" de Clarín (solo para detectar temas).

Un detalle: **Télam ya no existe como agencia de noticias**. El Decreto 548/2024 la convirtió en una empresa de publicidad (APE S.A.U.), así que cualquier "fuente Télam" posterior a 2024 es sospechosa.

### 2. Indicadores: dónde consultarlos y con qué API

| Indicador | Fuente / API | Qué publica | Actualización | Condiciones |
|---|---|---|---|---|
| Dólar oficial, blue, MEP (bolsa), CCL, mayorista, tarjeta, cripto | **DolarApi**: https://dolarapi.com/v1/dolares y /v1/dolares/{blue, oficial, bolsa, contadoconliqui…} | Compra, venta y `fechaActualizacion` | Intradiaria. Un sitio que la usa dice que se actualiza "cada pocos minutos durante horario bancario", pero DolarApi no lo documenta oficialmente | Gratis, sin clave, código MIT, CORS habilitado |
| Histórico del dólar, riesgo país, inflación mensual e interanual, UVA | **ArgentinaDatos**: /v1/finanzas/indices/riesgo-pais/ultimo, /inflacion, /inflacionInteranual | Serie con `fecha` y `valor` | Riesgo país diario (EMBI de J.P. Morgan); inflación mensual (INDEC) | Sin límite numérico, pero pide "una consulta cada 3 horas y por serie", guardar una copia local y citar "ArgentinaDatos https://argentinadatos.com" |
| Reservas internacionales, tipo de cambio mayorista A3500, tasas (TAMAR, BADLAR), base monetaria | **BCRA, Estadísticas Monetarias v4.0**: api.bcra.gob.ar/estadisticas/v4.0/monetarias/1 (1 = reservas) | Serie diaria en millones de USD (cifras provisorias) | Diaria, días hábiles. La hora de publicación no está documentada: hay que leer `ultFechaInformada` | Sin autenticación, control de tráfico por IP, máximo 3.000 filas por consulta. **La v3 se dio de baja el 28/02/2026**, así que hay que usar v4.0 |
| IPC (nivel general y núcleo), EMAE, tipo de cambio BNA | **API de Series de Tiempo**: apis.datos.gob.ar/series (IPC: 148.3_INIVELNAL_DICI_M_26). También existe una API propia del INDEC, lanzada en noviembre de 2026 y todavía en beta | Series con transformaciones (`percent_change`, `percent_change_a_year_ago`) | Mensual, según el calendario del INDEC | Cuotas por IP: 60 por segundo, 2.000 por minuto, 40.000 por hora y 200.000 por día; máximo 1.000 filas |
| MSCI Merval (cierre diario) | **Rava, histórico por fecha**: https://www.rava.com/cotizaciones/historico/merval/AAAA/MM/DD/ (ej. /2026/11/17/) | El HTML trae un bloque JSON-LD (FAQPage) con el cierre, la variación %, el mínimo y el máximo del día. Ej.: "El MERVAL cerro a 81.794 el 17 de noviembre de 2026… suba del 0,4%" | Un cierre por día hábil; el día en curso da 404 hasta que cierra la rueda (y los fines de semana/feriados también: hay que retroceder hasta el último día con página) | Gratis, sin clave, `robots.txt` abierto (`Disallow:` vacío). Es scraping, no API: el formato puede cambiar. Rava lo titula "MERVAL", no "MSCI Merval": el nombre lo pone el código. El cierre se valida contra la fecha de la URL; el código retrocede hasta 7 días buscando el último día con página. Formato: "81.794 puntos". **Respaldo data912: desactivado** (ninguna ruta trae el índice, ver Caveats); si Rava falla, "sin dato". Verificado el 18/11/2026 (13/11: 85.096; 17/11: 81.794) |
| Acciones líderes (GGAL, YPFD, PAMP, BMA…) | **data912**: https://data912.com/historical/stocks/{TICKER} (diario con `date`, `o`, `h`, `l`, `c`, `v`) y /live/arg_stocks (todas en una consulta) | Precio de cierre (`c`, en pesos) por fecha: se toma la última fila con `date` menor o igual a ayer y se formatea `$ 4.770,00`; `/live` además trae `pct_change`, puntas y volumen | Diaria. `/live` se actualiza cada ~20 s según la documentación de terceros, pero hay caché y la propia API dice que es "educativa", no tiempo real | Gratis, sin clave, sin registro; 120 consultas por minuto según una skill de terceros. API no oficial, mantenida por una persona. Verificado el 18/11/2026: GGAL 4.770, YPFD 6.040, PAMP 4.290 |
| Respaldo de acciones | **Yahoo Finance**. **No se usa (decisión del 18/11/2026)**; los datos de la prueba quedan como antecedente (endpoint `query1.finance.yahoo.com/v8/finance/chart/GGAL.BA?interval=1d&range=5d`) | Velas diarias con timestamp, en pesos | Diaria | Antecedente: gratis, sin clave, pero no oficial: puede cortar o pedir cabeceras. Funcionaba con GGAL.BA, YPFD.BA y PAMP.BA (coinciden con data912). **No sirve para el índice**: `^MERV` quedó congelado en el valor viejo (2.848.945, sin velas) y `MMSCI.BA` trae una sola vela del día |
| ~~BYMADATA~~ | open.bymadata.com.ar | Índices y precios | — | **Descartada**: la API oficial es comercial y el endpoint público no respondió (timeout) desde acá en dos intentos; las librerías de terceros que lo usan (PyOBD) dependen de que no cambie |

#### Formato y controles de acciones

- Valor numérico mayor que 0; fecha válida y no futura.
- En Rava, la fecha del texto del JSON-LD coincide con la de la URL.
- Retroceso de hasta 7 días en Rava; si se agota, "sin dato" (el respaldo de data912 está desactivado).
- Desactualizado si el dato supera 1 día hábil; se muestra siempre la fecha del dato y no la de la consulta.
- Copia local en `datos/acciones.json`, 3 horas, y una consulta fallida no se guarda como vigente.
- Formato: acciones `$ 1.234,50`; índice `81.794 puntos`.
- Sin dato antes que dato dudoso. Nunca un valor viejo sin marcarlo.

Sobre el Merval: desde el 19 de octubre de 2026 lo calcula MSCI en lugar de S&P y se llama **MSCI Merval** (ticker MMSCI; el índice general es GMSCI). Cualquier IA entrenada antes va a decir "S&P Merval". Es un ejemplo perfecto de dato desactualizado que hay que corregir por regla.

Ojo con los agregadores: distintos tableros de terceros muestran valores de riesgo país muy diferentes según la fecha y el proveedor (por ejemplo, un sitio mostraba un dato "con 26 h de antigüedad"). Por eso cada número tiene que mostrarse con su fecha.

### 3. Formato: cómo lo hacen los newsletters matutinos

| Newsletter | Estructura | Largo |
|---|---|---|
| **Axios AM** (Mike Allen) | "Smart Brevity": titular, dato en negrita, "Why it matters" en 1–2 líneas, viñetas | Unas 1.191 palabras en una edición (Fast Company, 2019); cada nota por debajo de 300 palabras |
| **Morning Brew** | Mercados, nota principal, notas cortas, juegos y recomendaciones | Promete 5 minutos; la parte de noticias se lee en unos 5 minutos y la edición completa ronda las 2.300 palabras |
| **Semafor Flagship** | Mapa con 10 noticias numeradas más 2 extra | Unas 150 palabras por noticia |
| **The Morning (NYT)**, David Leonhardt | 1–2 temas analizados y después una ronda de enlaces breves | Unas 1.000 palabras en el texto principal; sale a las 6:30 (hora de Nueva York) |
| **Primera mañana (Cenital)**, Florencia Halfon Laksman | "Las noticias que importan", de lunes a viernes, con firma y voz propia | Breve |
| **Recomendadas AM (Infobae)**, Juan Mascardi | Síntesis a las 7, de lunes a viernes | Breve (en 2023 se informó que Infobae discontinuó varias newsletters; hay que confirmar que siga activa) |

Qué tienen en común: una apertura que se entiende sola, secciones fijas siempre en el mismo orden, una o dos frases por idea, negritas para escanear y un enlace para profundizar. Ninguno de estos productos cabe en 3 minutos. Mi Café tiene que ser **más corto que todos**.

**Cálculo del largo:** el metaanálisis de Brysbaert (2019), con 190 estudios, da 238 palabras por minuto en lectura silenciosa de no ficción (en lectores de inglés), y el estudio IReST (Trauzettel-Klosinski y Dietz, 2012) midió 218 palabras por minuto en español, con 250 lectores. En 3 minutos entran unas 650–700 palabras. Para tener margen frente a cifras y nombres propios, el objetivo es **550–650 palabras**.

### 4. Errores frecuentes al resumir con IA y cómo evitarlos

Evidencia: el estudio de la EBU y la BBC (octubre de 2025; 22 medios públicos, 18 países, 2.709 respuestas evaluadas de ChatGPT, Copilot, Gemini y Perplexity) encontró que el 45% de las respuestas tenía al menos un problema significativo. El 31% tenía problemas de fuentes y el 20% errores graves de exactitud, como detalles inventados o información desactualizada. Gemini llegó al 76%, contra 37% de Copilot, 36% de ChatGPT y 30% de Perplexity. El 16 de enero de 2025, Apple suspendió los resúmenes de notificaciones de noticias de Apple Intelligence después de que uno atribuyera a la BBC el titular falso "Luigi Mangione shoots himself". Los reactivó en iOS 26, marcados en cursiva y con la leyenda "Summarized by Apple Intelligence". En Argentina, casi uno de cada diez ya se informa con chatbots de IA, 4 puntos más que en 2025, según el DNR 2026.

| Error | Cómo se ve en un resumen | Control |
|---|---|---|
| Noticias viejas | Se incluye una nota de hace días porque "aparece" en la búsqueda | Filtrar por `pubDate` del RSS dentro de la ventana definida (ayer de 0 a 24 h; los lunes, de viernes a domingo); descartar lo que no tenga fecha |
| Datos inventados | Cifras "plausibles" del dólar o de la inflación | El modelo **nunca** escribe números: los inserta el código desde la API. Si falta el dato, "sin dato" |
| Mezcla de fechas | Se da el IPC de agosto como si fuera el de septiembre, o el riesgo país de anteayer como si fuera de hoy | Mostrar la fecha de cada indicador y marcarlo si tiene más de 1 día hábil (o más de 1 mes en los mensuales) |
| Atribución errónea | "Según Clarín…" algo que dijo otro medio | Cada nota lleva el enlace a la fuente original y el corrector verifica que el resumen esté en ese texto |
| Nombres desactualizados | "S&P Merval", "agencia Télam" | Un glosario de vigencia en la skill (MSCI Merval desde el 19/10/2026; Télam cerrada) |
| Duplicados | La misma noticia en dos secciones o en días seguidos | Deduplicar por URL y título contra los últimos 3 resúmenes |
| Sesgo de una sola fuente | Todo el resumen sale de un medio | Máximo 3 notas por medio; en temas polémicos, dos fuentes |

## Recommendations: la receta de Mi Café

**Fuentes (RSS):** Infobae (general y por categoría), Página/12 (portada, el país, economía, el mundo), Ámbito (economía y finanzas), Olé (últimas noticias), elDiarioAR. Clarín y La Nación se leen por RSS solo para detectar temas; el enlace va al medio gratuito siempre que lo haya.

**Indicadores, en este orden y con fecha:**
1. Dólar oficial, blue, MEP y CCL, con la brecha calculada: **DolarApi** /v1/dolares.
2. Riesgo país: **ArgentinaDatos** /riesgo-pais/ultimo.
3. MSCI Merval: cierre del último día hábil desde **Rava** (página histórica por fecha, leer el JSON-LD); el respaldo en data912 está desactivado, así que si Rava falla o no trae dato válido, "sin dato". Acciones líderes (GGAL, YPFD, PAMP): **data912** `/historical/stocks/{ticker}`, tomando la última fila con `date` ≤ ayer. Sin Yahoo. Cada valor se muestra con su fecha de cierre. Si la fuente no responde o la fecha no es la del último día hábil, "sin dato".
4. Reservas: **BCRA v4.0** (variable 1).
5. Última inflación mensual e interanual: **ArgentinaDatos** o **Series de Tiempo** (INDEC).

Guardar una copia local diaria en datos/ y consultar cada serie como máximo una vez cada 3 horas, como pide ArgentinaDatos.

**Estructura (unas 600 palabras en total):**
- Apertura: 1 frase con "lo más importante de hoy" (unas 25 palabras).
- Indicadores: tarjetas con valor, ▲/▼, fecha y fuente (unas 60 palabras, sin prosa).
- Política: 2 noticias.
- Economía: 2 noticias.
- Internacional: 2 noticias.
- Deportes: 1–2 noticias.
- Tecnología: 1 noticia.
- Cada noticia: título de hasta 10 palabras, 1–2 frases (40–50 palabras), una línea de "por qué importa", y medio, fecha y enlace.
- Cierre opcional: "Lo que viene hoy", 1 línea con agenda.

**Controles anti-errores (en la skill y en el agente corrector):**
1. Ningún número sin fuente y fecha; si no hay dato, "sin dato". Los números los pone el código, nunca el modelo.
2. Ventana temporal estricta: ayer, y los lunes de viernes a domingo. Descartar notas sin `pubDate` o fuera de la ventana.
3. Enlace obligatorio en cada noticia; el corrector abre el enlace y verifica que el resumen esté respaldado por el texto.
4. Máximo 3 notas por medio y dos fuentes en temas polémicos.
5. Deduplicación contra los últimos 3 resúmenes.
6. Glosario de vigencia (MSCI Merval, Télam, versiones de API) y alerta si una API devuelve 410 o un dato con fecha vieja.
7. Contar las palabras antes de guardar: si pasa de 650, recortar desde Deportes y Tecnología, nunca los indicadores.

## Cobertura medida de los feeds

Medición hecha el 18/11/2026 (miércoles) con `noticias.obtener` y los 12 feeds de `config.FUENTES_RSS`, todos los temas tildados. "Leídas" son las notas con fecha y link que trae el feed; "en ventana" las que caen en la ventana; "elegidas" las que quedan tras deduplicar y aplicar el tope por medio. La tabla de abajo es la medición **antes** de la spec 33, cuando el tope se contaba sobre todas las secciones juntas (por eso Infobae queda en 0 en varias); la medición posterior está después de ella.

**Día hábil: miércoles 18/11/2026 (ventana: martes 17/11, tope 3 por medio).**

| Medio | Sección | Leídas | En ventana | Elegidas |
|---|---|---|---|---|
| Infobae | Política | 100 | 31 | 0 |
| elDiarioAR | Política | 97 | 22 | 3 |
| Página/12 | Política | 25 | 9 | 3 |
| Infobae | Economía | 100 | 44 | 0 |
| Ámbito (economia.xml) | Economía | 97 | 13 | 1 |
| Ámbito (finanzas.xml) | Economía | 20 | 2 | 2 |
| Página/12 | Economía | 25 | 9 | 0 |
| Página/12 | Internacional | 25 | 7 | 0 |
| Infobae | Internacional | 0 | 0 | 0 (sin ítems) |
| Olé | Deportes | 10 | 0 | 0 (ningún ítem en la ventana) |
| Infobae | Deportes | 100 | 42 | 3 |
| Infobae | Tecnología | 0 | 0 | 0 (sin ítems) |

Notas que muestra la lista ese día: Política 6, Economía 3, Internacional 0, Deportes 3, Tecnología 0.

**Después de la spec 33 (misma medición, repetida el 18/11/2026 con red real, cupo 3 por medio y sección).** Las columnas "Leídas" y "En ventana" no cambian; "Elegidas" pasa a: Infobae Política 3, elDiarioAR Política 3, Página/12 Política 3, Infobae Economía 3, Ámbito economia.xml 1 y finanzas.xml 2 (3 en total para Ámbito / Economía), Página/12 Economía 3, Página/12 Internacional 3, Infobae Deportes 3, y 0 en Infobae Internacional, Olé Deportes e Infobae Tecnología (sin ítems o fuera de ventana). La lista muestra: Política 9 (antes 6), Economía 9 (antes 3), Internacional 3 (antes 0), Deportes 3, Tecnología 0; 24 notas en total, unos 6,6 mil caracteres. Tecnología sigue en 0 porque el feed de Infobae no trae ítems (eso lo resuelve la spec 34, no esta). El resumen sigue con máximo 3 notas por medio en total.

**Lunes (simulado): se corrió la misma función con la fecha del lunes 16/11/2026 (ventana: viernes 13 a domingo 15, tope 5).** Es una simulación hecha el 18/11 con lo que los feeds traían ese día, no una lectura en vivo de un lunes; los feeds ya habían empujado fuera buena parte del fin de semana, así que subestima la cobertura real de un lunes y hay que repetirla un lunes de verdad.

| Medio | Sección | Leídas | En ventana | Elegidas |
|---|---|---|---|---|
| Infobae | Política | 100 | 11 | 5 |
| elDiarioAR | Política | 97 | 21 | 5 |
| Página/12 | Política | 25 | 0 | 0 |
| Infobae | Economía | 100 | 0 | 0 |
| Ámbito (economia.xml) | Economía | 97 | 22 | 5 |
| Ámbito (finanzas.xml) | Economía | 20 | 0 | 0 |
| Página/12 | Economía | 25 | 2 | 2 |
| Página/12 | Internacional | 25 | 0 | 0 |
| Infobae | Internacional | 0 | 0 | 0 (sin ítems) |
| Olé | Deportes | 10 | 0 | 0 (ningún ítem en la ventana) |
| Infobae | Deportes | 100 | 0 | 0 |
| Infobae | Tecnología | 0 | 0 | 0 (sin ítems) |

Hallazgos: Infobae Internacional e Infobae Tecnología siguen sin traer ítems (como el 11/11/2026), así que Tecnología queda sin notas. Olé trae solo 10 ítems y ninguno de ayer. Los feeds de Infobae y los de elDiarioAR y Ámbito traen 97 a 100 ítems pero cubren pocas horas de días anteriores.

**Después de la spec 34 (18/11/2026, red real, día hábil con ventana del martes 17/11).** Se probaron los candidatos con `urllib` (HTTP, `<channel>`, ítems con `pubDate` con zona y link http(s), y cuántos de ayer). Se agregaron 10 feeds (22 en total).

| Medio | Sección | Leídas | En ventana | Elegidas |
|---|---|---|---|---|
| iProfesional | Política | 22 | 8 | 3 |
| Ámbito (politica.xml) | Política | 20 | 2 | 2 |
| El Cronista | Economía | 48 | 21 | 3 |
| Ámbito (mundo.xml) | Internacional | 100 | 17 | 3 |
| Perfil | Internacional | 50 | 11 | 3 |
| Ámbito (deportes) | Deportes | 20 | 4 | 3 |
| Perfil | Deportes | 50 | 1 | 1 |
| Ámbito (tecnologia.xml) | Tecnología | 20 | 4 | 3 |
| Perfil | Tecnología | 50 | 1 | 1 |
| iProfesional | Tecnología | 18 | 5 | 3 |

Los 12 feeds anteriores dieron lo mismo (Página/12 Política pasó de 9 a 8 en ventana por el momento de la lectura). La lista de "Noticias de ayer" pasa de Política 9, Economía 9, Internacional 3, Deportes 3, Tecnología 0 (24 notas) a **Política 14, Economía 12, Internacional 9, Deportes 7, Tecnología 7 (49 notas)**, sin feeds caídos. Medios distintos con notas de ayer: Tecnología 3 (Ámbito, Perfil, iProfesional), Internacional 3 (Página/12, Ámbito, Perfil), Deportes 3 (Infobae, Ámbito, Perfil). Olé e Infobae Internacional y Tecnología siguen sin traer notas.

## Caveats

- Los datos de acceso y RSS de varios medios salen de directorios de terceros (Feeder, Inkline, Feedspot) con verificaciones de octubre–noviembre de 2026, no de las páginas oficiales de cada diario, salvo en el caso de Página/12. Los muros de pago cambian seguido: conviene probar cada feed al instalar la app.
- Los cupos de notas gratis de Clarín y La Nación (10 + 30) son de 2017; hoy el conteo es dinámico.
- DolarApi no documenta oficialmente su frecuencia ni sus límites; el blue es un valor informal que agrega la propia API.
- Merval y acciones: **ninguna fuente gratuita es oficial**. BYMADATA quedó descartada (API comercial; el endpoint público no respondió). Lo que sí anda hoy, probado el 18/11/2026: Rava (scraping de HTML) para el índice y data912 (API no oficial) para las acciones. Pueden cambiar sin aviso, por eso el servidor tiene que validar la fecha y caer en "sin dato".
- Respaldo del índice en data912: **no existe**. Probado el 18/11/2026: `MERV` y `MMSCI` devuelven "no tengo ese ticker" y `/live/arg_stocks` no incluye el índice. El respaldo quedó desactivado: si Rava falla, el MSCI Merval sale "sin dato". Yahoo tampoco se usa (`^MERV` congelado, `MMSCI.BA` con una sola vela).
- Los largos de Axios, Morning Brew y Semafor vienen de reseñas y análisis de terceros, y algunos son de hace años.
- La API del INDEC está en beta (noviembre de 2026); por ahora conviene usar Series de Tiempo como respaldo.