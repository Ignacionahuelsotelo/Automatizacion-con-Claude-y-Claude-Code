# 28 - Bug: la página se rompe al tildar un tema en preferencias

**Estado:** hecha

## Depende de
25-front-calidad-tecnica (el front ya está en `micafe/web/estatico/`). No depende de ninguna spec nueva: va primero.

## Para qué
Que tildar o destildar un checkbox de "Mis preferencias" (temas o indicadores) siempre guarde bien y deje la página andando, aunque se toquen varios seguidos.

## Lo que ya se leyó (investigación inicial, sin reproducir todavía)

Camino de un tilde: `casilla.addEventListener("change", guardarPreferencias)` (app.js) -> `POST /api/preferencias` con `{indicadores, temas}` -> `servicio.guardar_preferencias` -> `preferencias.guardar` -> `json_seguro.escribir`. Si sale bien, el front dispara a la vez `cargarIndicadores()` y `cargarNoticias()` (dos GET que leen `preferencias.json` de nuevo).

No hay una causa confirmada: leyendo el código no se encontró un error que rompa siempre. Candidatas, de más a menos probable:

1. **Escrituras simultáneas al mismo archivo temporal.** `json_seguro.escribir` usa siempre `ruta + ".tmp"`. `gustos.guardar` tiene un candado (`_candado`), pero `preferencias.guardar` no. Dos tildes seguidos hacen dos POST en hilos distintos del servidor: ambos abren `preferencias.json.tmp`, uno hace `os.replace` y al otro le falla (`FileNotFoundError`, un `OSError`). El servicio lo convierte en `ErrorAlmacenamiento` (500) y la página muestra "No se guardó: No se pudo guardar las preferencias...". La misma carrera existe en las copias `indicadores.json` y `acciones.json` (ahí solo se loguea).
2. **Respuestas desordenadas en el front.** `guardarPreferencias` no serializa los pedidos ni descarta respuestas viejas: con tildes rápidos, un `cargarIndicadores()`/`cargarNoticias()` más lento puede pintar el resultado de las preferencias anteriores, y el mensaje "Guardado." puede no corresponder al último tilde.
3. **Indicadores lentos o con error al activar "Acciones".** Tildar "acciones" hace que `GET /api/indicadores` consulte Rava (hasta 8 consultas de 15 s) y data912; la lista queda en "Cargando indicadores…" mucho tiempo y, si algo falla de forma no prevista, aparece "No se pudieron cargar los indicadores.".
4. **Descartada por lectura:** estilos (`estilos.css` no tiene reglas `:checked` ni `:has`), `validar` (acepta listas vacías y cualquier subconjunto de la lista cerrada) y `noticias.obtener` con `temas` vacío (queda solo Internacional).

Hace falta el síntoma exacto: qué se ve cuando "se rompe" y qué dice la consola del navegador y la del servidor (ver pregunta abierta 1 del README).

## Qué tiene que hacer
1. **Reproducir primero**, con el servidor corriendo y la consola del navegador abierta: (a) un tilde por vez en cada checkbox; (b) tres o cuatro tildes muy seguidos; (c) tildar "Acciones"; (d) destildar todos los temas; (e) destildar todos los indicadores. Anotar qué falla, el mensaje de la página, el error de la consola del navegador y la traza de la consola del servidor.
2. **Escribir la causa confirmada** en la sección "Causa encontrada" de esta misma spec (con la línea de código y el paso que la reproduce). Si la causa no es ninguna de las candidatas, reemplazar la lista de arriba por lo que se halló.
3. **Corregir la causa confirmada.** Si resulta ser la candidata 1, la corrección es que `json_seguro.escribir` use un archivo temporal único por escritura (por ejemplo `tempfile.mkstemp` en la misma carpeta, solo librería estándar) o un candado por ruta, de modo que ninguna escritura concurrente falle. Si es la 2, el front serializa los guardados (un guardado a la vez; si se tilda mientras se guarda, se vuelve a guardar al terminar con el estado final) y descarta respuestas de pedidos viejos. Una candidata que no sea la causa no se toca en esta spec: se anota en "Notas" para decidir aparte.
4. **Test de backend con `unittest`** (en `tests/test_servidor.py` y/o `tests/test_almacen.py`, sin red ni `claude`, con carpetas temporales y fuentes simuladas): (a) varios POST concurrentes (por ejemplo 20 en hilos) a `/api/preferencias` con combinaciones distintas dan todos 200 y el archivo final es un JSON válido y una de las combinaciones enviadas; (b) para cada subconjunto de la lista cerrada de temas y de indicadores, `POST /api/preferencias` da 200 y después `GET /api/indicadores` y `GET /api/noticias` dan 200; (c) el test falla con el código anterior a la corrección.
5. Si la causa estuvo en el front, dejar escritos los pasos manuales de abajo como la verificación y, si el entorno de desarrollo de la spec 26 (`tests/e2e/`, Playwright, opcional) está instalado, sumar un caso que tilde varias casillas seguidas y compruebe "Guardado." y la consola sin errores. Sin ese entorno, alcanzan los pasos manuales.

## Causa encontrada
Confirmada la candidata 1 (18/11/2026). `json_seguro.escribir` usaba siempre el mismo temporal, `ruta + ".tmp"`: dos escrituras simultáneas abrían el mismo archivo, la primera hacía `os.replace` y a la segunda le fallaba con `FileNotFoundError` (`os.replace(x.json.tmp, x.json)`), que el servicio convierte en `ErrorAlmacenamiento` (500, "No se guardó...").

Cómo se reproduce: 200 llamadas a `json_seguro.escribir` sobre la misma ruta desde 20 hilos (o 20 POST a `/api/preferencias` desde 8 hilos) fallan en 3 de 3 corridas con el código anterior. No se levantó el navegador: el síntoma de la página ("No se guardó") coincide con ese 500, pero no se vio en pantalla. Las candidatas 2 y 3 no se tocaron (ver Notas).

## Fuera de alcance
Rediseño de las preferencias; agregar o quitar temas e indicadores; cambiar el formato de `preferencias.json`; sumar dependencias de desarrollo nuevas.

## Archivos que toca
- `micafe/almacen/json_seguro.py` y/o `micafe/almacen/preferencias.py` (si la causa es la candidata 1)
- `micafe/web/estatico/app.js` (si la causa es del front, sección 4 "Preferencias")
- `micafe/web/servidor.py` y `micafe/dominio/servicio.py` solo si la causa está ahí
- `tests/test_servidor.py`, `tests/test_almacen.py`, `tests/test_preferencias.py`
- esta spec (sección "Causa encontrada")

## Criterios de aceptación
- [x] La causa está escrita en esta spec, con el paso para reproducirla.
- [x] Hay un test que falla sin la corrección y pasa con ella.
- [x] 20 POST concurrentes a `/api/preferencias` dan 200 y dejan un `preferencias.json` válido.
- [x] Todo subconjunto de temas e indicadores se guarda y deja andar a `GET /api/indicadores` y `GET /api/noticias`.
- [ ] En el navegador, tildar y destildar cada checkbox (también varios seguidos) deja "Guardado." y la lista de noticias e indicadores coherente con lo tildado.
- [ ] La consola del navegador no muestra errores en ninguno de esos pasos.
- [x] `python3 -m unittest discover -s tests -t .` pasa.
- [x] Los mensajes de error que ve la persona siguen en español y sin texto técnico.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir http://localhost:8000 con la consola del navegador abierta (pestaña Consola y Red).
3. Tildar y destildar un tema: debe decir "Guardando…" y después "Guardado.", y la lista de "Noticias de ayer" cambia según los temas.
4. Tildar 4 casillas seguidas, lo más rápido posible: el último mensaje debe ser "Guardado.", sin "No se guardó", y al recargar (F5) las casillas quedan como se dejaron.
5. Tildar y destildar "Acciones": los indicadores se actualizan (o dicen "sin dato" con su aviso) y la página sigue respondiendo.
6. Destildar todos los temas: la lista dice "No hay notas de ayer para los temas elegidos." (queda Internacional si hay notas) y no hay errores en la consola.
7. Revisar que `datos/preferencias.json` sea JSON válido y que no quede `preferencias.json.tmp`.

## Notas de implementación
- Cambio: `json_seguro.escribir` usa `tempfile.mkstemp` en la misma carpeta (temporal único por escritura) y sigue haciendo `os.replace`; la limpieza en caso de error no cambió. Como beneficio, también quedan arregladas las copias `indicadores.json`, `acciones.json`, gustos y resúmenes, que usan la misma función.
- Tests nuevos: `tests/test_almacen.py` (escrituras concurrentes) y `tests/test_servidor.py`, clase `PreferenciasConcurrentes` (20 POST en hilos y todos los subconjuntos de temas e indicadores con GET a indicadores y noticias). Fallan con el código anterior.
- `mkstemp` crea el archivo con permisos 0600 (antes 0644); para datos personales en `datos/` es aceptable.
- No verificado: los criterios de navegador (no se abrió la página; el entorno e2e es opcional). Quedan para la prueba manual de "Cómo probarlo" (pasos 3 a 7). Por eso esos dos criterios siguen sin tildar.
- Candidatas no tocadas, a decidir aparte: 2 (el front no serializa guardados ni descarta respuestas viejas) y 3 (lentitud al activar "Acciones").
