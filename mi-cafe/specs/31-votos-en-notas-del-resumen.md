# 31 - Votar las notas del resumen de hoy

**Estado:** hecha

## Depende de
Ninguna spec nueva (se apoya en la 09, hecha). Conviene hacerla después de la 28, que toca la misma zona de `app.js`.

## Para qué
Hoy los botones de me gusta / no me gusta solo están en la lista "Noticias de ayer" (spec 09, decisión "Dónde se vota una nota"). Las notas del resumen de hoy, que es lo que la persona lee, no tienen botones. Que se pueda votar ahí también.

## Cómo se identifican las notas (investigación)
- `gustos.py` guarda cada voto con `tipo`, `clave`, `voto`, `votado_en`; en una nota la `clave` es su **link** (`http` o `https`), y se exigen también `titulo` (no vacío), `medio` y `seccion` (strings) cuando `voto` no es null (`validar_voto`). Votar de nuevo la misma clave reemplaza el voto; `voto: null` lo quita.
- En `app.js`, `crearBotonesVoto(tipo, clave, nota, descripcion)` ya sabe crear los botones, y `pintarVotos()` marca todos los `button[data-tipo]` según `votosGuardados`, así que dos botones con el mismo link quedan sincronizados.
- Las notas del resumen son texto plano (`resumen.texto`): `elementosDelResumen` ya detecta el título (primera línea del bloque), la línea "Medio, fecha" (la anterior al link) y el link; la sección es el último encabezado (`SECCIONES`) visto. Pero el front no guarda `titulo`, `medio` ni `seccion` de cada nota, que el servidor exige para el voto.
- Las claves coinciden con las de "Noticias de ayer": votar una nota en una lista la muestra votada en la otra, y a Claude le llega un solo voto por nota.

## Qué tiene que hacer
1. Backend: una función pura en `micafe/dominio/resumen.py` (o `corrector.py`, donde ya está `notas_del_texto`) que, dado el texto del resumen, devuelva la lista de notas `{titulo, medio, seccion, link}` leyendo los encabezados de sección, el título (primera línea), el medio (de la línea "Medio, fecha", cortando en la última coma) y el link (la línea que es solo un link). Si una nota no se puede leer completa (sin link, sin título), no se incluye. El `medio` puede ser `""` si no se pudo leer; no se inventa.
2. `servicio.ultimo_resumen()` y la respuesta de `POST /api/resumen`/estado (spec 30) suman `notas` al resumen que devuelven, calculadas al responder (no se guardan en el archivo: los resúmenes viejos también las tienen y `datos/resumenes/*.json` no cambia de formato). Se documenta en el contrato del encabezado de `app.js`.
3. Front: en cada nota del resumen se muestran los dos botones (reutilizando `crearBotonesVoto("nota", link, nota, titulo)`) en el pie de la nota, después del link. Si el link de un bloque no está entre `resumen.notas`, no se muestran botones (no se votan notas que no se entienden).
4. Después de dibujar el resumen se llama a `pintarVotos()`, para que las notas ya votadas aparezcan marcadas.
5. El mensaje de "Voto guardado." / "Voto quitado." / error de una nota del resumen se muestra junto al resumen (un `<p class="estado" aria-live="polite">` nuevo), no en la sección "Noticias de ayer", que puede quedar fuera de pantalla. `votar` recibe el destino del mensaje como parámetro.
6. Los botones del resumen no interfieren con la caja de preguntas: tocar el título sigue eligiendo la nota; tocar un botón de voto no.
7. Una nota con dos links (temas polémicos: se citan dos fuentes) lleva los botones solo para el primer link (ver pregunta abierta 10 del README).
8. Estilos mínimos en `estilos.css` para el pie de la nota del resumen, con los mismos botones `.voto`.

## Fuera de alcance
Votar el resumen entero o secciones; cambiar cuántos votos se pasan a Claude (30) o cómo los usa la skill; votar notas de resúmenes viejos desde el archivo; rediseño visual.

## Archivos que toca
- `micafe/dominio/resumen.py` o `micafe/dominio/corrector.py`
- `micafe/dominio/servicio.py`
- `micafe/modelos.py` (tipo de `ResumenGuardado` con `notas` opcional)
- `micafe/web/estatico/app.js`, `index.html`, `estilos.css`
- `tests/test_resumen.py` (o `test_corrector.py`), `tests/test_servicio.py`, `tests/test_servidor.py`

## Criterios de aceptación
- [x] Con un texto de resumen de ejemplo (fixture), la función devuelve una nota por bloque con `titulo`, `medio`, `seccion` y `link` correctos, y omite apertura, cierre y bloques sin link.
- [x] `GET /api/resumen` devuelve `notas` calculadas, sin cambiar el archivo guardado.
- [x] Un voto armado con una de esas notas lo acepta `POST /api/gustos` (200) y queda en `gustos.json` con título, medio y sección.
- [ ] En la página, cada nota del resumen muestra me gusta / no me gusta; tocar uno lo marca, tocarlo de nuevo lo quita, y el otro lo cambia.
- [ ] Una nota votada en "Noticias de ayer" aparece marcada en el resumen (y al revés) cuando comparten link.
- [ ] El mensaje del voto aparece junto al resumen.
- [ ] Los botones tienen nombre accesible con el título de la nota (`aria-label`) y se pueden usar con teclado.
- [ ] Todo el texto se inserta con `textContent`; no hay HTML del modelo.
- [x] `python3 -m unittest discover -s tests -t .` pasa.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, preparar o abrir un resumen guardado y votar una nota con me gusta: el botón queda marcado y dice "Voto guardado." junto al resumen.
3. Mirar `datos/gustos.json`: hay una entrada `tipo: "nota"` con el link, título, medio y sección de esa nota.
4. Buscar la misma nota en "Noticias de ayer": está marcada. Quitar el voto desde allá y recargar: en el resumen ya no está marcada.
5. Votar con no me gusta, cambiar a me gusta y quitar: las tres acciones funcionan.
6. Votar con Tab y Enter, sin mouse.
7. Preparar un resumen nuevo con votos hechos: el pedido a Claude sigue llevando los últimos 30 votos (spec 09) sin cambios.

## Notas de implementación
- `corrector.notas_votables(texto)` (pura) lee sección, título, medio (línea anterior al link, cortada en la última coma; `""` si el link va pegado al título o la línea es "Por qué importa:") y link (el primero que es solo un link). Omite apertura, cierre y bloques sin link o sin sección.
- `servicio.ultimo_resumen()` y el resultado de `preparar_resumen` (y por lo tanto `/api/resumen/estado`) suman `notas` con `_con_notas`; el archivo de `datos/resumenes/` no cambia. Tipo `NotaDelResumen` y `ResumenGuardado.notas` (NotRequired) en `modelos.py`.
- Front: `elementosDelResumen` recibe `notas` y agrega, tras el primer link de cada bloque (decisión 10: se vota el primero), un pie con `crearBotonesVoto`; `votar` y `crearBotonesVoto` reciben el `<p id="estado-voto-resumen">` como destino del mensaje. `mostrarResumen` llama a `pintarVotos()`. Los botones no están dentro del título, así que no disparan la elección de nota.
- Sin tildar (no verificados, no hay Playwright ni navegador acá; la sintaxis de `app.js` se chequeó con `node --check`): los criterios de página (botones visibles y alternancia, sincronía con "Noticias de ayer", mensaje junto al resumen, `aria-label` y teclado, `textContent`). Se prueban a mano con "Cómo probarlo". No se sumó caso e2e.
