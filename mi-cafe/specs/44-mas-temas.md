# 44 - Más temas: Sociedad, Policiales, Salud y Ciencia, Espectáculos y Cultura

**Estado:** hecha

## Depende de
43-feeds-en-paralelo (con cuatro temas más, los feeds casi se duplican). También usa el diagnóstico de la spec 32 y las specs 37 y 42 (`TEMAS` única y secciones desde el servidor).

## Para qué
Hoy los temas elegibles son cinco. Se suman cuatro, en un orden fijo, para que la persona pueda armar un resumen con lo que le interesa. Como `config.TEMAS` ya es la única definición (spec 37) y la página recibe `opciones.secciones` del servidor (spec 42), el trabajo está en `config`, en los feeds, en los sinónimos y en que el prompt, el corrector y la skill traten los nombres nuevos como encabezados válidos.

## Qué tiene que hacer
1. En `micafe/config.py`, `TEMAS` pasa a: `["Política", "Economía", "Internacional", "Sociedad", "Policiales", "Deportes", "Salud y Ciencia", "Espectáculos y Cultura", "Tecnología"]`. Ese es el orden fijo en que se muestran en preferencias y en el resumen (se puede ajustar en una pregunta abierta). `SECCIONES = TEMAS` sigue siendo un alias.
2. **Verificar feeds antes de agregarlos** (como en la spec 34): con `curl -sS -A "MiCafe/1.0"` y el diagnóstico de la spec 32 (`por_fuente`: `leidas`, `en_ventana`, `elegidas`), anotar para cada candidato HTTP, si es RSS válido (`<channel>`), cuántos ítems, si todos tienen `pubDate` con zona horaria y link http(s) y cuántos caen en la ventana de ayer. Candidatos, todos por probar:
   - Infobae: `.../arc/outboundfeeds/rss/category/sociedad/`, `.../category/teleshow/`, `.../category/cultura/` (y las que existan para policiales, salud y ciencia).
   - Página/12: `.../arc/outboundfeeds/rss/secciones/sociedad/notas/`, `.../secciones/cultura/notas/` (y espectáculos o ciencia si existen).
   - Perfil: `https://www.perfil.com/feed/sociedad`, `/policia`, `/espectaculos`, `/ciencia`, `/salud`, `/cultura`.
   - Ámbito: el equivalente de cada sección (por ejemplo `/rss/pages/...xml`), probando las que existan.
   Solo entran los feeds que pasen: RSS válido, gratis (sin muro duro), con fecha y link, y con notas en la ventana. Registrar resultado y fecha de la prueba en `docs/investigacion.md`; actualizar el comentario "Probados el ..." de `config.py`.
3. Cada tema nuevo tiene **al menos 2 medios distintos** entre sus feeds de `FUENTES_RSS`. Si un tema no llega a 2 medios con feeds válidos, no se agrega a `TEMAS` y se anota en las preguntas abiertas. `tests/test_config.py` lo exige para todos los temas (también los cinco existentes).
4. **elDiarioAR:** el feed general (`https://www.eldiarioar.com/rss/`) hoy está en Política. Se reclasifica por el `<category>` de cada nota del RSS (la spec 38 ya las lee): una nota con categoría Sociedad va a Sociedad, con Política queda en Política, etc., usando una tabla `CATEGORIAS_A_TEMA` en `config.py` (categoría normalizada -> tema). Lo que no tenga categoría reconocida **se descarta de ese feed** (no se manda a Política por defecto). Si al verificar resulta que el feed no trae `<category>` útil, se saca de Política y se anota en `docs/investigacion.md`. La reclasificación vive en `fuentes/noticias.py` (función pura con test), y solo aplica a las fuentes marcadas con un campo opcional `reclasificar_por_categoria: True` en `FUENTES_RSS`.
5. **Sinónimos:** agregar a `SINONIMOS_TEMAS` una clave por tema nuevo (por ejemplo "sociedad", "policiales", "salud", "ciencia", "espectáculos", "cultura") con términos equivalentes razonables (conjunto inicial para validar; ver pregunta abierta). Si alguna clave nombra un tema, sumarla a `TEMA_DE_CLAVE_SINONIMO` (por ejemplo "salud" y "ciencia" -> "Salud y Ciencia") para que el aviso de tema destildado (spec 42) funcione.
6. **Prompt, corrector y skill:** los encabezados válidos salen de `config.TEMAS` (el corrector ya usa `SECCIONES`; verificar `notas_del_texto` y `notas_votables` con encabezados de dos o más palabras como "Salud y Ciencia" y "Espectáculos y Cultura": la comparación es por línea completa, no por palabra). `.claude/skills/resumen-diario/SKILL.md` y `.claude/skills/corrector/SKILL.md` dejan de nombrar las cinco secciones fijas y dicen "las secciones del plan de hoy, en el orden del plan".
7. **Plan de secciones:** `seleccion.plan_de_secciones` ya trabaja sobre `TEMAS`; revisar que con 9 temas posibles y `NOTAS_OBJETIVO = 9` se respete `MINIMO_POR_SECCION_ACTIVA` y el recorte por largo. Si con muchos temas tildados el mínimo de 1 por sección supera las 9 notas objetivo, el plan se queda con las secciones de más peso (regla de la spec 40); verificar y, si hace falta, anotarlo en preguntas abiertas.
8. **Preferencias existentes:** un `datos/preferencias.json` viejo se lee igual; los temas nuevos quedan destildados (no se agregan solos). Por defecto (sin archivo) solo se tildan los cinco temas originales, para no cambiarle el resumen a quien ya lo usa (se puede discutir en preguntas abiertas).
9. **Gustos:** `almacen/gustos.py` valida contra `config.TEMAS`, por lo que acepta votar los temas nuevos sin tocarlo (con test).
10. **Página:** sin cambios de código si `opciones.secciones` ya se usa; verificar que los nueve checkboxes aparecen, que "Elegí al menos un tema." sigue andando y que los encabezados largos no rompen el diseño.
11. `docs/investigacion.md`: tabla de feeds con los nuevos y resultado de las pruebas.

## Fuera de alcance
Subtemas de Deportes (spec 45); preferencias por prioridad, medios y palabras (49 y 50); scraping de HTML, Clarín y La Nación (decisión ya tomada); cambiar los topes por medio; cambiar el largo del resumen.

## Archivos que toca
- `micafe/config.py` (`TEMAS`, `FUENTES_RSS`, `SINONIMOS_TEMAS`, `TEMA_DE_CLAVE_SINONIMO`, `CATEGORIAS_A_TEMA`)
- `micafe/fuentes/noticias.py` (reclasificación por categoría)
- `micafe/dominio/seleccion.py`, `micafe/dominio/corrector.py` (solo si hay algo que ajustar)
- `.claude/skills/resumen-diario/SKILL.md`, `.claude/skills/corrector/SKILL.md`
- `docs/investigacion.md`
- `tests/test_config.py`, `tests/test_noticias.py`, `tests/test_seleccion.py`, `tests/test_corrector.py`, `tests/test_preferencias.py`, `tests/test_gustos.py`, fixtures nuevos en `tests/fixtures/`

## Criterios de aceptación
- [x] `config.TEMAS` tiene ocho temas (Policiales quedó afuera, ver notas) en el orden fijo; `opciones.secciones` sale de `TEMAS` (test existente en `test_servidor.py`); no se abrió la página en el navegador.
- [x] Cada tema tiene al menos 2 medios distintos en `FUENTES_RSS` y `tests/test_config.py` falla si alguno tiene menos.
- [x] Todos los feeds nuevos fueron probados a mano, están anotados con fecha en `docs/investigacion.md` y cumplen: RSS válido, gratis, con fecha y link.
- [x] El feed general de elDiarioAR ya no mete notas en Política por defecto: se reclasifica por `<category>` o se sacó (queda escrito cuál de las dos).
- [x] Una nota de elDiarioAR con categoría desconocida no aparece en ninguna sección.
- [x] Un pedido "policiales" o "ciencia" encuentra sinónimos; si el tema está destildado, el aviso de la spec 42 lo dice.
- [x] Un resumen con "Salud y Ciencia" como encabezado pasa el corrector y `notas_votables` lo toma como sección.
- [x] Un `preferencias.json` viejo se lee igual y los temas nuevos quedan destildados.
- [x] Se puede votar 👍/👎 un tema nuevo.
- [x] Con los nueve temas tildados, el plan de secciones suma `NOTAS_OBJETIVO` notas y respeta el máximo de 650 palabras (plan por código, test).
- [x] `python3 -m unittest discover -s tests -t .` pasa (379 tests). No arranqué `python3 servidor.py` a mano.

## Tests (unittest, sin red ni `claude`)
- `test_config.py`: cada tema de `TEMAS` tiene al menos 2 medios distintos; toda `seccion` de `FUENTES_RSS` está en `TEMAS`; toda URL es `https`; `SINONIMOS_TEMAS` y `TEMA_DE_CLAVE_SINONIMO` solo apuntan a temas que existen.
- `test_noticias.py`: fixture RSS de elDiarioAR con `<category>` variadas: se reclasifica, y la de categoría desconocida se descarta; un feed sin la marca no se reclasifica.
- `test_seleccion.py`: plan con los nueve temas tildados y con algunos nuevos sin candidatas; pedido "policiales" con sinónimos.
- `test_corrector.py`: encabezados de varias palabras.
- `test_preferencias.py` y `test_gustos.py`: archivo viejo, temas nuevos válidos.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir http://localhost:8000, ir a preferencias: aparecen los nueve temas. Tildar Sociedad y Policiales y preparar el resumen.
3. Ver "Noticias de ayer": hay notas de las secciones nuevas con medios distintos; en la consola del servidor, un `Feed ... en_ventana=` por cada feed nuevo.
4. Escribir en el pedido "ciencia" con ese tema destildado: aparece "Tu pedido no encontró notas de ayer" y el aviso del tema destildado.
5. Confirmar a mano que ninguna nota de Política viene de una categoría que no es política (elDiarioAR).

## Notas de implementación
- **Feeds probados el 24/11/2026** con `curl`; resultado completo en `docs/investigacion.md`. Entran: Sociedad (Infobae, elDiarioAR, Página/12), Salud y Ciencia (Infobae, iProfesional), Espectáculos y Cultura (Infobae teleshow y cultura, Página/12 cultura-y-espectaculos, Ámbito espectaculos). iProfesional salud tiene poco volumen (hoy 0 de ayer, pero notas de días cercanos).
- **Policiales queda afuera de `TEMAS`:** solo Infobae (`sociedad/policiales/`) tiene un feed válido; Perfil, Ámbito, Página/12, iProfesional y El Cronista dan 404, vacío o desactualizado. Por eso `TEMAS` tiene ocho temas, no nueve. Se puede sumar cuando aparezca un segundo medio. Quedó la clave `policiales` en `SINONIMOS_TEMAS` (sirve para encontrar notas en otras secciones, sin tema asociado en `TEMA_DE_CLAVE_SINONIMO`).
- **Orden:** Política, Economía, Internacional, Sociedad, Deportes, Salud y Ciencia, Espectáculos y Cultura, Tecnología (el propuesto, sin Policiales).
- **elDiarioAR:** el feed general no trae `<category>`, así que se sacó de Política y se reemplazó por `/rss/politica/` (verificado). La reclasificación quedó implementada igual (`reclasificar_por_categoria` en `fuentes/noticias.py`, tabla `CATEGORIAS_A_TEMA` en `config.py`, marca `reclasificar_por_categoria` en `FuenteRSS`), con test, pero ningún feed la usa hoy. Las notas reclasificadas a un tema destildado se descartan.
- **Por defecto:** `config.TEMAS_POR_DEFECTO` (los cinco originales) lo usa `preferencias.por_defecto()`. Un archivo viejo se lee igual y los temas nuevos quedan destildados.
- **Plan con muchos temas:** `plan_de_secciones` reparte el mínimo por sección en orden de peso (después orden de `TEMAS`) y corta al llegar a `total`, así que si hay más secciones activas que notas objetivo quedan las de más peso. Con ocho temas y `NOTAS_OBJETIVO = 9` no se llega a ese caso (el test lo prueba con `total=2`). No se subió `NOTAS_OBJETIVO`.
- **Skill del resumen:** ya no nombra las cinco secciones fijas. La skill del corrector no las nombraba. `corrector.py` no necesitó cambios: compara por línea completa.
- **Sinónimos:** conjunto inicial para sociedad, policiales, salud, ciencia, espectáculos y cultura; a validar con datos reales.
