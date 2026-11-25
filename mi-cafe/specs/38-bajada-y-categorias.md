# 38 - Bajada y categorías del RSS

**Estado:** hecha

## Depende de
Nada (se puede hacer en paralelo con la 37). Es requisito de la 39.

## Para qué
Hoy solo se leen `title`, `link` y `pubDate` del RSS (`micafe/fuentes/noticias.py:95-108`) y el prompt manda solo el título (`micafe/dominio/resumen.py:74-79`). Un título como "Gran triunfo del Millonario" no dice "fútbol" ni "River". Con la bajada (`description`) y las categorías (`category`) hay más texto para decidir si una nota encaja con un pedido o un gusto, y Claude tiene más contexto para redactar.

## Qué tiene que hacer
1. En `micafe/fuentes/noticias.py`, cada candidata suma dos campos:
   - `bajada`: sale de `<description>`, sin etiquetas HTML y con las entidades resueltas, recortada a `config.MAXIMO_BAJADA = 300` caracteres (cortando en un límite de palabra y agregando "…" si se recortó).
   - `categorias`: lista de textos de los `<category>` del ítem, sin vacíos ni repetidos (comparando sin mayúsculas), como máximo `config.MAXIMO_CATEGORIAS = 5`.
2. Limpiar HTML con `html.parser.HTMLParser` y `html.unescape` de la librería estándar (sin dependencias nuevas). Se descartan `<script>` y `<style>`; los espacios y saltos de línea se colapsan en uno solo.
3. Si el ítem no tiene `description` (o queda vacía tras limpiarla), `bajada` queda en `""` y la nota **no se descarta**. Sin `category`, `categorias` es `[]`.
4. `micafe/modelos.py`: los tipos `Nota` y `NotaDeFeed` suman `bajada: str` y `categorias: list[str]` (con valor por defecto para que el código viejo y los resúmenes ya guardados sigan leyéndose).
5. `armar_pedido` en `micafe/dominio/resumen.py` agrega la bajada en una línea aparte, debajo del título de cada candidata, solo si no está vacía. Las categorías se pueden mostrar en la misma línea de datos de la nota; el pedido sigue siendo texto plano y la bajada se trata como dato, no como instrucción (el pedido avisa que ese texto viene de afuera).
6. `corrector.verificar_con_modelo` (dominio) también recibe la bajada de cada candidata para chequear que lo escrito se apoye en "título y bajada". Actualizar `.claude/skills/corrector/SKILL.md` para que diga "título y bajada" donde hoy dice solo "título".
7. Logging: el log sigue sin títulos ni bajadas (solo cantidades y nombres de medios).
8. Fixtures de `tests/fixtures/` con `description` (con HTML, entidades y sin ellas) y `category`, y al menos un ítem sin ninguno de los dos.
9. La página sigue mostrando como hoy las candidatas (título y link); mostrar la bajada queda para otra spec si se pide.

## Fuera de alcance
Usar la bajada para puntuar (spec 39); mostrarla en la página; leer `content:encoded`, imágenes u otros campos; sumar feeds.

## Archivos que toca
- `micafe/fuentes/noticias.py`
- `micafe/config.py` (`MAXIMO_BAJADA`, `MAXIMO_CATEGORIAS`)
- `micafe/modelos.py`
- `micafe/dominio/resumen.py`, `micafe/dominio/corrector.py`
- `.claude/skills/corrector/SKILL.md`
- `tests/fixtures/` (feeds de ejemplo)
- `tests/test_noticias.py`, `tests/test_resumen.py`, `tests/test_corrector.py`

## Criterios de aceptación
- [x] Una nota con `<description><![CDATA[<p>Hola &amp; <b>chau</b></p>]]></description>` queda con `bajada == "Hola & chau"`.
- [x] Una bajada de más de 300 caracteres queda en 300 o menos, con "…" al final.
- [x] Una nota sin `description` entra igual a las candidatas, con `bajada == ""`.
- [x] `categorias` trae los `<category>` sin repetidos ni vacíos, con tope de 5.
- [x] El pedido a Claude incluye la bajada debajo del título y no la incluye si está vacía.
- [x] El corrector con modelo recibe la bajada y la skill del corrector dice "título y bajada".
- [x] El log no contiene títulos ni bajadas (test sobre los registros capturados con `assertLogs`).
- [x] Los resúmenes y candidatas guardados antes (sin estos campos) se leen sin error.
- [x] `python3 -m unittest discover -s tests -t .` pasa (278 tests).
- [ ] `python3 servidor.py` arranca y prueba a mano con feeds reales (no verificado acá: sin red ni `claude`).

## Tests (unittest, sin red ni `claude`)
- `test_noticias.py`: limpieza de HTML, entidades (`&amp;`, `&#8220;`), `script`/`style` descartados, recorte a 300, sin `description`, categorías repetidas y tope.
- `test_resumen.py`: `armar_pedido` con una candidata con bajada y otra sin bajada.
- `test_corrector.py`: el prompt de `verificar_con_modelo` (con `claude` simulado) incluye la bajada.
- Un test de logs que comprueba que no se loguea ni título ni bajada.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py` y preparar un resumen con `MICAFE_LOG=DEBUG`: en la consola no aparecen títulos ni bajadas.
3. Con un feed real, comprobar a mano (con una consola de Python y la función de lectura) que una nota trae `bajada` y `categorias` razonables.
4. Preparar un resumen completo: sale como siempre y los datos viejos de `datos/resumenes/` se siguen abriendo.

## Notas de implementación

- `noticias.py`: `limpiar_bajada` (HTMLParser + `html.unescape`, descarta `script`/`style`, colapsa espacios, recorta en límite de palabra con "…"; si no hay espacios corta duro) y `_categorias`. `obtener` las devuelve en cada nota (`bajada`, `categorias`).
- `modelos.py`: `Nota` y `NotaDeFeed` suman los campos como `NotRequired`; el código usa `.get` para que los datos viejos se lean sin error.
- `armar_pedido`: la línea de la nota suma ` Categorías: ...` y, debajo, `  Bajada: ...` solo si hay; se agregó una frase que avisa que títulos, bajadas y categorías son datos. El corrector con modelo recibe la bajada; el texto del chequeo verificado pasó a "título, bajada y medio". La skill del corrector dice "título y bajada".
- Decisión (pregunta abierta 8 del README): no se descartan bajadas iguales al título; se mide con feeds reales.
- El fixture nuevo es `tests/fixtures/rss_bajada.xml` (no se tocó `rss.xml` para no alterar otros tests). El log ya no tenía títulos; un test lo comprueba.
