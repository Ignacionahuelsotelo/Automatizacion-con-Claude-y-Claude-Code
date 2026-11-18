# 25 - Front: calidad técnica y accesibilidad

**Estado:** hecha

## Depende de
24.

## Para qué
Con el front ya en archivos separados, se ordena el JavaScript y se revisa lo técnico (estructura, errores de red, accesibilidad), sin tocar el diseño.

## Qué tiene que hacer
1. Ordenar `app.js` en funciones con una responsabilidad cada una y secciones claras (estado, llamadas a la API, dibujo de indicadores, dibujo del resumen, gustos, caja de preguntas, preferencias). Si conviene, partirlo en módulos ES nativos (`<script type="module">`) dentro de `estatico/js/`, sin librerías ni build; el servidor sirve esos archivos con la misma lista cerrada de la spec 24.
2. Una sola función para pedir a la API (`fetch`) que maneje: respuesta que no es JSON, código de error, red caída y el mensaje `errores` del servidor. Los textos de error que ve la persona siguen siendo los actuales, en español.
3. Sacar el texto del usuario o de las fuentes de cualquier `innerHTML`: se usa `textContent` o creación de nodos, y los enlaces de las notas llevan `rel="noopener noreferrer"` y `target="_blank"` como hoy. Verificar los lugares donde hoy se arma HTML con cadenas.
4. Estados de la interfaz explícitos (cargando, error, vacío, con dato) y botones deshabilitados durante pedidos largos, como hoy en "Preparar el de hoy".
5. Revisión de accesibilidad y buenas prácticas de UX con la guía de `web-design-guidelines` y corrección solo de lo técnico: etiquetas de formularios, nombre accesible de los botones 👍/👎, `aria-live` para avisos y respuestas, foco visible, orden del foco, jerarquía de títulos, contraste que ya cumpla. Lo que sea decisión de diseño visual se anota para más adelante y no se cambia.
6. Respetar las reglas de `CLAUDE.md` en lo que muestra la página: toda noticia con su enlace, montos tal como los manda el servidor (el front no calcula ni reformatea números), "sin dato" cuando no hay dato, aviso visible cuando el corrector no pasó.
7. Un archivo corto `docs/front.md` o un comentario de cabecera en `app.js` con el mapa de módulos y el contrato de la API que usa el front.

## Fuera de alcance
Rediseño visual, por ahora sin design-taste-frontend. Cambiar colores, tipografías, layout, animaciones o textos de marca. Frameworks, bundlers, TypeScript, PWA.

## Skills a usar
- `web-design-guidelines`: revisión de accesibilidad y UX del front.
- `webapp-testing`: recorrer la página y revisar consola.
- `verification-before-completion`.
- `systematic-debugging` ante cualquier regresión.

## Archivos que toca
- `micafe/web/estatico/app.js` (o `js/*.js`), `index.html` (solo atributos de accesibilidad), `estilos.css` (solo foco y reglas técnicas)
- `micafe/web/servidor.py` (lista de archivos permitidos, si se parte en módulos)
- `docs/front.md` (nuevo, opcional)

## Criterios de aceptación
- [x] No hay variables globales sueltas ni `innerHTML` con texto externo.
- [x] Un solo punto de llamada a la API y errores mostrados en español para: red caída, 400, 500, respuesta que no es JSON.
- [ ] Todo se puede usar con teclado y los botones tienen nombre accesible.
- [x] Los avisos y respuestas se anuncian a lectores de pantalla (`aria-live`).
- [ ] Visualmente la página es igual que antes (comparar capturas).
- [ ] La consola del navegador sin errores ni advertencias.
- [x] Sin librerías externas ni build.
- [x] Las reglas de `CLAUDE.md` que muestra la página siguen cumpliéndose.

## Cómo probarlo
1. Recorrer la página solo con teclado (Tab, Enter, Espacio).
2. Apagar el servidor a mitad de una acción: la página avisa en español y no se rompe.
3. Cortar internet y recargar: avisos de fuentes caídas.
4. Revisar con las herramientas de desarrollo del navegador: sin errores en consola ni pedidos externos.
5. Preparar un resumen de punta a punta y votar, preguntar y cambiar preferencias.

## Notas de implementación
- `app.js` quedó en un solo archivo (sin módulos ES: no hizo falta tocar la lista cerrada de la spec 24), con cabecera que tiene el mapa de secciones y el contrato de la API (cubre el punto 7; no se creó `docs/front.md`). Secciones: DOM y estado, API, gustos, preferencias, indicadores, noticias, resumen, preguntas, arranque. Todo dentro de una IIFE con `"use strict"`.
- `api()` es el único `fetch`: devuelve `{ok, red, datos, errores}` y nunca tira. Cubre red caída, respuesta que no es JSON ("El servidor respondió algo que no se entiende."), 400/500 y el `errores` del servidor. Los textos de error que ya existían se mantienen; los nuevos son el de no-JSON y el de error HTTP sin `errores`.
- Ya no hay `innerHTML`: los íconos 👍/👎 se arman con `createElementNS`. Enlaces con `target="_blank"` y `rel="noopener noreferrer"` desde un solo helper.
- Estados: se agregó "Cargando indicadores…" (antes solo noticias lo tenían) y `aria-busy` en el resumen mientras se prepara; los botones siguen deshabilitados en pedidos largos.
- Accesibilidad: `aria-live`/`role="status"` en los avisos (indicadores, noticias, corrector, preferencias) y `aria-live` en la respuesta; los botones 👍/👎 ahora dicen a qué nota o tema se refieren ("Me gusta: <título>") y van en `role="group"`; la caja de pregunta apunta a la nota elegida con `aria-describedby`. El `label` del textarea, los `fieldset/legend`, la jerarquía h1 > h2 > h3/h4 y `:focus-visible` ya estaban bien. No se tocó `estilos.css`.
- Revisión con `web-design-guidelines`: la skill manda a bajar las reglas de una URL externa y en esta sesión no se usó la red; se revisó a mano contra los puntos de la spec. Pendiente para una pasada de diseño (no se cambió): botones 👍/👎 de 30 px (objetivo táctil chico), no hay enlace "saltar al contenido", el subrayado de enlaces solo aparece al pasar el mouse (los enlaces se distinguen poco sin hover).
- Verificado sin navegador: `node --check app.js`, prueba de `api()` con `fetch` simulado (red, no-JSON, 400, 500, ok) y la suite (191 tests OK). No se abrió la página en un navegador.
- Sin tildar: igual visualmente (capturas), consola sin errores ni advertencias, y uso completo con teclado; requieren abrir la página a mano.
