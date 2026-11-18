# 24 - Front en archivos separados (HTML, CSS y JS)

**Estado:** hecha

## Depende de
22. Además necesita que se resuelva en `specs/README.md` la pregunta abierta sobre la regla "un único `index.html`" de `CLAUDE.md` y `docs/plan.md`: separar archivos la cambia. Confirmada el 18/11/2026: se separa en HTML, CSS y JS (sin librerías externas ni build).

## Para qué
`index.html` tiene 574 líneas con estilos y scripts mezclados. Se separa en archivos propios, sin librerías externas, y sin cambiar cómo se ve ni cómo anda.

## Qué tiene que hacer
1. Crear `micafe/web/estatico/` con:
   - `index.html` (solo estructura y textos),
   - `estilos.css` (el contenido del `<style>` actual, tal cual),
   - `app.js` (el contenido del `<script>` actual, tal cual por ahora; el ordenamiento interno es la spec 25).
2. Mover `index.html` de la raíz con `git mv` y referenciar `estilos.css` y `app.js` con rutas relativas. Sin CDN, sin fuentes ni librerías externas, sin build.
3. El servidor sirve esos archivos con una lista cerrada de nombres permitidos (no una ruta libre): `/` devuelve `index.html`, `/estilos.css` y `/app.js` con su `Content-Type` correcto y `charset=utf-8`. Cualquier otra ruta que no sea de la API sigue siendo 404. Sin posibilidad de salirse de la carpeta (`..`, rutas absolutas, enlaces simbólicos).
4. Las rutas del front salen de `micafe/config.py`.
5. Nada visual cambia: mismos colores, tipografías, tamaños, textos y comportamiento. Todo el texto visible sigue en español rioplatense.
6. Actualizar `CLAUDE.md` y `docs/plan.md` (fila 9 de la tabla de piezas) para reflejar que la página son tres archivos estáticos sin librerías externas. Los cambios de esa regla los confirma el usuario según la pregunta abierta.
7. Tests: `/`, `/estilos.css` y `/app.js` responden 200 con el tipo correcto; `/../servidor.py`, `/%2e%2e/config.py` y `/app.js/..` no devuelven archivos del proyecto.

## Fuera de alcance
Rediseño visual, por ahora sin design-taste-frontend. Reordenar o reescribir el JS (25), accesibilidad (25), frameworks, minificación, caché del navegador.

## Skills a usar
- `webapp-testing`: comparar la página antes y después (capturas y consola sin errores).
- `verification-before-completion`.

## Archivos que toca
- `micafe/web/estatico/index.html`, `estilos.css`, `app.js` (nuevos; `index.html` llega por `git mv`)
- `micafe/web/servidor.py` (y `rutas.py` si existe), `micafe/config.py`
- `tests/test_servidor.py`
- `CLAUDE.md`, `docs/plan.md`

## Criterios de aceptación
- [x] La raíz ya no tiene `index.html`.
- [ ] La página se ve y anda igual: indicadores, noticias, preparar resumen, 👍/👎, preguntas, preferencias.
- [ ] La consola del navegador no muestra errores ni pedidos externos.
- [x] Rutas con `..` o fuera de la lista devuelven 404.
- [x] `python3 servidor.py` sigue siendo el comando de arranque.
- [x] La suite pasa.
- [x] Sigue sin librerías ni dependencias externas.

## Cómo probarlo
1. `python3 servidor.py` y abrir http://localhost:8000. Pestaña Red del navegador: solo pedidos a localhost.
2. `curl -i http://localhost:8000/estilos.css` y `/app.js` (tipos correctos); `curl --path-as-is http://localhost:8000/../servidor.py` da 404.
3. Comparar capturas con la versión anterior.
4. `python3 -m unittest discover -s tests -t .`.

## Notas de implementación
- Se crearon `micafe/web/estatico/{index.html,estilos.css,app.js}`; el contenido de `<style>` y `<script>` se copió tal cual (reconstruido, es idéntico byte a byte al `index.html` anterior). El original tenía 727 líneas, no 574.
- `micafe/config.py`: `CARPETA_ESTATICA`, `ARCHIVO_INDEX` (nueva ruta) y `ARCHIVOS_ESTATICOS` (lista cerrada ruta -> archivo y Content-Type). El servidor solo sirve esas tres rutas; todo lo demás es 404, sin armar rutas de disco a partir del pedido.
- No se usó `git mv`: `mi-cafe/` está sin versionar en git, así que se movió con archivos normales.
- Tests nuevos en `tests/test_servidor.py` (tipos y 404 con `..`, `%2e%2e`, `/app.js/..`, etc.) y ajuste en `tests/test_config.py`. Suite: 191 tests OK.
- `CLAUDE.md` y `docs/plan.md` (fila 9) actualizados.
- Sin tildar: "La página se ve y anda igual" y "La consola no muestra errores ni pedidos externos". No se pudo abrir un navegador; solo se comprobó por HTTP y que el HTML/CSS/JS no tienen URLs externas.
