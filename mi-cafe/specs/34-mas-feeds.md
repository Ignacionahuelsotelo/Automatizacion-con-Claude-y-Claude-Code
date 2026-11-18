# 34 - Más feeds RSS por tema

**Estado:** hecha

## Depende de
32-diagnostico-de-feeds (para saber qué secciones están flojas). Idealmente después de la 33.

## Para qué
Hay pocos medios por tema (Tecnología tiene uno solo y el comentario de `config.py` lo da sin ítems; Internacional y Deportes tienen dos) y como el resumen admite como mucho 3 notas por medio, con pocos medios no se llega a las notas que pide la skill (2, 2, 2, 1 o 2, y 1). Sumar feeds públicos gratuitos, con las mismas reglas.

## Candidatos (de `docs/investigacion.md`, ninguno probado todavía)
- Ámbito: `https://www.ambito.com/rss/ultimas-noticias.xml` y `/rss/home.xml` (sin sección asignada: solo sirven si se les puede asignar una).
- TN, Perfil (`perfil.com/feed`), iProfesional, El Cronista (muro medido): feeds "activos según Inkline", URLs sin confirmar.
- Chequeado: sin sección de las cinco.
- Clarín y La Nación: muro de pago medido. Solo para detectar temas; nunca el único enlace (regla de CLAUDE.md). Ver pregunta abierta 4: no se incluyen salvo decisión expresa.
- Feeds por sección de Infobae que hoy no se usan, y de Olé por club.

## Qué tiene que hacer
1. Para cada candidato, probar a mano (por ejemplo con `curl -sS -A "MiCafe/1.0"`) y anotar: HTTP, si es un RSS válido (`<channel>`), cuántos ítems, si todos tienen `pubDate` con zona horaria y link `http(s)`, y cuántos caen en la ventana de ayer. Registrar el resultado y la fecha de la prueba en `docs/investigacion.md`.
2. Agregar a `FUENTES_RSS` de `micafe/config.py` solo los feeds que pasen: RSS válido, `pubDate` con fecha y link, al menos algunas notas en la ventana, acceso gratuito. Cada uno con `medio`, `seccion` (una de `SECCIONES`) y `url` `https`. Actualizar el comentario "Probados el …" con la fecha.
3. Prioridad: primero Tecnología, después Internacional y Deportes, después Política y Economía. Si un medio solo se puede asignar a una sección, entra solo en esa.
4. Un feed que se cae no rompe nada: se sigue con el resto y se avisa en la página (ya lo hace `noticias.obtener`).
5. Sin dependencias nuevas: solo `urllib` y `xml.etree` como hoy. Nada de `feedparser`, scraping de HTML ni APIs de noticias.
6. Si con N feeds nuevos el tiempo de lectura (serie, 10 s de timeout cada uno) hace lenta la carga de la página, no se resuelve acá: se anota en la pregunta abierta 6 (lectura en paralelo con hilos, también librería estándar).
7. Las reglas de CLAUDE.md no cambian: link en toda nota, ventana de ayer, descartar notas sin fecha, deduplicar contra los últimos 3 resúmenes, máximo 3 por medio en el resumen, 550 a 650 palabras.

## Fuera de alcance
Scraping de páginas sin RSS; fuentes pagas; Clarín y La Nación (salvo decisión); cambiar topes (spec 33); cambiar el largo o la cantidad de notas por sección; leer feeds en paralelo.

## Archivos que toca
- `micafe/config.py` (`FUENTES_RSS`)
- `docs/investigacion.md` (resultados de la prueba y tabla de fuentes)
- `tests/test_config.py` (validación de la lista), `tests/test_noticias.py`
- `.claude/skills/resumen-diario/SKILL.md` solo si cambia la prioridad de medios

## Criterios de aceptación
- [x] Cada feed nuevo tiene su prueba registrada en `docs/investigacion.md` con fecha.
- [x] Un test recorre `FUENTES_RSS` y comprueba: `medio` no vacío, `seccion` en `SECCIONES`, `url` que empieza con `https://`, y sin URLs repetidas.
- [x] Un test de `noticias.obtener` con un feed nuevo simulado (fixture) lo lee, aplica la ventana y descarta las notas sin fecha o sin link.
- [x] Según la medición de la spec 32, Tecnología, Internacional y Deportes tienen al menos tantos medios distintos como notas pide la skill (o queda anotado por qué no se pudo).
- [ ] Con un feed nuevo caído, la página muestra el aviso en español y el resto anda. (Cubierto por test de `obtener`; no se miró la página a mano.)
- [x] No se agregó ninguna dependencia ni archivo de configuración nuevo.
- [x] `python3 -m unittest discover -s tests -t .` pasa, sin red.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py` y mirar "Noticias de ayer": hay notas de los medios nuevos, cada una con su link, y los avisos de fuentes caídas (si los hay) están en español.
3. Comparar los conteos por feed del log (spec 32) antes y después.
4. Preparar un resumen un día hábil y un lunes: ningún medio pasa de 3 notas (5 el lunes), todas con link y de ayer.
5. Poner una URL inexistente en un feed de prueba: la página avisa y no se cae.

## Notas de implementación
- Se probaron con red real el 18/11/2026 (resultados en `docs/investigacion.md`). Entraron 10 feeds: iProfesional (política, tecnología), El Cronista (economía-política, asignado a Economía), Ámbito (política, mundo, deportes, tecnología) y Perfil (internacional, deportes, tecnología). TN descartado: `pubDate` en ISO 8601 y sin feeds por sección. Quedaron afuera: Ámbito ultimas-noticias/home (sin sección), iProfesional economía (0 de ayer) e internacional (404), El Cronista tecnología (0 ítems), Perfil política y economía (pocos ítems), Chequeado (sin sección). Clarín y La Nación no se agregaron (decisión).
- No se tocó la skill ni el código de lectura. Tests nuevos: validación de `FUENTES_RSS` y cada sección con al menos 2 medios (`tests/test_config.py`), y feed nuevo con ventana, sin fecha/link/fecha ISO y feed caído (`tests/test_noticias.py`, fixture `tests/fixtures/rss_perfil_gmt.xml`).
- La carga lee 22 feeds en serie (10 s de timeout cada uno); no se midió el tiempo de la página, queda para la pregunta abierta 6.
- No verificado: el aviso en la página con un feed caído, y las pruebas de un lunes real.
