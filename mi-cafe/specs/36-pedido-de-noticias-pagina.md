# 36 - Pedido de noticias en texto: página

**Estado:** hecha

## Depende de
35-pedido-de-noticias-backend y 30-progreso-en-tiempo-real (la página usa el estado de carga con etapas).

## Para qué
Un lugar en la página donde la persona escribe qué noticias quiere ver hoy, y que "Preparar el de hoy" use ese texto con la pantalla de carga de la spec 30.

## Qué tiene que hacer
1. En "Resumen de hoy" (`index.html`), arriba del botón, un `<label>` y un `<textarea id="pedido-noticias" maxlength="500">` ("¿Qué noticias querés ver hoy? Es opcional.") con un contador de caracteres ("0/500", `aria-live="polite"`). El límite es el de `MAXIMO_PEDIDO_USUARIO` (500): el front lo repite como constante visible, pero la validación que vale es la del servidor.
2. "Preparar el de hoy" manda `POST /api/resumen` con `{"pedido": texto}` (el texto sin espacios de los costados; vacío = no se manda el campo). Los errores 400 del servidor se muestran en español junto al botón, sin iniciar el seguimiento.
3. Mientras el armado está en curso (spec 30), el textarea queda `disabled` junto con el botón. Si la página se recarga en medio del armado, queda deshabilitado también.
4. Al terminar bien, el textarea se vacía. Si falla, se conserva el texto para reintentar sin volver a escribir.
5. El resumen mostrado indica el pedido con el que se armó, en la cabecera del resumen: «Pedido de hoy: "…"», dibujado con `textContent` (nunca `innerHTML`). Sale del campo `pedido` de `GET /api/resumen`; si no hay, no se muestra nada.
6. Mensajes en español para los errores del pedido: "El pedido es muy largo (máximo 500 caracteres)." y "El pedido tiene que ser un texto." (los manda el servidor); sin conexión: el mensaje de siempre.
7. Actualizar el contrato del encabezado de `app.js`, el `CLAUDE.md` (flujo: el pedido opcional) y el `README.md` del proyecto si describen el flujo.
8. Accesibilidad como la spec 25: etiqueta asociada, foco visible, se usa con teclado, el contador anuncia sin molestar.

## Fuera de alcance
Chat con varios mensajes o respuestas de Claude en pantalla; guardar pedidos anteriores o autocompletar; cambiar fuentes o temas según el pedido; rediseño visual.

## Archivos que toca
- `micafe/web/estatico/index.html`, `app.js`, `estilos.css`
- `CLAUDE.md`, `README.md` (flujo)
- Sin cambios de backend (los hizo la spec 35)

## Criterios de aceptación
- [x] Hay un cuadro de texto con etiqueta y contador, y no deja escribir más de 500 caracteres.
- [x] Sin texto, "Preparar el de hoy" anda como antes (no manda `pedido`).
- [x] Con texto, el POST lleva `pedido` y el resumen que se guarda lo tiene.
- [ ] El cuadro y el botón se deshabilitan durante el armado y se habilitan al terminar o fallar; tras recargar en medio del armado siguen deshabilitados.
- [ ] Tras un error el texto se conserva; tras un éxito se vacía.
- [x] El pedido se ve en la cabecera del resumen, escapado (un pedido con `<b>hola</b>` se ve como texto).
- [x] Un pedido demasiado largo (pegado desde afuera, salteando `maxlength`, o con `curl`) muestra el error en español del servidor.
- [x] La consola del navegador no muestra errores.
- [x] `python3 -m unittest discover -s tests -t .` sigue pasando.

## Cómo probarlo
Manual (y, si está instalado el entorno opcional de la spec 26, un caso en `tests/e2e/` con el servidor y un `claude` simulado, sin tocar `datos/` reales):
1. `python3 servidor.py`, abrir http://localhost:8000.
2. Escribir "más economía y deportes" y tocar "Preparar el de hoy": se ven las etapas, el cuadro y el botón están deshabilitados, y al final el resumen muestra «Pedido de hoy: "más economía y deportes"».
3. Dejar el cuadro vacío y preparar de nuevo: anda como siempre y no muestra "Pedido de hoy".
4. Escribir `<b>prueba</b> <script>alert(1)</script>`: se muestra como texto y no ejecuta nada.
5. Escribir 500 caracteres y ver el contador "500/500"; con `curl` mandar 501 y ver el error en español.
6. Provocar un fallo (sin `claude` en el PATH, spec 29): el mensaje sale en español y el texto del cuadro queda.
7. Revisar `datos/resumenes/AAAA-MM-DD.json` y comprobar que tiene `pedido`.

## Notas de implementación

- `index.html`: bloque `.pedido` con `<label for>`, `<textarea id="pedido-noticias" maxlength="500">` y contador `#contador-pedido` (`aria-live="polite"`). `app.js`: constante `MAXIMO_PEDIDO`, el POST manda `{pedido}` con el texto recortado (sin cuerpo si está vacío), `ocuparResumen` deshabilita también el cuadro (cubre la recarga en medio del armado, vía `retomarResumen`), se vacía solo al terminar bien, y la cabecera suma «Pedido de hoy: "…"» con nodos de texto (nunca `innerHTML`). Contrato del encabezado actualizado; también CLAUDE.md y README.md.
- Aviso de "pedido sin notas aplicables" (decisión 12): NO se hizo. El backend no sabe si el pedido tuvo notas aplicables (lo decide el modelo al redactar) y no hay dato para deducirlo; haría falta una spec de backend (por ejemplo, que la skill devuelva una marca verificable).
- e2e: 4 casos nuevos en `tests/e2e/e2e_pagina.py` (contador y error 400 en español con valor de 501 caracteres, cabecera escapada, POST sin y con `pedido`, cuadro deshabilitado durante el armado y vaciado al éxito). Los dos que arman un resumen van al final porque reemplazan el guardado.
- Sin verificar: recarga en medio del armado (el `claude` simulado responde al instante) y conservación del texto tras un fallo del armado (el simulado no falla); ambos salen del código (`ocuparResumen`, no se vacía en `mostrarResultado` de fallo) pero sin prueba. Tampoco se probó con `claude` real ni con `python3 servidor.py` en el puerto 8000.
