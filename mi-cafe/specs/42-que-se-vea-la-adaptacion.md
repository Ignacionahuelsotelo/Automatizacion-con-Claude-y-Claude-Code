# 42 - Que se vea la adaptación

**Estado:** hecha

## Depende de
40-plan-de-secciones y 41-perfil-de-gustos.

## Para qué
Con las specs 37 a 41 el resumen se adapta a los temas, al pedido y a los gustos, pero la persona no lo ve: no sabe si su pedido encontró notas ni por qué hay cinco notas de Economía. Mostrar en la página cómo se armó el resumen de hoy, avisar cuando el pedido no encontró nada y sacar la lista de secciones copiada en el front.

## Qué tiene que hacer
1. **"Noticias de ayer" por puntaje:** la lista de candidatas se ordena por puntaje (el que calculó el servidor, no uno propio del front) y cada nota lleva etiquetas visibles, derivadas de los `motivos`: "Por tu pedido", "Medio que te gusta", "Tema que te gusta". Las etiquetas son texto, no solo color. El endpoint de candidatas devuelve `motivos` por nota y el orden ya aplicado.
2. **Cabecera "Cómo se armó hoy"** en el resumen mostrado, como `<details>` o bloque plegable con teclado: el plan por sección (cantidad de notas de cada una, y si el plan quedó incompleto), cuántas notas encajaron con el pedido y los ajustes por gustos ("Economía y el medio X subieron por tus votos"). Sale de los campos `plan`, `pedido` y `pedido_sin_notas` del resumen guardado y de las prioridades de `GET /api/perfil`. Resúmenes viejos sin `plan` simplemente no muestran el bloque.
3. **Aviso "Tu pedido no encontró notas de ayer":** se muestra cuando `pedido_sin_notas` es verdadero, junto al pedido en la cabecera del resumen y en el resultado de "Preparar el de hoy". Si el pedido habla de un tema que está destildado, el aviso lo dice: "Ese tema está destildado en tus preferencias." con un enlace o botón que lleva a preferencias. Texto en español, sin términos técnicos.
4. **Lista de secciones desde el servidor:** `SECCIONES` deja de estar copiada en `micafe/web/estatico/app.js:37`; llega en `opciones.secciones` (el endpoint de opciones, tomada de `config.TEMAS`). Sin la lista, el front muestra un mensaje de error en español en lugar de adivinar. Con esto Internacional y cualquier tema nuevo aparecen sin tocar el front.
5. Opcional dentro de esta spec: mostrar las prioridades de `GET /api/perfil` y un botón "Reiniciar lo aprendido" que pide confirmación (`confirm` o diálogo propio accesible) y llama a `POST /api/perfil/reiniciar` con `{"confirmar": true}`. Si no entra en esta spec, se anota en las preguntas abiertas del README.
6. **Seguridad y reglas:** todo texto que viene del servidor (pedido, secciones, medios, etiquetas, motivos) se dibuja con `textContent` o nodos de texto, nunca `innerHTML`. La cabecera y las etiquetas no muestran números de indicadores (ni valores ni variaciones): solo cantidades de notas. Se mantienen los formatos y reglas de `CLAUDE.md`.
7. **Accesibilidad (como la spec 25):** el bloque "Cómo se armó hoy" y el aviso se usan con teclado (foco visible, `Enter`/`Espacio`), el aviso tiene `role="status"` y las etiquetas no dependen solo del color.
8. Sin rediseño visual: se reutilizan los estilos existentes de `estilos.css` y se suman pocas clases.
9. Actualizar el contrato del encabezado de `app.js`, `CLAUDE.md` (flujo y endpoints) y `README.md`.

## Fuera de alcance
Cambiar las reglas de selección o del plan; gráficos o historial del perfil; edición manual de las prioridades; rediseño visual; pedir nuevos feeds.

## Archivos que toca
- `micafe/web/estatico/index.html`, `app.js`, `estilos.css`
- `micafe/web/servidor.py` y `micafe/dominio/servicio.py` (`opciones.secciones`, `motivos` y orden en las candidatas)
- `CLAUDE.md`, `README.md`
- `tests/test_servidor.py`; `tests/e2e/e2e_pagina.py` si hay Playwright, y actualizar los casos de `tests/e2e/` que se rompan por los cambios

## Criterios de aceptación
- [x] La lista de "Noticias de ayer" viene ordenada por puntaje y las notas del pedido muestran la etiqueta "Por tu pedido".
- [x] Una nota de un medio con muchos 👍 muestra "Medio que te gusta".
- [x] El resumen muestra "Cómo se armó hoy" con las cantidades por sección y si el plan quedó incompleto.
- [x] Con `pedido_sin_notas` verdadero aparece "Tu pedido no encontró notas de ayer"; si además el tema está destildado, el aviso lo explica.
- [x] `app.js` ya no define `SECCIONES`; las secciones llegan de `opciones.secciones` y se ven las cinco.
- [x] Un pedido o un medio con `<b>x</b>` se ve como texto.
- [x] No aparece ningún número de indicador en la cabecera ni en las etiquetas.
- [x] Se puede abrir y cerrar "Cómo se armó hoy" solo con teclado y el foco se ve.
- [x] Un resumen guardado antes de las specs 40 y 41 (sin `plan`) se muestra sin errores.
- [x] La consola del navegador no muestra errores (los e2e fallan si hay errores de consola).
- [x] `python3 -m unittest discover -s tests -t .` pasa y `python3 servidor.py` arranca; los e2e opcionales, si hay Playwright, pasan.

## Tests (unittest, sin red ni `claude`)
- `test_servidor.py`: `opciones.secciones` coincide con `config.TEMAS`; las candidatas salen ordenadas por puntaje con `motivos`; el resumen guardado expone `plan`, `pedido` y `pedido_sin_notas`; uno viejo sin esos campos responde 200.
- e2e opcionales (`tests/e2e/`, servidor y `claude` simulados, sin tocar `datos/` reales): aviso de pedido sin notas, bloque "Cómo se armó hoy" plegable con teclado, etiqueta "Por tu pedido", pedido con HTML escapado y secciones desde el servidor. Ajustar los casos viejos que dependan de `SECCIONES` en el front.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .` (y los e2e si está `.venv-dev/`).
2. `python3 servidor.py`, abrir http://localhost:8000, escribir "fútbol argentino" y preparar el resumen: en "Noticias de ayer" las de River, Boca y similares van arriba con "Por tu pedido", y "Cómo se armó hoy" muestra el plan.
3. Pedir un tema destildado (por ejemplo "tecnología" sin Tecnología): aparece "Tu pedido no encontró notas de ayer" con la explicación.
4. Votar 👍 varias notas de un medio, recargar y ver "Medio que te gusta".
5. Con teclado: tabular hasta "Cómo se armó hoy", abrir y cerrar con `Enter`.
6. Mirar la consola del navegador: sin errores. Confirmar con `grep SECCIONES micafe/web/estatico/app.js` que no hay copia de la lista.

## Notas de implementación
- `GET /api/noticias` ahora viene ordenado por `seleccion.ordenar_por_puntaje` y cada nota trae `motivos` (sin puntaje). El pedido que cuenta es el del resumen de hoy (si el último guardado es de hoy y trae `pedido`); sin eso solo pesan frescura y perfil. No se corta ni se descarta nada (`elegir_candidatas` sigue siendo solo para Claude).
- Etiquetas en el front: motivo `pedido:...` -> "Por tu pedido"; "medio que te gusta" -> "Medio que te gusta"; "te gustó algo parecido" -> "Tema que te gusta" (simple: no se cruza con las prioridades de sección).
- `opciones.secciones` sale de `config.TEMAS` (servicio). `SECCIONES` se sacó de `app.js`; sin la lista, la página avisa y no dibuja el resumen.
- Aviso de tema destildado: el servidor suma `temas_destildados_pedido` al resumen cuando `pedido_sin_notas` es verdadero (`seleccion.temas_destildados_nombrados`, con `config.TEMA_DE_CLAVE_SINONIMO` para "fútbol" -> Deportes). El aviso (`#aviso-pedido`, `role="status"`) lleva un botón "Ir a preferencias" que da foco a los temas. Se ve también al terminar "Preparar el de hoy" porque usa el mismo `mostrarResumen`.
- "Cómo se armó hoy" es un `<details>`/`<summary>` nativo (teclado y foco gratis): cantidades por sección, plan incompleto, notas que encajaron con el pedido y ajustes por gustos (`GET /api/perfil`, solo secciones y medios, sin términos). Resúmenes sin `plan` no lo muestran.
- Opcional hecho: botón "Reiniciar lo aprendido" con `window.confirm` dentro de ese bloque (por eso un resumen viejo sin plan no lo ofrece). Se resuelve la pregunta abierta 7.
- Tests: `test_servidor.py`, `test_seleccion.py` y 4 casos nuevos en `tests/e2e/e2e_pagina.py` (16 de 16 pasan con `tests/e2e/correr_e2e.sh`).
- No verificado: pasos 2 a 4 de "Cómo probarlo" con el servidor real y `claude`.
