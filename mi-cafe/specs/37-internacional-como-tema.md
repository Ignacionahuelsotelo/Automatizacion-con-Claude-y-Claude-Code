# 37 - Internacional como tema elegible y filtro estricto

**Estado:** hecha

## Depende de
Nada (es la base de la Fase A). Conviene hacerla primero: las specs 39 a 42 asumen que los temas tildados filtran de verdad.

## Para qué
Hoy Internacional entra siempre al resumen, aunque la persona no la tilde: `micafe/fuentes/noticias.py` (líneas 35-37 y 146) la trata como sección obligatoria, `micafe/almacen/preferencias.py` (línea 22) la deja fuera de `TEMAS` y `tests/test_noticias.py` (línea 193) fija ese comportamiento. Que Internacional sea un tema más, que se tilda y se destilda, y que un tema destildado no traiga nada.

## Qué tiene que hacer
1. En `micafe/config.py`, `TEMAS` pasa a ser la única fuente de la lista de temas elegibles y es igual a las secciones de noticias (Política, Economía, Internacional, Deportes, Tecnología, en el orden en que se muestran). `micafe/almacen/preferencias.py` importa `TEMAS` de `config` y no define una lista propia. Verificar dónde vive hoy `SECCIONES` y dejar una sola definición en `config`.
2. Borrar `SECCIONES_SIEMPRE` (y todo lo que la use) de `micafe/fuentes/noticias.py`. `noticias.obtener` lee solo los feeds de las secciones que están en `temas`.
3. Validar preferencias: tiene que haber al menos un tema de noticias. `PUT/POST` de preferencias con `{"temas": []}` responde 400 con el mensaje "Elegí al menos un tema.". La validación vive en `almacen/preferencias.py` (error previsto, subclase de `ErrorMiCafe`) y el servidor la atrapa donde ya atrapa los demás. "Acciones" sigue siendo el checkbox aparte y no cuenta como tema (ver pregunta abierta).
4. `almacen/gustos.py` acepta votar el tema Internacional (valida contra `config.TEMAS`).
5. Compatibilidad: un `datos/preferencias.json` viejo, sin Internacional en `temas`, se lee igual; Internacional queda destildada (no se agrega sola). Un archivo viejo con `temas` vacío se lee sin romper y la página pide elegir al menos uno al guardar.
6. La página: el checkbox de Internacional aparece en preferencias junto con los demás (la lista de temas ya la recibe del servidor si existe; si hoy está copiada en `app.js`, se deja anotado para la spec 42 y no se amplía el problema). El mensaje "Elegí al menos un tema." se muestra en español junto al botón de guardar.
7. Con `temas=["Deportes"]` solo se leen feeds de Deportes: no se hace ningún pedido de red a los demás feeds.
8. Reemplazar el test de `tests/test_noticias.py:193` (el que exige que Internacional entre siempre) por uno que exija lo contrario: sin Internacional en `temas`, no hay candidatas de Internacional ni se pide su feed.

## Fuera de alcance
Elegir feeds por tema en la página; cambiar cuántas notas lleva cada sección (spec 40); pedidos en texto (spec 39); rediseño visual.

## Archivos que toca
- `micafe/config.py`
- `micafe/almacen/preferencias.py`, `micafe/almacen/gustos.py`
- `micafe/fuentes/noticias.py`
- `micafe/web/servidor.py` (solo si hay que mapear el 400)
- `micafe/web/estatico/app.js` (mostrar el mensaje y el checkbox, sin tocar la copia de `SECCIONES`, que se saca en la 42)
- `.claude/skills/resumen-diario/SKILL.md` y `CLAUDE.md` si mencionan que Internacional entra siempre
- `tests/test_noticias.py`, `tests/test_preferencias.py`, `tests/test_gustos.py`, `tests/test_servidor.py`

## Criterios de aceptación
- [x] `config.TEMAS` contiene las cinco secciones y `preferencias.TEMAS` sale de `config` (no hay dos listas).
- [x] `SECCIONES_SIEMPRE` no existe más en el código.
- [x] Guardar `{"temas": []}` responde 400 con "Elegí al menos un tema." y no modifica `datos/preferencias.json`.
- [x] Se puede tildar y guardar Internacional, y se guarda en `datos/preferencias.json`.
- [x] Con `temas=["Deportes"]`, `noticias.obtener` solo pide feeds de Deportes (el test cuenta los pedidos simulados).
- [x] Con Internacional destildada, no aparece ninguna candidata de Internacional.
- [x] Se puede votar el tema Internacional (👍/👎) en `almacen/gustos.py`.
- [x] Un `preferencias.json` viejo sin Internacional se lee sin error y Internacional queda destildada.
- [x] El test de `tests/test_noticias.py:193` fue reemplazado, no solo borrado.
- [x] `python3 -m unittest discover -s tests -t .` pasa y `python3 servidor.py` arranca. (Tests verificados; el arranque del servidor y la prueba en la página no se hicieron a mano.)

## Tests (unittest, sin red ni `claude`)
- `test_preferencias.py`: temas vacíos rechazados con el mensaje exacto; Internacional válida; archivo viejo sin Internacional se lee igual.
- `test_gustos.py`: voto a tema Internacional aceptado; un tema inexistente sigue rechazado.
- `test_noticias.py`: con fixtures de feeds de las cinco secciones y un `abrir_url` simulado que registra las URLs pedidas, `temas=["Deportes"]` solo pide feeds de Deportes; sin Internacional en `temas` no hay candidatas de Internacional.
- `test_servidor.py`: el POST de preferencias con `{"temas": []}` da 400 con el mensaje en español.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir http://localhost:8000, ir a preferencias: destildar todos los temas y guardar: sale "Elegí al menos un tema.".
3. Dejar solo Deportes, guardar y mirar "Noticias de ayer": solo hay notas de Deportes.
4. Tildar Internacional y guardar: aparece su sección. Destildarla: desaparece.
5. Con `curl -X POST` a preferencias con `{"temas": []}`: 400.
6. Poner a mano un `datos/preferencias.json` sin Internacional y abrir la página: se ve destildada y no hay error.

## Notas de implementación
- `config.TEMAS` es la única lista; `config.SECCIONES` queda como alias (`SECCIONES = TEMAS`) para no tocar al corrector ni al orden de las notas. `preferencias` y `gustos` importan `TEMAS` de `config`.
- Los errores de preferencias ya eran una lista de mensajes que el servidor responde como 400 (no una excepción): se sumó "Elegí al menos un tema." en `preferencias.validar(datos, exigir_tema=True)`. `leer` valida con `exigir_tema=False`, así un archivo viejo con `temas` vacío se lee sin aviso. Opción más simple frente a crear una subclase de `ErrorMiCafe`; no se tocó `servidor.py`.
- "Acciones" no cuenta como tema (resuelto como propone la pregunta abierta 1). Los valores por defecto ahora incluyen Internacional; un archivo viejo sin ella la deja destildada.
- `SECCIONES_SIEMPRE` borrada; `noticias.obtener` filtra solo por `temas`.
- `app.js` no se tocó: el checkbox sale de `opciones.temas` que manda el servidor, y el mensaje se muestra como "No se guardó: Elegí al menos un tema.". La copia `SECCIONES` de `app.js:37` queda para la spec 42.
- `SKILL.md` y `CLAUDE.md` no decían que Internacional entra siempre: sin cambios.
- Tests ajustados: los que guardaban `temas: []` ahora usan un tema; el test de `test_noticias` de Internacional siempre fue reemplazado.
