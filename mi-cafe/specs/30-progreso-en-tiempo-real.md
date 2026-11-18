# 30 - Progreso en tiempo real al preparar el resumen

**Estado:** hecha

## Depende de
29-chequeo-claude (la primera etapa es comprobar Claude).

## Para qué
Hoy `POST /api/resumen` es un único pedido que se queda abierto hasta que termina todo (puede llegar a varios minutos, con hasta 3 redacciones y verificaciones de Claude) y la página solo dice "Cargando…". Que la persona vea en qué etapa va (indicadores, noticias, redacción, corrección), que el botón no se pueda tocar mientras corre y que los errores salgan en español.

## Opciones evaluadas (solo librería estándar)
- **Polling (recomendada).** El servidor corre el armado en un hilo y guarda un estado en memoria; la página lo consulta cada 1,5 s con `GET /api/resumen/estado`. Es lo más simple, entra en la estructura actual (`RUTAS_JSON`, una respuesta por pedido), se puede probar con `unittest` y sobrevive a recargar la página (el estado vive en el servidor) y a un corte de red momentáneo.
- **Server-Sent Events (descartada por ahora).** `ThreadingHTTPServer` lo soporta, pero exige una respuesta que queda abierta, `Content-Type: text/event-stream`, manejo de reconexión y de clientes que se van (`BrokenPipeError`), y es más difícil de probar. No aporta nada que el polling a 1,5 s no dé para un proceso que dura minutos.

Confirmar la recomendación en la pregunta abierta 8 del README.

## Qué tiene que hacer
1. Módulo nuevo `micafe/dominio/progreso.py` (sin dependencias de `web`): una clase con candado (`threading.Lock`) que guarda el estado del armado y expone `iniciar()`, `avanzar(etapa, intento=None)`, `terminar(resultado)`, `fallar(errores, extras)` e `instantanea()` (copia del estado para responder). Un solo armado a la vez.
2. Etapas fijas, definidas en `micafe/config.py` (`ETAPAS_RESUMEN`, lista de `(clave, texto)`) y en este orden, que es el real del código: `claude` "Comprobando Claude", `noticias` "Trayendo noticias", `indicadores` "Trayendo indicadores", `redactando` "Redactando con Claude", `corrigiendo` "Corrigiendo", `guardando` "Guardando". Los textos son fijos: no incluyen contenido de notas ni de resúmenes.
3. `servicio.preparar_resumen` recibe un parámetro opcional `avisar: Callable[[str, int | None], None] | None = None` y lo llama al empezar cada etapa. `redactando` e `intento` se marcan en el wrapper `redactar`; `corrigiendo` se marca al volver `redactar` (así cada reintento del corrector, 2 como máximo, vuelve a "Redactando… intento 2 de 3" sin tocar `corrector.revisar`). Sin `avisar`, anda igual que hoy.
4. `POST /api/resumen` pasa a **iniciar** el armado en un hilo (`daemon=True`) y responde enseguida `202 {"ok": true, "estado": {...}}`. Si ya hay uno en curso, responde `409 {"ok": false, "errores": ["Ya se está preparando un resumen. Esperá a que termine."]}`.
5. `GET /api/resumen/estado` responde `200 {"estado": "libre" | "en_curso" | "listo" | "fallo", "etapa": clave, "etapas": [{"clave", "texto", "situacion": "pendiente" | "en_curso" | "hecha"}], "intento": n | null, "inicio": "dd/mm/aaaa hh:mm", "resultado": {"resumen", "avisos"} (solo en "listo"), "errores": [...] y "avisos" (solo en "fallo")}`. El estado "listo" o "fallo" se conserva hasta que arranque otro armado o se reinicie el servidor (pregunta abierta 9).
6. Cualquier excepción del hilo se atrapa en un único lugar: un `ErrorMiCafe` deja `fallo` con su mensaje (y sus `extras`, como los avisos de fuentes), y una excepción no prevista deja `fallo` con "Pasó un error inesperado al preparar el resumen. Mirá la consola del servidor." y la traza en el log (con el comentario que justifique el `except Exception`, como en `servidor.py`). El hilo nunca muere en silencio y el estado nunca queda en "en_curso" para siempre.
7. Front (`app.js`, sección 7 "Resumen"; `index.html` suma una lista `<ol id="etapas-resumen">`): al tocar el botón se hace el POST; mientras el estado es `en_curso` se consulta cada 1,5 s (constante en `app.js`) y se pinta la lista de etapas con `textContent` (hecha / en curso / pendiente) más el texto "Redactando con Claude (intento 2 de 3)" cuando corresponda; el botón queda `disabled` y `aria-busy` en el resumen. Se anuncia por `aria-live="polite"`.
8. Al cargar la página se consulta `GET /api/resumen/estado`: si está `en_curso`, se retoma el seguimiento y el botón arranca deshabilitado (recargar no deja tocar el botón dos veces). Si está `listo` y la persona no lo vio, se muestra el resumen (que sale de `GET /api/resumen`).
9. Cuando llega `listo`, se muestra el resumen, los avisos de fuentes e indicadores (igual que hoy) y se habilita el botón. Cuando llega `fallo`, se muestra "No se pudo preparar el resumen: " + errores, se vuelve a mostrar el último resumen guardado (como hoy) y se habilita el botón.
10. Si el polling falla 3 veces seguidas, se frena y se muestra "Se perdió la conexión con el servidor. Revisá que siga andando y recargá la página." y se habilita el botón.
11. Actualizar el contrato del encabezado de `app.js` y los docstrings de `servidor.py` (el POST de `/api/resumen` ya no devuelve el resumen).

## Fuera de alcance
SSE y WebSocket; cancelar un armado en curso; historial de armados; porcentaje de avance o tiempo estimado; que sobreviva a reiniciar el servidor; la caja de pedido (specs 35 y 36).

## Archivos que toca
- `micafe/dominio/progreso.py` (nuevo)
- `micafe/dominio/servicio.py`
- `micafe/config.py` (`ETAPAS_RESUMEN`)
- `micafe/web/servidor.py`
- `micafe/web/estatico/index.html`, `app.js`, `estilos.css`
- `tests/test_progreso.py` (nuevo), `tests/test_servicio.py`, `tests/test_servidor.py`
- `CLAUDE.md`: la línea del flujo y la de `POST /api/resumen`, si quedaron desactualizadas

## Criterios de aceptación
- [x] `POST /api/resumen` responde 202 en menos de 1 segundo aunque `claude` tarde (test con un `redactar` simulado que espera un `threading.Event`).
- [x] Un segundo POST con un armado en curso da 409 y el mensaje en español.
- [x] `GET /api/resumen/estado` pasa por las etapas en el orden de `ETAPAS_RESUMEN` y termina en "listo" con el resumen guardado.
- [x] Un fallo de Claude, del corrector o del guardado deja "fallo" con el mensaje en español y los avisos de fuentes, y permite iniciar otro armado.
- [x] Un error inesperado en el hilo deja "fallo" (no "en_curso") y queda en el log.
- [x] Con 2 reintentos del corrector, el estado muestra el intento (2 de 3, 3 de 3).
- [ ] En la página el botón se deshabilita al empezar, se ve la etapa actual, y se habilita al terminar o fallar; recargando en medio del armado, sigue deshabilitado y retoma el seguimiento.
- [ ] El texto del resumen, de las notas y del pedido no aparece en el estado ni en el log (solo etapas fijas).
- [x] Los tests viejos de `POST /api/resumen` se actualizaron al contrato nuevo; la suite pasa sin red ni `claude` real.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir la página, tocar "Preparar el de hoy": el botón se deshabilita y la lista de etapas va avanzando (Comprobando Claude, Trayendo noticias, Trayendo indicadores, Redactando con Claude, Corrigiendo, Guardando).
3. Durante la redacción, recargar la página (F5): sigue mostrando la etapa en curso y el botón sigue deshabilitado. Al terminar aparece el resumen.
4. Con `curl -i -X POST http://localhost:8000/api/resumen` dos veces seguidas: el primero da 202 y el segundo 409.
5. Probar un fallo: arrancar con un PATH sin `claude` (spec 29) o apagar la red: la página dice "No se pudo preparar el resumen: …" en español y el botón se habilita.
6. Cortar el servidor en medio de un armado: la página avisa que se perdió la conexión y habilita el botón.

## Notas de implementación
- Nuevo `micafe/dominio/progreso.py` (clase `Progreso` con `threading.Lock`); `servicio.py` guarda una instancia en `progreso_resumen` (los tests la reemplazan) y suma `iniciar_resumen()`, `estado_del_resumen()` y el cuerpo del hilo `_armar_en_hilo` (único `except` de ErrorMiCafe y de `Exception`).
- `preparar_resumen(ahora, avisar)`: marca `claude`, `noticias`, `indicadores`, `redactando` (con el intento) y `corrigiendo` en el wrapper `redactar`, y `guardando`. El chequeo de Claude de la spec 29 es ahora la primera etapa: la página ya no hace un chequeo previo antes del POST (se evita duplicarlo); `GET /api/claude` sigue mostrando el estado junto al botón al cargar. Sin Claude el estado queda en `fallo` con el mensaje de la spec 29 (ya no hay 503 en el POST: el POST responde 202 y el fallo se ve en el estado).
- Se agregó `intentos_max` (3) al estado, para que la página escriba "intento 2 de 3" sin hardcodear el 3.
- Tests: `tests/test_progreso.py`, `EtapasDelResumen` y `ArmadoEnSegundoPlano` en `tests/test_servicio.py`, `ResumenEnSegundoPlano` en `tests/test_servidor.py`. No había tests viejos de `POST /api/resumen`, y el e2e no toca ese botón.
- No verificado: la página en un navegador (criterio 7) ni que el log no tenga texto (el test cubre solo el estado en curso; el código no loguea contenido).
