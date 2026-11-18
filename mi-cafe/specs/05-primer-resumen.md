# 05 - Primer resumen con Claude

**Estado:** hecha

## Depende de
03-indicadores, 04-noticias

## Para qué
Comprobar que el servidor puede llamar a Claude con `claude -p` y que devuelve un resumen corto con links, siguiendo una skill simple.

## Qué tiene que hacer
1. Crear una skill simple en `.claude/skills/` (por ejemplo `resumen-basico/SKILL.md`): 1 o 2 frases por nota, siempre con link, en español rioplatense.
2. El servidor arma el pedido con las notas de ayer (spec 04) y llama a `claude -p` (usa el plan del usuario, sin API key propia).
3. Los indicadores NO se le pasan para que los redacte: los pone el servidor tal cual salen de la spec 03. Claude no escribe ningún número.
4. Devolver el resumen al navegador y mostrarlo en `index.html`.
5. Timeout de 5 minutos para `claude -p`; si se pasa o falla, devolver un error claro.
6. Mientras espera, la página muestra "preparando…".

## Fuera de alcance
Reglas completas de la skill (spec 06), corrector (spec 07), guardado del resumen (spec 08), gustos, caja de preguntas.

## Archivos que toca
- `servidor.py`
- `index.html`
- `.claude/skills/resumen-basico/SKILL.md` (nuevo)

## Criterios de aceptación
- [ ] Un botón dispara el resumen y aparece "preparando…" mientras tarda. (No comprobado en navegador: el JS tiene sintaxis válida y el endpoint responde, pero no vi el botón en pantalla.)
- [x] El resumen es corto y cada nota tiene su link.
- [x] Los links del resumen están entre las notas que se le pasaron (no inventa links).
- [x] No hay cifras de indicadores escritas por el modelo.
- [ ] Si `claude -p` falla o tarda de más, la página muestra un error y sigue usable. (Del lado del servidor sí: error claro en JSON y el servidor sigue atendiendo. Falta ver el mensaje en la página.)
- [x] Las instrucciones viven en la skill, no hardcodeadas en Python.

## Cómo probarlo
1. Tocar el botón y esperar el resumen.
2. Verificar a mano que los links corresponden a las notas de la spec 04.
3. Renombrar temporalmente el comando `claude` para simular el fallo y ver el error.

## Notas de implementación

**Qué se hizo**
- `.claude/skills/resumen-basico/SKILL.md`: la skill con las instrucciones (1 o 2 frases por nota, link de la lista, español rioplatense, sin cifras de indicadores, sin inventar). Se lee tal cual y se pasa a `claude -p` como parte del pedido.
- `resumen.py` (nuevo): arma el pedido con las notas de ayer y llama a `claude -p --tools "" --no-session-persistence` desde la carpeta del proyecto, con timeout de 5 minutos (decisión 13). Levanta `ErrorResumen` con mensaje y código HTTP si no hay notas (422), si no está `claude` en el PATH, si falla (502), si se pasa del timeout (504) o si devuelve texto vacío.
- `servidor.py`: ruta nueva `POST /api/resumen`. Trae las notas (spec 04) y los indicadores (spec 03), llama a `resumen.generar` y devuelve `{ok, indicadores, generado_en, texto}`. Los indicadores van del servidor a la página tal cual; Claude no los recibe.
- `index.html`: sección "Resumen de ayer" con botón "Preparar resumen", "preparando…" mientras espera, bloque de indicadores (reusa `dibujarIndicador`) y el texto de Claude como párrafos (con `textContent`, sin HTML del modelo).

**Decisión tomada: servidor con hilos.** `HTTPServer` atiende de a un pedido, así que una espera de hasta 5 minutos dejaba la página colgada. Pasé a `ThreadingHTTPServer` (también de la librería estándar). Es el único cambio que va más allá de lo literal de la spec, y se hizo para cumplir "la página sigue usable".

**Pruebas hechas (en puertos temporales; el 8000 no se tocó)**
- Resumen real con `claude -p` en el puerto 8123: HTTP 200, 12 notas, las 12 con link. Todos los links del texto están entre los links de `/api/noticias`. Fuera de los links no quedó ninguna cifra.
- `claude` fuera del PATH (puerto 8124): HTTP 502 con "No se encontró el comando `claude`…". No se renombró el binario real: se usó un PATH sin él.
- `claude` que sale con error (puerto 8126, con un `claude` falso en una carpeta temporal): HTTP 502 con el código y el stderr.
- Timeout forzado a 3 s (puerto 8125): HTTP 504 con mensaje claro. Durante la espera, `GET /` respondió en 3 ms y `GET /api/indicadores` en 1,3 s: la página sigue usable.
- `node --check` sobre el JS de `index.html`: sin errores de sintaxis.

**Pendiente de verificar a mano**
- Ver en el navegador el botón, el "preparando…" y cómo se muestra el error.
- Repetir la prueba de "claude no disponible" desde el navegador (criterio 5).

**A tener en cuenta**
- El texto de Claude puede traer subtítulos de sección ("Política", "Economía"): la skill pide agrupar por sección. Las reglas de formato finales son de la spec 06.
- No se valida en código que los links existan en la lista: hoy se verificó a mano y en la spec 07 entra el corrector.
- Si no hay notas de ayer, no se llama a Claude: se devuelve 422 con aviso.
- El resumen no se guarda en disco (eso es la spec 08).

