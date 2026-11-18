# 10 - Caja de preguntas

**Estado:** hecha

## Depende de
08-pagina-completa

## Para qué
Poder preguntarle a Claude sobre una noticia y que responda solo con lo que dice esa nota.

## Qué tiene que hacer
1. Una caja de preguntas en la página, asociada a una nota elegida tocándola en el resumen.
2. El servidor manda a `claude -p` la pregunta y el contenido de esa nota, con una skill que fija las reglas de respuesta.
3. La respuesta se apoya solo en esa nota; si la nota no alcanza, responde que no lo dice en vez de inventar.
4. Ningún número en la respuesta que no esté en la nota; nada de datos de afuera.
5. Estado de "pensando…" y manejo de timeout/errores como en la spec 05.
6. La respuesta se muestra junto a la nota, con el link a la nota original.

## Fuera de alcance
Conversaciones con memoria de varios turnos, preguntas generales sin nota, buscar en internet.

## Archivos que toca
- `index.html`
- `servidor.py`
- `.claude/skills/` (skill de respuesta a preguntas)

## Criterios de aceptación
- [x] Se puede elegir una nota y hacerle una pregunta. (Chrome headless, con `claude` falso.)
- [ ] La respuesta se sostiene en el texto de esa nota (verificable leyéndola). (No comprobado: requiere el `claude` real.)
- [ ] Si la pregunta no se puede responder con la nota, lo dice. (No comprobado con el modelo real: el falso devuelve la frase fija y eso prueba solo el camino del código.)
- [x] Se ve "pensando…" y, ante un fallo, un error claro sin romper la página. (Chrome headless: "Pensando…" durante el pedido; con `claude` que falla, el error sale en la página y el botón vuelve a quedar habilitado.)
- [x] La respuesta muestra el link de la nota. (Chrome headless y API.)

## Cómo probarlo
1. Preguntar algo que la nota responde y comparar con el texto.
2. Preguntar algo que la nota no dice y comprobar que lo reconoce.
3. Simular la caída de `claude -p` y ver el error.

## Notas de implementación

**Qué se hizo**
- `caja.py` (módulo nuevo, como pidió la decisión 12 del README): `responder(datos)` valida el pedido (fecha del resumen `AAAA-MM-DD`, link de la nota y pregunta), busca la nota en `datos/resumenes/AAAA-MM-DD.json` por su link y arma el pedido con la skill, el bloque de la nota tal como está en el resumen y la pregunta. Llama a `claude -p` con `resumen.ejecutar_claude`, o sea el mismo mecanismo y el mismo timeout de 5 minutos que el resumen.
- `.claude/skills/preguntas-nota/SKILL.md` (nueva): reglas de respuesta. Solo lo que dice la nota; si no lo dice, responde exactamente "La nota no dice eso."; ninguna cifra que no esté en la nota; texto plano, dos o tres frases, sin links (la página muestra el link).
- `servidor.py`: ruta nueva `POST /api/preguntas`. Responde `{ok, respuesta, link}`; errores con `{ok: false, errores}`: 400 pedido inválido, 404 la nota no está en el resumen de esa fecha, 502 `claude` falla o trae cifras que no están en la nota, 504 timeout. El docstring menciona la ruta.
- `index.html`: el título de cada nota del resumen es un botón (`button.titulo-nota`) que la elige. Debajo del resumen aparece la caja: nombre de la nota elegida, campo de pregunta (máximo 500 caracteres), botón "Preguntar", estado ("Pensando… Claude está leyendo la nota…"), y la respuesta con su link. Al preparar o cargar un resumen, la caja se oculta.

**Decisiones**
- **Qué es "el contenido de la nota".** El feed solo trae título, medio, fecha y link. El cuerpo de 40 a 50 palabras lo redacta Claude dentro del resumen. Por eso, la "nota" que recibe Claude es el bloque del resumen (título, cuerpo, "Por qué importa", medio y fecha, link) y sus fuentes. No se bajan las páginas de los medios: sería una función nueva fuera de la spec. Si se quiere que responda con el texto completo del artículo, hay que decidirlo aparte (bajar la página, y eso cambia la ventana de fuentes).
- **El servidor no confía en el texto que manda la página.** Busca la nota por fecha y link dentro del resumen guardado. Así la respuesta siempre sale de lo que está guardado.
- **Cifras.** Como "ningún número lo escribe el modelo", el código compara las cifras de la respuesta con las de la nota (sin puntos ni comas: `1.234,50` y `123450` cuentan igual). Si la respuesta trae una cifra que no está en la nota, no se muestra y se devuelve un 502 con aviso. No hay reintento.
- **Límite de 500 caracteres** para la pregunta (en el servidor y en el campo). Es un límite propio para acotar el pedido; no lo pedía la spec.
- **Dónde se ve la respuesta.** La caja va justo debajo del resumen (no al lado de cada nota). La respuesta aparece ahí, con el link de la nota elegida. Es una lectura de "junto a la nota" que conviene confirmar.
- **Una sola nota a la vez.** Elegir otra nota limpia la respuesta anterior. No hay memoria de varios turnos (fuera de alcance).

**Pruebas hechas** (en una copia del proyecto en el scratchpad, en el puerto 8150; el 8000 no se tocó ni se reinició; `datos/` real no se modificó; `claude` fue un script falso en el PATH que arma respuestas según la pregunta y puede fallar, devolver una cifra inventada o demorar)
- API (curl): respuesta válida 200 con el link; pregunta sin respuesta en la nota, frase fija; nota que no está en el resumen 404; fecha inválida (`../x`) 400; pregunta vacía 400; JSON inválido 400; cuerpo que es lista 400; pregunta de 501 caracteres 400; GET `/api/preguntas` 404. Solo los dos pedidos válidos llegaron a `claude`.
- Errores de `claude`: cifra inventada → 502 con el aviso; código de salida 3 → 502 con el mensaje; `claude` fuera del PATH → 502 con el mensaje; timeout (con el límite bajado a 1 segundo solo en la prueba) → 504.
- Pedido a `claude`: lleva la skill sin el encabezado, el bloque de la nota elegida con su link, la regla de la frase fija y la pregunta. No lleva la otra nota del resumen.
- Navegador (Chrome headless por DevTools en el puerto 9333, sin instalar nada): 2 botones de nota; la caja está oculta hasta elegir; elegir una nota la marca (`aria-pressed`) y muestra su nombre; pregunta vacía → "Escribí una pregunta."; durante el pedido, "Pensando…" y el botón deshabilitado; respuesta con el texto, el rótulo "Respuesta, según la nota:" y el link; pregunta sin respuesta en la nota → "La nota no dice eso."; elegir otra nota limpia la respuesta. Captura revisada: `/private/tmp/claude-501/-Users-ignaciosotelo-Desktop-Automatizacion-con-Claude-y-Claude-Code-mi-cafe/dc4de262-903c-4346-8b82-e8ae7fc33578/scratchpad/caja-preguntas-10.png`.
- Navegador con `claude` que falla: "No se pudo responder: Claude terminó con error (código 3)…", el botón vuelve a quedar habilitado y las notas siguen en la página.

**Pendiente o no probado**
- No se corrió con el `claude` real (para no gastar el plan). Quedan sin tildar: que la respuesta real se sostenga en la nota, y que el modelo real diga "La nota no dice eso." cuando corresponde. Cómo probarlo 1 y 2 quedan por hacer con el modelo real.
- El servidor del puerto 8000 corre código anterior: para ver la caja hay que reiniciarlo con `python3 servidor.py`. No lo reinicié.
- El mensaje de timeout dice "5 minutos" con el valor real (en la prueba dijo "0 minutos" porque el límite estaba bajado a 1 segundo).
