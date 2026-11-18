# 32 - Diagnóstico de feeds: cuántas notas trae cada fuente

**Estado:** hecha

## Depende de
Ninguna. Es la base de las specs 33 y 34: antes de agregar fuentes o tocar topes hay que medir.

## Para qué
Se dice que hay pocas notas por tema, pero hoy no se sabe cuántas notas trae cada feed, cuántas caen en la ventana de ayer ni cuántas se pierden por el tope. Esta spec agrega esa medición (sin cambiar qué notas se muestran) y documenta lo que se ve.

## Lo que se encontró leyendo el código
- `config.FUENTES_RSS` tiene 12 feeds: Política (Infobae, elDiarioAR, Página/12), Economía (Infobae, Ámbito x2, Página/12), Internacional (Página/12, Infobae), Deportes (Olé, Infobae), Tecnología (solo Infobae). Un comentario de `config.py` dice que Infobae internacional y tecnología "responden bien pero hoy no traen ítems" (11/11/2026): si sigue así, Tecnología queda sin notas.
- `noticias.obtener` aplica el tope por medio (3, o 5 los lunes) sobre **todas** las secciones juntas: se ordena por fecha y cada medio conserva sus 3 notas más nuevas sin mirar la sección. Infobae está en las cinco secciones, así que sus 3 notas pueden ser todas de Política y dejar a Tecnología o Deportes sin ninguna (esto se corrige en la spec 33).
- La ventana es solo ayer (los lunes, viernes a domingo): un feed que publica poco, o que cacheó, trae pocas notas dentro de la ventana.
- El corrector cuenta el tope sobre el resumen completo (`_chequear_codigo`, "Tope por medio").
- Los feeds se leen de a uno, en serie, con 10 s de timeout cada uno.

## Qué tiene que hacer
1. `noticias.obtener` suma al resultado una lista `por_fuente`: por cada feed leído, `{medio, seccion, leidas, en_ventana, elegidas}` (cuántas notas tenía el feed, cuántas caen en la ventana y cuántas quedaron tras deduplicar y aplicar el tope). Los feeds que fallaron ya están en `fallas`. No cambia `notas`, `fallas` ni el resto de las claves.
2. Se agrega el tipo a `micafe/modelos.py`.
3. Cada vez que se arma la lista, se loguea a nivel INFO una línea por feed con esos números (solo conteos: ni títulos ni links). Con `MICAFE_LOG=DEBUG` sigue igual.
4. Con eso, hacer la medición real y dejarla escrita en una tabla nueva en `docs/investigacion.md` ("Cobertura medida de los feeds"): fecha de la prueba, un día hábil común y un lunes, por feed. Si un feed no trae ítems o ninguno con fecha en la ventana, anotarlo.
5. Escribir al final de esta spec, en "Resultado de la medición", cuántas notas candidatas queda por sección y qué secciones están flojas. Ese número alimenta las specs 33 y 34.

## Fuera de alcance
Agregar o quitar feeds (spec 34); cambiar topes (spec 33); mostrar los conteos en la página; leer feeds en paralelo (pregunta abierta 6).

## Archivos que toca
- `micafe/fuentes/noticias.py`
- `micafe/modelos.py`
- `docs/investigacion.md` (tabla de cobertura medida)
- `tests/test_noticias.py` (con feeds de `tests/fixtures/`)
- esta spec (sección "Resultado de la medición")

## Criterios de aceptación
- [x] `obtener(...)` devuelve `por_fuente` con `leidas`, `en_ventana` y `elegidas` correctos para un fixture con fechas dentro y fuera de la ventana y más notas que el tope (el test calcula los valores esperados a mano).
- [x] `notas`, `fallas`, `ventana`, `tope_por_medio` y `generado_en` salen idénticos a antes (los tests existentes de `test_noticias.py` siguen pasando sin tocarse).
- [x] Los logs traen solo conteos: ningún título ni link.
- [x] `docs/investigacion.md` tiene la tabla de cobertura con fecha de la medición.
- [x] "Resultado de la medición" está completado.
- [x] `python3 -m unittest discover -s tests -t .` pasa, sin red.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir la página (carga las noticias) y mirar la consola del servidor: hay una línea por feed con sus conteos.
3. Un día hábil y un lunes (o simulando la fecha en un test), anotar los conteos en `docs/investigacion.md`.
4. Confirmar que la lista de "Noticias de ayer" es la misma que antes del cambio.

## Resultado de la medición

Medido el 18/11/2026 (detalle en `docs/investigacion.md`, "Cobertura medida de los feeds"). Candidatas en ventana por sección en un día hábil (martes 17/11, sumando los feeds; puede haber repetidos entre medios): Política 62, Economía 68, Internacional 7, Deportes 42, Tecnología 0. Notas que hoy muestra la lista: Política 6, Economía 3, Internacional 0, Deportes 3, Tecnología 0.

Secciones flojas:
- **Tecnología:** sin notas, porque su único feed (Infobae) no trae ítems.
- **Internacional:** hay 7 candidatas (todas de Página/12) pero se muestran 0, porque el tope de 3 por medio se cuenta sobre todas las secciones juntas y las de Infobae/Página/12 se lo llevan otras secciones; Infobae Internacional tampoco trae ítems. Esto lo corrige la spec 33.
- **Deportes:** Olé no tiene ítems en la ventana; solo aporta Infobae.
- **Economía:** 68 candidatas pero solo 3 mostradas por el mismo tope compartido.
- El lunes es una simulación (ver la tabla): hay que repetirla un lunes real.

## Notas de implementación

- `noticias.obtener` suma `por_fuente` (tipo `ConteoDeFuente` en `micafe/modelos.py`). Un link repetido entre feeds se le anota al primer feed que lo trae (el mismo que gana en la deduplicación). Los feeds que fallaron no aparecen en `por_fuente`, quedan en `fallas`.
- Una línea INFO por feed con solo conteos. Las claves anteriores del resultado no cambian.
- Tests nuevos en `tests/test_noticias.py` (`DiagnosticoPorFuente`); los anteriores no se tocaron.
- Medición hecha con red real y la librería estándar; el lunes se simuló pasando `ahora` del 16/11.
