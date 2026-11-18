# 20 - Logging y manejo de errores consistentes

**Estado:** hecha

## Depende de
19.

## Para qué
Hoy los errores técnicos salen con `print("Aviso: ...")` y `traceback.print_exc()` desparramados, y cada módulo resuelve las fallas a su manera (`ErrorResumen` vive en `resumen.py` y lo usa `caja.py`; las fuentes devuelven avisos como texto). Se unifica con `logging` de la librería estándar y una jerarquía de errores chica, sin cambiar lo que ve el usuario.

## Qué tiene que hacer
1. Configurar `logging` una sola vez en el arranque (`micafe/logs.py` o dentro de `web/servidor.py`): salida a la consola del servidor, formato con hora, nivel y módulo, en español. Nivel por defecto INFO, y variable de entorno opcional `MICAFE_LOG` para subir a DEBUG.
2. Cada módulo usa `logger = logging.getLogger(__name__)`. Reemplazar todos los `print` y `traceback.print_exc()` por `logger.warning`, `logger.error` o `logger.exception`. El mensaje "Aviso: ..." que hoy va a la consola se conserva como texto del log.
3. Crear `micafe/errores.py` con una base `ErrorMiCafe` (con `mensaje` en español para mostrar y `codigo` HTTP) y las subclases que hagan falta (por ejemplo `ErrorResumen`, `ErrorFuente`, `ErrorAlmacenamiento`). `ErrorResumen` mantiene su nombre y atributos (`mensaje`, `codigo`) para no romper nada, y se mueve acá.
4. El servidor atrapa `ErrorMiCafe` en un solo lugar y arma la respuesta JSON `{"ok": false, "errores": [...]}` con su código. Lo no previsto sigue dando 500 con el aviso actual ("Pasó un error inesperado en el servidor. Mirá la consola para más detalle.") y la traza va al log.
5. Regla de oro que no cambia: el detalle técnico va al log y a la consola; la página recibe solo mensajes en español sin texto técnico. Nunca se loguea contenido de resúmenes completos ni de preguntas del usuario (solo tamaño o fecha).
6. Reemplazar los `except Exception` demasiado anchos por excepciones concretas, salvo el último recurso del servidor y el hilo que llama a `claude -p`. Cada uno que quede lleva un comentario con el motivo.
7. Una fuente que falla sigue sin tirar la app: se avisa en la página y se sigue con el resto (decisión 3 y spec 12).
8. Tests: que un error de fuente quede en el log (`assertLogs`) y que la respuesta al navegador no incluya traza ni nombres de archivos.

## Fuera de alcance
Archivos de log en disco, rotación, niveles por módulo, métricas, cambiar los textos de aviso que ve el usuario.

## Skills a usar
- `systematic-debugging`: al achicar los `except` anchos, confirmar la causa real de cada falla simulada.
- `verification-before-completion`: provocar cada tipo de falla antes de cerrar.

## Archivos que toca
- `micafe/errores.py`, módulo de logging (nuevos)
- Todos los módulos de `micafe/` que hoy usan `print` o `traceback`
- `tests/*` (los que usan `ErrorResumen`; sumar los de logging)

## Criterios de aceptación
- [x] `grep -rn "print(" micafe/` no devuelve nada (salvo el mensaje de arranque, que sale por el logger o se justifica).
- [x] Los mensajes de error que ve la página son los mismos de antes, en español y sin texto técnico.
- [x] Una falla simulada de cada fuente (DolarApi, ArgentinaDatos, BCRA, Rava, data912, un RSS, `claude`) deja una línea en la consola y un aviso en la página, y la app sigue andando.
- [x] Un error inesperado simulado da 500 con el aviso en español y la traza solo en el log.
- [x] No hay `except Exception` sin comentario que lo justifique.
- [x] La suite pasa.

## Cómo probarlo
1. Sin internet, abrir la página: avisos en español y consola con detalle.
2. Sacar `claude` del PATH, tocar "Preparar el de hoy": mensaje claro en la página y línea de error en la consola.
3. Dejar un `datos/preferencias.json` roto: la app sigue y avisa.
4. `MICAFE_LOG=DEBUG python3 servidor.py` muestra más detalle.
5. `python3 -m unittest discover -s tests -t .`.

## Notas de implementación
- Nuevos: `micafe/errores.py` (`ErrorMiCafe` con `mensaje`, `codigo` y `extras`; subclases `ErrorResumen`, `ErrorFuente`, `ErrorAlmacenamiento`) y `micafe/logs.py` (`configurar()`, llamada en `main()`; formato `HH:MM:SS NIVEL módulo: mensaje`, INFO por defecto, `MICAFE_LOG=DEBUG` para más detalle).
- Todos los `print` pasaron a `logger.*` con el texto "Aviso: ..." intacto. El detalle del JSON roto de preferencias pasó a DEBUG. `resumen.ErrorResumen` sigue importable (se re-exporta desde `errores.py`).
- El servidor atrapa `ErrorMiCafe` en `do_GET`/`do_POST` (`_responder_error`), lo registra como aviso y responde `{"ok": false, "errores": [...]}` con su código (más `avisos` vía `extras` en el resumen). Los fallos de escritura (`OSError`) ahora se elevan como `ErrorAlmacenamiento` con los mismos textos de antes.
- Quedan solo dos `except Exception`, ambos en el servidor y comentados (último recurso). No hay hilo propio que llame a `claude`.
- Se agregó log de error cuando `claude` no está, se pasa del timeout o no devuelve texto (antes solo había mensaje en la página).
- Tests nuevos: clase `LogYErrores` en `tests/test_servidor.py` (3 tests). Suite: 171 OK.
- Verificado a mano con servidor en puerto 0: sin red (DolarApi, ArgentinaDatos, BCRA, Rava, data912 y los RSS dejan línea en el log y la página sigue), preferencias rotas, `claude` fuera del PATH y `MICAFE_LOG=DEBUG`.
