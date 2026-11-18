# 29 - Chequeo de la conexión con `claude`

**Estado:** hecha

## Depende de
Ninguna (puede hacerse en paralelo con la 28). La 30 la usa como primera etapa.

## Para qué
Hoy, si `claude` no está en el PATH o no funciona, la persona se entera recién después de que el servidor trajo indicadores y noticias (`resumen.generar` chequea `shutil.which` al final). Que la página avise de entrada, con un mensaje claro en español, si Claude está disponible.

## Qué tiene que hacer
1. Agregar en `micafe/dominio/resumen.py` una función `comprobar_claude()` que devuelva si `claude` está disponible y un mensaje en español. Pasos: (a) `shutil.which("claude")`; si no está: "No se encontró el comando `claude`. Revisá que Claude Code esté instalado y en el PATH."; (b) correr `claude --version` con `subprocess.run` (lista de argumentos, sin shell) y un timeout corto; si tarda: "Claude no respondió a tiempo."; si sale con código distinto de 0 o no se puede ejecutar: "`claude` está instalado pero no funciona. Probá abrir Claude Code en la terminal."
2. Estados posibles con su mensaje fijo: `ok`, `no_instalado`, `no_responde`, `con_error`. Nada técnico (rutas, trazas) en el mensaje; el detalle va al log (`logger.warning`/`error`), sin contenido de resúmenes ni preguntas.
3. El chequeo **no** hace una consulta real al modelo (`claude -p "hola"` gasta del plan y tarda). Sí alcanza para saber que el comando existe y arranca. No verifica que la sesión esté iniciada: si el resumen falla por eso, el error ya existente de `ejecutar_claude` lo cuenta (ver pregunta abierta 7 del README).
4. Constante nueva en `micafe/config.py`: `TIMEOUT_CHEQUEO_CLAUDE = 10` (segundos), con comentario.
5. Ruta nueva `GET /api/claude` que responde `200 {"disponible": true|false, "estado": "...", "mensaje": "..."}` (siempre 200: que Claude no esté no es un error del servidor). Se agrega a `RUTAS_JSON` y se documenta en el contrato del encabezado de `app.js`. El servicio expone `servicio.estado_de_claude()`; la capa web no importa `resumen` directamente.
6. En la página: junto al botón "Preparar el de hoy", una línea de estado ("Claude: listo" o el mensaje de error) que se llena al cargar. Si no está disponible, el botón **no** se deshabilita (el chequeo puede dar un falso negativo y se puede instalar sin recargar): al tocarlo se vuelve a comprobar y se muestra el mensaje.
7. `servicio.preparar_resumen` hace el chequeo **antes** de traer noticias e indicadores; si falla, levanta `ErrorResumen` con el mismo mensaje (código 503) sin haber consultado ninguna fuente.
8. Al arrancar el servidor, loguear un `warning` si `claude` no está disponible (el servidor igual arranca).

## Fuera de alcance
Verificar la sesión o el plan de Claude; reintentos automáticos; instalar Claude Code; la pantalla de carga con etapas (spec 30).

## Archivos que toca
- `micafe/dominio/resumen.py`
- `micafe/dominio/servicio.py`
- `micafe/config.py`
- `micafe/web/servidor.py`
- `micafe/web/estatico/index.html`, `micafe/web/estatico/app.js`
- `tests/test_resumen.py`, `tests/test_servicio.py`, `tests/test_servidor.py`

## Criterios de aceptación
- [x] Con `claude` fuera del PATH, `GET /api/claude` da `disponible: false` y el mensaje "No se encontró el comando `claude`…".
- [x] Con `claude --version` que tarda más que el timeout, el mensaje es "Claude no respondió a tiempo.".
- [x] Con `claude --version` que falla (código distinto de 0 o `OSError`), el mensaje es "`claude` está instalado pero no funciona…".
- [ ] Con `claude` funcionando, `disponible: true` y la página dice "Claude: listo".
- [x] `preparar_resumen` con Claude no disponible falla antes de llamar a las fuentes de indicadores y noticias (un test lo verifica con fuentes simuladas que fallarían si se llamaran).
- [ ] Ningún mensaje que llega a la página tiene rutas, trazas ni texto en inglés técnico.
- [x] Todos los tests nuevos usan `unittest`, `mock` y no ejecutan `claude` real ni usan red.
- [x] `python3 -m unittest discover -s tests -t .` pasa.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py` con `claude` en el PATH: abrir la página y ver "Claude: listo". `curl http://localhost:8000/api/claude` devuelve `disponible: true`.
3. Probar sin `claude`: arrancar el servidor con un PATH sin Claude (por ejemplo `PATH=/usr/bin:/bin /usr/bin/python3 servidor.py`) y recargar: la página muestra el mensaje en español; tocar "Preparar el de hoy" repite el mensaje enseguida, sin demorarse en traer noticias.
4. Mirar la consola del servidor: aparece el aviso al arrancar sin `claude`, sin trazas largas.

## Notas de implementación
- `resumen.comprobar_claude()` devuelve `{disponible, estado, mensaje}`; los mensajes fijos están en `MENSAJES_CLAUDE`. `TIMEOUT_CHEQUEO_CLAUDE = 10` en `config.py`.
- `servicio.estado_de_claude()` y `GET /api/claude` (siempre 200). `preparar_resumen` chequea primero y levanta `ErrorResumen` con código 503.
- Al arrancar, `main()` loguea un warning si Claude no está disponible.
- Página: línea `#estado-claude` junto al botón; se llena al cargar y al tocar el botón (que nunca se deshabilita por el chequeo). Si no está, no se pide el resumen.
- Sin verificar a mano: "Claude: listo" en la página, el arranque sin `claude` en el PATH y que no haya texto técnico en la página real (solo hay tests de backend).
