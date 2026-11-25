# 50 - Pantalla de Preferencias

**Estado:** hecha

## Depende de
49-preferencias-v2-backend y 42-que-se-vea-la-adaptacion (reutiliza "Lo que aprendí" y el botón de reiniciar).

## Para qué
Las preferencias hoy son unos checkboxes dentro de la página principal. Con temas con prioridad, subtemas, medios, palabras e indicadores no entra más ahí. Una pantalla de Preferencias propia, que es una **vista dentro de la misma página** (decisión aprobada), con todo lo que la persona puede decidir y lo que el sistema aprendió de sus 👍/👎.

## Qué tiene que hacer
1. **Vista `#preferencias` dentro de la misma página:** no hay un archivo nuevo, no se toca `ARCHIVOS_ESTATICOS` ni se agrega una ruta al servidor. En `index.html` hay una `<section id="preferencias" hidden>` y la vista del resumen sigue siendo la principal; se alterna con el hash de la URL (`#preferencias`) y con un botón **"Preferencias"** en la cabecera (un `<a href="#preferencias">` o botón). Al abrir la vista el foco va al título de la sección (`tabindex="-1"`); un botón/enlace "Volver al resumen" regresa y devuelve el foco al botón que la abrió. El botón "atrás" del navegador funciona (`hashchange`). Cargar la página con `#preferencias` abre directo esa vista.
2. **Bloques** (cada uno un `<fieldset>`/`<section>` con título; todo sale de `GET /api/preferencias` y `opciones`, sin listas copiadas en `app.js`):
   - **Temas:** una fila por tema con un interruptor (checkbox con rol `switch` o checkbox simple, con etiqueta visible) y un selector de prioridad (alta, normal, baja; deshabilitado si el tema está apagado). Si no queda ningún tema activo, el mensaje "Elegí al menos un tema." junto al botón de guardar.
   - **Subtemas de Deportes:** checkboxes, visibles solo si Deportes está activo. Ninguno tildado significa todos (texto de ayuda en español).
   - **Medios:** dos listas ("Medios que prefiero" y "Medios que no quiero ver") con los medios de `opciones.medios`; un medio no puede estar en las dos (al tildar uno se destilda en la otra, con aviso `role="status"`).
   - **Indicadores visibles:** un checkbox por grupo de `opciones.indicadores` (Dólar, Otros dólares, Riesgo país, Reservas, Tasas, Inflación, Acciones), en el orden del servidor.
   - **Palabras:** dos campos ("Palabras que quiero seguir" y "Palabras que quiero evitar"), cada uno con un input de texto que agrega con `Enter` o con un botón "Agregar", muestra las palabras como lista con un botón "Quitar" accesible, y respeta los topes que llegan en `opciones` (máximo de palabras y de caracteres); al pasarse, mensaje en español en un `role="status"`.
   - **"Lo que aprendí de tus 👍/👎":** lee `GET /api/perfil` y muestra las prioridades aprendidas (etiqueta en español, sin números ni títulos de notas), la fecha del último reinicio si existe y cuántos votos cuentan. Si no hay nada, "Todavía no aprendí nada de tus 👍/👎.". Un botón **"Reiniciar lo aprendido"** pide confirmación (`window.confirm` o diálogo propio accesible, como en la 42) y llama a `POST /api/perfil/reiniciar` con `{"confirmar": true}`; después vuelve a dibujar el bloque. El bloque de "Cómo se armó hoy" de la 42 sigue andando.
3. **Guardar:** un único botón "Guardar" arma el esquema v2 y lo manda a `POST /api/preferencias`. Si responde bien muestra "Guardado." en un `role="status"` (se mantiene visible unos segundos o hasta la próxima edición) y el botón vuelve a su estado; si responde 400 muestra los `errores` en español (uno por línea, junto al campo cuando se pueda) sin perder lo que escribió la persona. Si se cambió algo y se intenta salir de la vista sin guardar, se avisa ("Tenés cambios sin guardar.") con un botón para guardar o descartar (sin `beforeunload` agresivo).
4. **Sin opción de largo del resumen** (decisión aprobada).
5. **Los checkboxes viejos** de la vista principal (temas e indicadores) se **sacan** y el resumen principal muestra un resumen de una línea ("Temas: ... · Indicadores: ...") con un enlace "Cambiar" a `#preferencias`. El mensaje de "Ese tema está destildado en tus preferencias." de la spec 42 con su botón "Ir a preferencias" ahora abre esta vista y enfoca el interruptor de ese tema.
6. **Accesibilidad (como las specs 25 y 42):** todo se usa con teclado y el foco se ve; cada control tiene `<label>`; los grupos tienen `fieldset` y `legend`; los avisos usan `role="status"` (y `role="alert"` para errores); el orden de tabulación sigue el orden visual; los estados (activo, prioridad) no dependen solo del color; objetivos táctiles de al menos 44 px en pantallas chicas.
7. **Seguridad:** todo texto del servidor o de la persona se dibuja con `textContent` o nodos de texto, nunca `innerHTML` (una palabra `<b>x</b>` o un medio con HTML se ven como texto).
8. **Sin librerías, sin build, sin rediseño visual:** se reutilizan los estilos de `estilos.css` y se suman pocas clases (`.vista`, `.fila-tema`, `.lista-palabras`, etc.). Ningún número de indicador aparece en esta pantalla (solo nombres de grupo). El front no copia ni la lista de temas, subtemas, medios o indicadores ni los topes: todo llega de `opciones`.
9. **Pruebas e2e (Playwright, opcionales, en `tests/e2e/e2e_pagina.py`):** actualizar los casos que dependían de los checkboxes viejos y sumar casos: abrir la vista con el botón y con `#preferencias`; apagar un tema; cambiar prioridad; excluir un medio y ver que se destilda de preferidos; agregar y quitar una palabra; pasarse del tope; guardar con éxito ("Guardado."); error 400 mostrado; "Reiniciar lo aprendido" con confirmación (aceptar y cancelar); HTML en una palabra se ve como texto; tabulación completa con teclado; sin errores en la consola; vista principal después de volver.
10. Actualizar el contrato del encabezado de `app.js`, y en la spec 51 `CLAUDE.md` y `README.md`.

## Fuera de alcance
Una página aparte con su propio archivo estático; editar las prioridades aprendidas a mano; historial o gráficos del perfil; temas de color o rediseño; importar y exportar preferencias; opción de largo del resumen.

## Archivos que toca
- `micafe/web/estatico/index.html`, `app.js`, `estilos.css`
- `micafe/web/servidor.py` / `micafe/dominio/servicio.py` solo si `opciones` necesita algún dato que falte (los de la spec 49 deberían alcanzar)
- `tests/e2e/e2e_pagina.py` (y los scripts de `tests/e2e/` que se rompan)
- `tests/test_servidor.py` (el contrato de `opciones`)

## Criterios de aceptación
- [x] El botón "Preferencias" de la cabecera abre la vista `#preferencias` y "Volver al resumen" regresa; el botón "atrás" y recargar con `#preferencias` andan.
- [x] No se tocó `ARCHIVOS_ESTATICOS` ni se agregó ninguna ruta.
- [x] Se ven los seis bloques con los datos que manda el servidor: temas con interruptor y prioridad, subtemas, medios, indicadores, palabras y "Lo que aprendí de tus 👍/👎".
- [x] Cambiar algo y tocar "Guardar" muestra "Guardado."; recargar mantiene lo guardado.
- [x] Un guardado inválido (sin ningún tema, palabra de más de 40 caracteres, más de 20 palabras) muestra el error en español y conserva lo escrito.
- [x] Un medio no puede quedar en preferidos y excluidos a la vez.
- [x] "Reiniciar lo aprendido" pide confirmación y, al confirmar, el bloque queda vacío; al cancelar no pasa nada.
- [x] `grep` en `app.js` no encuentra listas copiadas de temas, medios o indicadores.
- [x] Una palabra `<b>x</b>` se ve como texto.
- [x] Todo se puede usar con teclado, con foco visible, y los avisos son `role="status"`/`"alert"`.
- [x] La consola del navegador no muestra errores y los e2e (si hay `.venv-dev/`) pasan.
- [x] `python3 -m unittest discover -s tests -t .` pasa. (`python3 servidor.py` en el puerto 8000 no se probó: el servidor de los e2e es el mismo código.)

## Tests
- `unittest` (sin red ni `claude`): `test_servidor.py` verifica que `opciones` trae todo lo que la pantalla necesita (`secciones`, `subtemas`, `medios`, `indicadores`, `prioridades`, topes) y que `POST` con lo que arma la pantalla se guarda; el resto de la lógica ya está en las pruebas de la 49.
- e2e opcionales (servidor y `claude` simulados, datos temporales, sin tocar `datos/` reales): los casos de arriba (`tests/e2e/correr_e2e.sh`).

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .` y, si hay `.venv-dev/`, `tests/e2e/correr_e2e.sh`.
2. `python3 servidor.py`, abrir http://localhost:8000 y tocar "Preferencias": se ve la vista y la URL termina en `#preferencias`.
3. Apagar Política, poner Deportes en prioridad alta, excluir un medio, agregar "Boca" a seguir y tocar "Guardar": aparece "Guardado.".
4. Recargar la página: todo sigue igual. Preparar el resumen: no hay notas del medio excluido ni de Política.
5. Votar 👍 varias notas, volver a "Preferencias": "Lo que aprendí" muestra las prioridades; tocar "Reiniciar lo aprendido" y confirmar.
6. Con teclado: tabular por toda la pantalla, activar un interruptor con `Espacio`, agregar una palabra con `Enter`, guardar sin usar el mouse.
7. Mirar la consola del navegador: sin errores.

## Notas de implementación
- **Vista y navegación:** `<section id="preferencias" hidden>` en `index.html`; la vista del resumen quedó envuelta en `#vista-resumen`. Se alterna con `location.hash` y `hashchange`; el foco va al título al abrir y vuelve al enlace que abrió (o al botón "Preferencias" de la cabecera) al salir. No se tocó `ARCHIVOS_ESTATICOS` ni se agregó ninguna ruta.
- **Edición:** `app.js` edita un `borrador` (copia del v2 del servidor) y "Guardar" manda el v2 entero. Las listas de medios, subtemas e indicadores se guardan en el orden de `opciones`, y el chequeo de "cambios sin guardar" compara sin importar ese orden. Lo único fijo en el front es `TEMA_DE_LOS_SUBTEMAS = "Deportes"` (los subtemas solo se ven con ese tema activo); todo lo demás sale de `opciones`.
- **Decisiones simples:** (1) los topes se validan en el front con mensaje en `role="status"` (sin `maxlength`, para poder avisar); el servidor los vuelve a validar. (2) Los errores 400 se muestran todos juntos en un `role="alert"` debajo de "Guardar", no junto a cada campo. (3) "Guardado." se queda hasta la próxima edición (sin temporizador). (4) Cambios sin guardar: al salir (botón o "atrás") se vuelve a la vista con un aviso con "Guardar y salir", "Descartar y salir" y "Seguir editando"; no hay `beforeunload`. (5) Los 👍/👎 de cada tema se mantuvieron en la fila de cada tema. (6) El botón "Guardar" queda siempre habilitado y "Elegí al menos un tema." se muestra al lado sin bloquearlo (el 400 del servidor es el que corta).
- **Panel "Lo que aprendí":** se recarga cada vez que se abre la vista y tras reiniciar (con `window.confirm`). El bloque "Cómo se armó hoy" quedó como estaba.
- **Etiquetas nuevas:** "Palabra que evitás", "Subtema que elegiste" y "Subtema que no elegiste".
- **Sin opción de largo del resumen.** El resumen de una línea de la vista principal muestra solo nombres de temas e indicadores.
- **Tests:** `tests/test_servidor.py` (contrato de lo que arma la pantalla y topes) y diez casos nuevos en `tests/e2e/e2e_pagina.py` (26 casos pasan). `CLAUDE.md` y `README.md` se actualizan en la spec 51.
