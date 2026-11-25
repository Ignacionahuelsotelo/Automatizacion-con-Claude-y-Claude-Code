# Specs de Mi Café

Se construyen en este orden; cada una deja la app andando. Fuente: `docs/plan.md`.

| # | Spec | Paso del plan | Estado |
|---|---|---|---|
| 01 | [Esqueleto](01-esqueleto.md) | 1 | hecha |
| 02 | [Preferencias](02-preferencias.md) | 2 | hecha |
| 03 | [Indicadores](03-indicadores.md) | 3 | hecha |
| 04 | [Noticias](04-noticias.md) | 4 | hecha |
| 05 | [Primer resumen con Claude](05-primer-resumen.md) | 5 | hecha |
| 06 | [Skills completas](06-skills-completas.md) | 6 (parte 1) | hecha |
| 07 | [Corrector](07-corrector.md) | 6 (parte 2) | hecha |
| 08 | [Página completa y archivo de resúmenes](08-pagina-completa.md) | 7 | hecha |
| 09 | [Gustos 👍/👎](09-gustos.md) | 8 | hecha |
| 10 | [Caja de preguntas](10-caja-preguntas.md) | 9 | hecha |
| 11 | [Acciones](11-acciones.md) | 10 (parte 1) | hecha (parcialmente reemplazada por 13, 14 y 15) |
| 12 | [Manejo de errores y pulido](12-manejo-errores.md) | 10 (parte 2) | hecha |
| 13 | [Acciones GGAL, YPFD y PAMP desde data912](13-acciones-data912.md) | 10 (fuente de acciones) | hecha |
| 14 | [MSCI Merval desde Rava, respaldo data912](14-merval-rava.md) | 10 (fuente de acciones) | hecha |
| 15 | [Acciones: avisos, página y resumen guardado](15-acciones-avisos-y-resumen.md) | 10 (fuente de acciones) | hecha |
| 16 | [Docs y skills: coherencia con las fuentes de acciones](16-docs-y-skills-fuentes-acciones.md) | tarea aparte | hecha |

### Refactor a aplicación real (specs 17 a 27)

| # | Spec | Estado |
|---|---|---|
| 17 | [Red de seguridad: tests con unittest](17-tests-base.md) | hecha |
| 18 | [Paquete `micafe/`: ordenar los módulos](18-paquete-micafe.md) | hecha |
| 19 | [Configuración centralizada](19-configuracion-centralizada.md) | hecha |
| 20 | [Logging y manejo de errores consistentes](20-logging-y-errores.md) | hecha |
| 21 | [Almacén JSON compartido](21-almacen-json.md) | hecha |
| 22 | [Capa HTTP delgada y servicio de resumen](22-http-delgado.md) | hecha |
| 23 | [Tipado y docstrings](23-tipado-y-docstrings.md) | hecha |
| 24 | [Front en archivos separados](24-front-archivos-separados.md) | hecha (carga y consola verificadas en navegador el 18/11/2026) |
| 25 | [Front: calidad técnica y accesibilidad](25-front-calidad-tecnica.md) | hecha |
| 26 | [Pruebas automáticas de la página](26-pruebas-de-pagina.md) | hecha (8 casos e2e pasando el 18/11/2026) |
| 27 | [README del proyecto y CLAUDE.md al día](27-readme-y-claude-md.md) | hecha |

### Mejoras posteriores (specs 28 a 36)

| # | Spec | Depende de | Estado |
|---|---|---|---|
| 28 | [Bug: la página se rompe al tildar un tema en preferencias](28-bug-checkbox-preferencias.md) | - | hecha |
| 29 | [Chequeo de la conexión con `claude`](29-chequeo-claude.md) | - | hecha |
| 30 | [Progreso en tiempo real al preparar el resumen (polling)](30-progreso-en-tiempo-real.md) | 29 | hecha |
| 31 | [Votar las notas del resumen de hoy](31-votos-en-notas-del-resumen.md) | - (conviene después de 28) | hecha |
| 32 | [Diagnóstico de feeds: cuántas notas trae cada fuente](32-diagnostico-de-feeds.md) | - | hecha |
| 33 | [Candidatas: tope por medio y por sección](33-candidatas-por-medio-y-seccion.md) | 32 | hecha |
| 34 | [Más feeds RSS por tema](34-mas-feeds.md) | 32 (idealmente 33) | hecha |
| 35 | [Pedido de noticias en texto: backend](35-pedido-de-noticias-backend.md) | 30 | hecha |
| 36 | [Pedido de noticias en texto: página](36-pedido-de-noticias-pagina.md) | 35 y 30 | hecha |

### Adaptación del resumen: Fase A (specs 37 a 42)

| # | Spec | Depende de | Estado |
|---|---|---|---|
| 37 | [Internacional como tema elegible y filtro estricto](37-internacional-como-tema.md) | - | hecha |
| 38 | [Bajada y categorías del RSS](38-bajada-y-categorias.md) | - | hecha |
| 39 | [Selección de candidatas por puntaje](39-seleccion-por-puntaje.md) | 37, 38 | hecha |
| 40 | [Plan de secciones calculado por código](40-plan-de-secciones.md) | 39 | hecha |
| 41 | [Perfil de gustos](41-perfil-de-gustos.md) | 39, 40 | hecha |
| 42 | [Que se vea la adaptación](42-que-se-vea-la-adaptacion.md) | 40, 41 | hecha |

Orden: 37 y 38 (independientes entre sí), 39, 40, 41, 42. Decisiones aprobadas para esta fase: la cantidad de notas por sección la calcula el código cada día y, si el resumen se pasa de largo, se recorta desde las secciones de menor prioridad (la regla de `CLAUDE.md` se actualiza en la 40); un pedido sobre un tema destildado no trae nada de ese tema y la página avisa (39 y 42); reiniciar lo aprendido ignora los votos desde una fecha, sin borrarlos (41). Esta fase retoma la pregunta abierta 2 de las specs 28 a 36 (cantidades fijas) y cierra lo pendiente de la spec 36 (aviso de pedido sin notas, que se cumple con 39 y 42).

### Más temas, indicadores y preferencias: Fases B, C y D (specs 43 a 51)

| # | Spec | Depende de | Estado |
|---|---|---|---|
| 43 | [Lectura de feeds en paralelo](43-feeds-en-paralelo.md) | - | hecha |
| 44 | [Más temas: Sociedad, Policiales, Salud y Ciencia, Espectáculos y Cultura](44-mas-temas.md) | 43 | hecha |
| 45 | [Subtemas de Deportes](45-subtemas-de-deportes.md) | 44 | hecha |
| 46 | [Dólar mayorista, tarjeta y cripto; indicadores fuera de la cuenta de palabras](46-dolar-mayorista-tarjeta-cripto.md) | - | hecha |
| 47 | [Reservas elegibles y tasas del BCRA v4.0](47-reservas-y-tasas-bcra.md) | 46 | hecha |
| 48 | [Inflación mensual e interanual y UVA](48-inflacion-y-uva.md) | 46 | hecha |
| 49 | [Preferencias v2, backend](49-preferencias-v2-backend.md) | 37, 41, 44, 45, 46 a 48 | hecha |
| 50 | [Pantalla de Preferencias](50-pantalla-de-preferencias.md) | 49, 42 | hecha |
| 51 | [Docs al día](51-docs-al-dia.md) | 43 a 50 | hecha |

Orden: 43 a 45 (temas y feeds) y 46 a 48 (indicadores) son dos líneas independientes; se pueden alternar. Después 49, 50 y 51. Decisiones aprobadas para esta tanda: (2) los indicadores salen de la cuenta de 550 a 650 palabras (spec 46; reemplaza la decisión 7 del 11/11/2026); (3) la inflación se suma (reemplaza la decisión 1 del 11/11/2026); (4) Bitcoin queda afuera, el dólar cripto de DolarApi entra; (5) los feeds nuevos entran solo si responden bien y el feed general de elDiarioAR se reclasifica por `<category>` o se saca de Política; (6) no hay opción de "largo del resumen"; (9) la pantalla de Preferencias es una vista (`#preferencias`) dentro de la misma página, sin tocar `ARCHIVOS_ESTATICOS`. La lectura de feeds en paralelo (pregunta abierta 6 de las specs 28 a 36) pasa a ser la spec 43.

## Preguntas abiertas (specs 43 a 51)

Estado al 24/11/2026, comprobado contra el código (`micafe/config.py`, `micafe/almacen/preferencias.py`, `micafe/web/estatico/app.js`).

1. **Orden de los temas nuevos (44).** Resuelta: `TEMAS` quedó Política, Economía, Internacional, Sociedad, Deportes, Salud y Ciencia, Espectáculos y Cultura, Tecnología.
2. **Temas nuevos tildados por defecto (44).** Resuelta: sin archivo de preferencias solo vienen tildados los cinco originales (`TEMAS_POR_DEFECTO`).
3. **Temas con menos de 2 medios (44).** Resuelta: Policiales quedó fuera de `TEMAS` porque solo Infobae tiene un feed válido (ver `docs/investigacion.md`).
4. **Plan con nueve temas (44).** Resuelta por los hechos: con Policiales afuera hay 8 temas y `NOTAS_OBJETIVO` sigue en 9 (`MINIMO_POR_SECCION_ACTIVA` = 1), así que con todos tildados sobra 1 nota. Vigente solo si se suma un noveno tema.
5. **Sinónimos y palabras clave (44, 45).** Vigente: los conjuntos de `SINONIMOS_TEMAS` y de `SUBTEMAS` siguen siendo un conjunto inicial a validar con datos reales.
6. **Feed de Olé "últimas noticias" (45).** Resuelta: se reemplazó por los feeds por deporte (fútbol primera, fútbol internacional, tenis y básquet); `automovilismo` da 404 y quedó sin feed.
7. **Casas de DolarApi (46).** Resuelta el 24/11/2026: las tres claves (`mayorista`, `tarjeta` y `cripto`) existen.
8. **Tasas, A3500 y grupos (46 a 48).** Resuelta: grupos `tasas` (BADLAR, TAMAR y plazo fijo), `dolar_otros` (mayorista, tarjeta, cripto y A3500) e `inflacion` (mensual, interanual y UVA). Se cambia si la pantalla pide otra agrupación.
9. **Ids del BCRA v4.0 (47).** Resuelta: `config.BCRA_IDS` (reservas 1, BADLAR 7, TAMAR 44, plazo fijo a 30 días 1207, A3500 5), verificados el 24/11/2026.
10. **UVA (48).** Resuelta: sale de ArgentinaDatos (`/v1/finanzas/indices/uva`); no se usó el BCRA.
11. **Reservas por defecto (47 y 49).** Resuelta: sin archivo, `por_defecto()` tilda todos los indicadores; un archivo viejo (sin `version`) migra con `reservas` tildada y los grupos nuevos destildados.
12. **Pesos de las preferencias (49).** Vigente: los valores de `config.py` (`PESO_MEDIO_PREFERIDO`, `PESO_PALABRA_SEGUIR`, `PESO_PALABRA_EVITAR`, `PESO_PRIORIDAD_ALTA/BAJA`, pesos de subtemas y `MAXIMO_PUNTAJE_PREFERENCIAS`) se pueden ajustar midiendo con datos reales; el pedido sigue ganando.
13. **Alcance de "medio excluido" (49).** Resuelta: se descarta de las candidatas y de "Noticias de ayer" (`seleccion.habilitadas`); los resúmenes ya guardados no se tocan.
14. **Cambios sin guardar (50).** Resuelta: aviso propio al salir de la vista con cambios, sin `beforeunload`.

**Orden sugerido de construcción (specs 28 a 36):** 28 primero (es un bug); 29 y 30 (conexión y progreso) antes que 35 y 36 (el pedido usa el estado de carga); 31 en cualquier momento después de 28; 32, 33 y 34 en ese orden (medir, ajustar topes, sumar fuentes), independientes de las demás y pueden hacerse en paralelo con 29 a 31. Orden lineal: 28, 29, 30, 31, 32, 33, 34, 35, 36. La 26 ya figura como hecha (pruebas e2e opcionales en `tests/e2e/`): las specs de página (28, 30, 31, 36) se prueban a mano y, si el entorno de desarrollo está instalado, se les puede sumar un caso e2e; no es requisito.

## Preguntas abiertas (specs 28 a 36)

1. **Síntoma exacto del bug de la 28.** Leyendo el código no se pudo confirmar la causa (hay candidatas en la spec). ¿Qué se ve cuando "se rompe" (mensaje, pantalla en blanco, lista que no cambia) y qué dice la consola del navegador y la del servidor? ¿Pasa con un tilde solo o al tildar varios seguidos, o al tildar "Acciones"?
2. **Qué significa "pocas notas por tema" (33 y 34).** ¿Es la lista "Noticias de ayer" o el resumen? El resumen tiene cantidades fijas en la skill (Política 2, Economía 2, Internacional 2, Deportes 1 o 2, Tecnología 1), por el largo de 550 a 650 palabras. Las specs 32 a 34 amplían las candidatas pero no cambian esas cantidades. ¿Se quieren más notas por sección en el resumen? Eso obliga a decidir qué pasa con el largo objetivo.
3. **Tope por medio (33).** Hoy el tope de 3 por medio (5 los lunes) se aplica a la lista de candidatas sobre todas las secciones juntas, y el corrector lo vuelve a contar sobre el resumen entero. Eso hace que un medio presente en varias secciones (Infobae) deje sin candidatas a otras. La spec 33 propone contar el tope de candidatas por medio y sección y dejar la regla de 3 por medio solo para el resumen. ¿Se aprueba? Con eso la lista "Noticias de ayer" puede crecer: ¿se acepta o se limita?
4. **Clarín y La Nación como fuentes (34).** Tienen muro de pago y CLAUDE.md pide usarlos solo para detectar temas, sin ser el único enlace. Si se agregan al RSS entran como candidatas con su link. ¿Se agregan (con la skill vigilando que no sean único enlace) o no se agregan?
5. **Agregar medios nuevos (34).** No es una dependencia de código (siguen siendo `urllib` y `xml.etree`), pero CLAUDE.md pide preguntar antes de sumar dependencias externas y suma fuentes que condicionan el contenido. ¿Se aprueba probar y agregar TN, Perfil, iProfesional, El Cronista y Ámbito "últimas noticias", o hay una lista de medios que sí o que no?
6. **Lectura de feeds en paralelo.** *(Resuelta en la spec 43: `HILOS_FEEDS` en `config.py`.)* Con más feeds, leerlos de a uno (10 s de timeout cada uno) puede hacer lenta la carga de la página y la etapa "Trayendo noticias". Se podría leer en paralelo con `concurrent.futures` (librería estándar). ¿Se hace como spec aparte?
7. **Chequeo de Claude (29).** La spec usa `claude --version`, que no gasta del plan pero no comprueba que la sesión esté iniciada. La alternativa es un `claude -p` mínimo, que sí lo comprueba pero consume del plan y tarda. ¿Alcanza `--version`?
8. **Progreso en tiempo real (30).** Se recomienda polling cada 1,5 s y se descarta Server-Sent Events. ¿Se confirma?
9. **Estado del armado solo en memoria (30).** Si se reinicia el servidor en medio del armado, se pierde el seguimiento (el resumen no se guarda). ¿Está bien?
10. **Notas con dos links en el resumen (31).** Cuando la skill cita dos fuentes para un tema polémico, la spec 31 deja los botones de voto solo en el primer link. ¿Se prefiere votar cada link por separado?
11. **Pedido de noticias (35).** ¿Sirve el límite de 500 caracteres? ¿El pedido se guarda solo dentro del resumen del día (propuesta) o querés un historial o precargar el último pedido?
12. **Pedido frente a gustos y preferencias (35).** Propuesta: el pedido de hoy desempata antes que los gustos, y no puede traer notas de temas destildados ni de fuentes que no estén en la lista. Si el pedido no tiene notas aplicables, se arma con lo que haya y no se avisa. ¿Se prefiere avisar en la página?

## Preguntas abiertas (specs 37 a 42)

1. **"Acciones" y "al menos un tema" (37).** El checkbox "acciones" sigue aparte de los temas de noticias. La spec 37 propone que no cuente: hay que tildar al menos un tema de noticias aunque "acciones" esté tildado. ¿Se confirma, o alcanza con tener "acciones"?
2. **Dónde vive hoy `SECCIONES` (37).** El pedido la ubica en `app.js:37` y en el código Python; la spec manda verificar y dejar una sola definición en `config`. No se leyó el código al escribir las specs.
3. **Sinónimos iniciales (39).** El conjunto de `SINONIMOS_TEMAS` que se carga al inicio (clubes, políticos, términos de economía) es una propuesta a validar; ¿hay temas o equipos que sí o sí tienen que estar?
4. **Pesos y valores numéricos (39 a 41).** `PESOS_PUNTAJE`, `MAXIMO_POR_SECCION`, vida media de 14 días, multiplicador x3 y tope +-5 son los de la propuesta; se pueden ajustar al medir con datos reales, sin cambiar la spec.
5. **Plan incompleto (40).** Si el plan queda incompleto, el resumen puede tener menos de 550 palabras. ¿Se acepta, o se prefiere avisar en la página que "hoy hay pocas notas"? (La spec 42 lo muestra en "Cómo se armó hoy".)
6. **Prioridad de recorte (40).** El orden de recorte por largo sale del plan (pedido, pesos, orden de `TEMAS`); si se quiere un orden fijo distinto, hay que decidirlo.
7. **Reinicio de lo aprendido en la página (42).** Resuelta: entró en la 42, dentro del bloque "Cómo se armó hoy" (con `confirm`).
8. **Bajada y fuentes (38).** Algunos feeds traen `description` con publicidad o texto repetido del título; se mide al probar con feeds reales y, si hace falta, se descartan bajadas iguales al título.

**Orden del refactor:** 17 primero (sin tests no se mueve nada), después 18 a 23 en ese orden, luego 24 y 25 (front), 26 y por último 27. Cada una deja `python3 servidor.py` andando y la suite pasando. El refactor no cambia qué hace la app ni sus reglas de `CLAUDE.md`. La spec 16 es independiente del refactor (ya figura como hecha en la tabla; no se tocó). Las specs de front dicen explícitamente "sin rediseño visual, por ahora sin design-taste-frontend".

**Reemplazos:** la spec 11 queda **parcialmente reemplazada** por la 13, 14 y 15 en lo que toca a la fuente de las acciones (BYMADATA y "sin dato" permanente). Su estado no se tocó; ver el aviso al principio de `11-acciones.md`. Orden sugerido: 13, 14, 15; la 16 es independiente del código y se cierra después de la 14.

Notas de división: el paso 6 se partió en skills y corrector; el paso 10 en acciones y errores. El archivo de resúmenes (pieza 8) se construye en la spec 08, porque el plan no le da un paso propio.

## Decisiones tomadas (11/11/2026)

1. **Inflación:** fuera de v1. No entra en los indicadores. *(Reemplazada por la spec 48: la inflación mensual, la interanual y la UVA entran como indicadores.)*
2. **Dólares:** oficial, blue, MEP y CCL, con brecha calculada por el código.
3. **RSS caídos:** se descarta el feed, se sigue con el resto y se avisa en la página.
4. **Puerto y arranque:** puerto 8000, con `python3 servidor.py`.
5. **Zona horaria:** "ayer" en America/Argentina/Buenos_Aires.
6. **Temas de preferencias (lista cerrada):** Política, Economía, Deportes, Tecnología. *(Reemplazada: hoy son los 8 de `config.TEMAS`, specs 37 y 44.)*
7. **Bloque de indicadores:** cuenta dentro de las 550 a 650 palabras. (Reemplazada por la spec 46: los indicadores no cuentan.)
8. **Reintentos del corrector:** 2 como máximo; si no pasa, se muestra con aviso visible.
9. **Repetida (dedupe):** mismo link o título casi igual que una nota de los últimos 3 resúmenes.
10. **Gustos 👍/👎:** se votan notas y temas; a Claude se le pasan los últimos 30 votos.
11. **Acciones:** MMSCI (MSCI Merval), GGAL, YPFD y PAMP, sin fuente paga. Si no hay fuente gratuita estable, "sin dato". *(La parte de la fuente quedó reemplazada por la decisión 15.)*
12. **Caja de preguntas:** se elige una nota tocándola.
13. **Timeout de `claude -p`:** 5 minutos.
14. **Lunes:** el tope por medio sube a 5 (la ventana es viernes a domingo). Los demás días sigue en 3.
15. **Fuente de acciones (18/11/2026):** MSCI Merval desde Rava (página histórica por fecha, JSON-LD), con respaldo en data912 si Rava falla. GGAL, YPFD y PAMP desde data912 (`/historical/stocks/{ticker}`). Sin Yahoo ni BYMADATA. Copia local en `datos/acciones.json`. Si no hay dato confiable, "sin dato".

## Decisiones sobre las preguntas abiertas

1. **Respaldo del Merval en data912:** se prueba a mano en la spec 14; si ningún candidato trae el índice, el respaldo queda desactivado y el Merval cae en "sin dato".
2. **Fecha de corte:** último cierre con fecha menor o igual a ayer. Un cierre de hoy no se usa hasta mañana.
3. **Yahoo Finance:** no se usa. Se saca del flujo y de la investigación.
4. **Formato del índice:** `81.794 puntos` (sin `$`).
5. **Retroceso en Rava:** hasta 7 días hacia atrás y 8 consultas como máximo por pedido.
6. **Acciones en preferencias:** sigue el checkbox único "acciones"; no se eligen una por una.
7. **`docs/plan.md`:** se actualiza la sección "Riesgos" para reflejar las fuentes aprobadas (se hace en la spec 16).

## Preguntas abiertas (refactor, specs 17 a 27)

1. **RESUELTA SOLO PARA PLAYWRIGHT (18/11/2026): el usuario aprobó explícitamente Playwright (Python) y su Chromium como dependencia de desarrollo, en un entorno virtual aislado `.venv-dev/`, fuera del runtime. `pytest`, `ruff`, `mypy` y `coverage` siguen sin aprobar.** Pregunta original: **Dependencias de desarrollo.** CLAUDE.md prohíbe dependencias externas sin preguntar. Hasta que se responda, nada de esto está aprobado: `pytest` (tests; mientras tanto se usa `unittest`), `ruff` (lint y formato), `mypy` (tipos), `Playwright` (pruebas de la página, spec 26), `coverage`. En las specs se usa solo la librería estándar. ¿Se aprueba alguna como herramienta de desarrollo, aislada de la app y sin ser requisito para correrla?
2. **RESUELTA (18/11/2026): sí, se separa.** **Regla "página en un único `index.html`".** Aparece en CLAUDE.md y en `docs/plan.md` (pieza 9). Separar HTML, CSS y JS (spec 24) la cambia a "archivos estáticos propios, sin librerías externas ni build". ¿Se confirma el cambio de la regla?
3. **Nombre de la carpeta de acceso a datos.** `micafe/datos/` se confunde con `datos/` de la raíz. Propuesta: `micafe/almacen/` (spec 18, punto 1). ¿Se acepta?
4. **Valores duplicados distintos.** Si al centralizar la configuración (spec 19) aparecen timeouts u otros valores distintos para lo mismo, no se unifican sin decisión. Se listarán acá. Spec 19: timeout HTTP 10 s (indicadores, noticias) vs 15 s (acciones); User-Agent `MiCafe/1.0` vs `MiCafe/1.0 uso personal` (Rava). Se conservaron tal cual.
5. **Bugs que aparezcan al escribir tests o tipos (specs 17 y 23).** No se arreglan dentro del refactor; se listarán acá y se decide si van a una spec aparte.
6. **Ubicación de las skills de desarrollo.** Las propias de la app están en `.claude/skills/`, pero brainstorming, systematic-debugging, verification-before-completion, webapp-testing, web-design-guidelines y find-skills están hoy en `.agents/skills/`. Las specs las nombran igual; ¿conviene moverlas o enlazarlas en `.claude/skills/`?
7. **Variables de entorno.** `MICAFE_DATOS` y `MICAFE_LOG` (specs 19 y 20) son opcionales y solo para pruebas y diagnóstico. ¿Está bien sumarlas, o se prefiere que no haya ninguna?

## Decisiones tomadas (specs 28 a 36)

Respuestas a las preguntas abiertas, decididas el 2026-11-18 por pedido del usuario ("resolvelas vos con la mejor decisión"):

1. **Síntoma del bug:** no se conoce; la spec 28 manda reproducirlo y dejar la causa escrita.
2. **"Pocas notas por tema":** se ataca la lista "Noticias de ayer" (candidatas). Las cantidades del resumen siguen fijas por el largo de 550 a 650 palabras.
3. **Tope por medio (33):** aprobado, se cuenta por medio y sección; la lista puede crecer.
4. **Clarín y La Nación:** no se agregan como feeds.
5. **Medios nuevos (34):** se aprueban TN, Perfil, iProfesional, El Cronista y Ámbito, solo si el feed es RSS válido, gratis y con fecha y link.
6. **Lectura de feeds en paralelo:** queda fuera por ahora; spec aparte si hace falta. *(Reemplazada: se hizo en la spec 43.)*
7. **Chequeo de Claude (29):** alcanza `claude --version`.
8. **Polling frente a SSE (30):** polling.
9. **Estado del armado:** solo en memoria, está bien.
10. **Notas con dos links:** se vota el primero.
11. **Pedido (35):** 500 caracteres, se guarda solo dentro del resumen del día.
12. **Pedido frente a gustos y preferencias:** el pedido desempata antes que los gustos y no trae temas destildados; la página avisa cuando no hay notas aplicables.
