# 40 - Plan de secciones calculado por código

**Estado:** hecha

## Depende de
39-seleccion-por-puntaje.

## Para qué
La skill `resumen-diario` fija las cantidades por sección (`SKILL.md:16-23, 48-50, 57-61`: Política 2, Economía 2, Internacional 2, Deportes 1 o 2, Tecnología 1) y los gustos solo desempatan. Si la persona deja solo Deportes, o pide más de un tema, el resumen no se adapta. El corrector además exige al menos 550 palabras (`micafe/dominio/corrector.py:170-175`), aunque no haya notas para llegar. Que el código calcule cada día cuántas notas lleva cada sección y que la skill y el corrector sigan ese plan.

## Qué tiene que hacer
1. En `micafe/dominio/seleccion.py` (puro, sin red ni disco) agregar `plan_de_secciones(candidatas, temas, pesos, tope_por_medio, total=NOTAS_OBJETIVO) -> list[CupoSeccion]` (nombre del tipo a definir en `modelos.py`: sección, cupo, cantidad de notas `[pedido]`, motivos del ajuste).
2. Reglas del plan:
   - Solo entran secciones tildadas en `temas` que tengan al menos una candidata.
   - Cada sección activa recibe al menos `config.MINIMO_POR_SECCION_ACTIVA = 1` y como máximo `config.MAXIMO_POR_SECCION`.
   - El reparto del resto sigue los pesos (`pesos` viene de `config.PESOS_PUNTAJE` y, desde la spec 41, del perfil de gustos): las secciones con notas marcadas `[pedido]` reciben más cupo.
   - **El plan nunca pide más notas de las que dan las candidatas y el tope por medio**: el cupo de una sección es como mucho la cantidad de candidatas que se pueden elegir respetando el tope por medio (3, o 5 los lunes) contado sobre el resumen entero.
   - Si el total posible es menor que `NOTAS_OBJETIVO`, el plan queda más chico (no se completa con relleno) y se marca como **incompleto**.
   - Determinista: mismas entradas, misma salida.
3. Constantes nuevas en `config.py`: `NOTAS_OBJETIVO = 9`, `MAXIMO_POR_SECCION`, `MINIMO_POR_SECCION_ACTIVA = 1`, cada una con su comentario.
4. `micafe/dominio/resumen.py` agrega al prompt la sección `## Plan de secciones para hoy` con una línea por sección y su cantidad exacta de notas (y qué candidatas `[pedido]` tiene), más si el plan quedó incompleto.
5. `.claude/skills/resumen-diario/SKILL.md`: se sacan las cantidades fijas y pasa a "seguí el plan de secciones, no escribas secciones fuera del plan". Se simplifican las reglas de gustos y de pedido (la selección y el plan ya los aplicaron; la skill solo redacta con lo elegido). No se tocan las reglas de indicadores, links, fechas ni formato.
6. `micafe/dominio/corrector.py`: dos chequeos nuevos por código (con su mensaje en español para el reintento):
   - **"Secciones del plan"**: ningún encabezado de sección fuera del plan y ninguna sección con más notas que su cuota.
   - **"Pedido"**: si hay al menos 2 notas `[pedido]` entre las candidatas, el resumen incluye al menos 2 de ellas (se comprueba por link). Con 1 sola, alcanza con 1.
   El chequeo de largo cambia: el mínimo de 550 palabras solo se exige si el plan quedó completo; el máximo de 650 sigue valiendo siempre. Si el plan es incompleto el largo mínimo se omite y se deja registrado en el resultado del corrector.
7. **Recorte por largo:** si el resumen se pasa de 650 palabras, se recorta desde las secciones de menor prioridad (la prioridad sale del plan: pedido, pesos y orden de `TEMAS`), nunca los indicadores. Actualizar esta regla en `CLAUDE.md`, que hoy dice "recortar desde Deportes y Tecnología". La skill y el mensaje de reintento del corrector usan la misma redacción.
8. `micafe/dominio/servicio.py` calcula el plan, lo pasa al prompt y al corrector y lo guarda en el resumen, en el campo `plan` (lista de secciones con su cupo y `completo: bool`). Los resúmenes viejos sin `plan` se siguen leyendo.
9. Se mantiene la regla de dedupe contra los últimos 3 resúmenes y la de 3 notas por medio.

## Fuera de alcance
El perfil aprendido de gustos (spec 41); mostrar el plan en la página (spec 42); cambiar el largo objetivo de 550 a 650 palabras; elegir con un modelo qué nota va en cada lugar (la elige Claude dentro del plan).

## Archivos que toca
- `micafe/dominio/seleccion.py`, `micafe/dominio/resumen.py`, `micafe/dominio/corrector.py`, `micafe/dominio/servicio.py`
- `micafe/config.py`, `micafe/modelos.py`
- `micafe/almacen/resumenes.py` (campo `plan`, solo si la lectura valida campos)
- `.claude/skills/resumen-diario/SKILL.md`, `.claude/skills/corrector/SKILL.md` (si menciona cantidades)
- `CLAUDE.md` (regla de recorte y 550 palabras condicionadas al plan)
- `docs/investigacion.md` o `docs/plan.md` si repiten las cantidades fijas
- `tests/test_seleccion.py`, `tests/test_resumen.py`, `tests/test_corrector.py`, `tests/test_servicio.py`

## Criterios de aceptación
- [x] Con solo Deportes tildado y 12 candidatas de 4 medios, el plan da Deportes 9 y ninguna otra sección.
- [x] Con 5 temas y candidatas de sobra, el plan suma `NOTAS_OBJETIVO` y cada sección activa tiene al menos 1.
- [x] Una sección con notas `[pedido]` recibe más cupo que sin pedido, con las mismas candidatas.
- [x] Con pocas candidatas (por ejemplo 5 en total), el plan pide como mucho 5 y queda marcado incompleto.
- [x] Un medio con una sola fuente y tope 3 no hace que el plan pida más de 3 de ese medio en total.
- [x] El prompt incluye `## Plan de secciones para hoy`.
- [x] El corrector rechaza un resumen con una sección fuera del plan o con más notas que su cuota, y lo acepta cuando cumple.
- [x] El corrector rechaza un resumen sin ninguna nota `[pedido]` cuando hay 2 o más que encajan.
- [x] Con el plan incompleto, un resumen de menos de 550 palabras pasa; con el plan completo, no.
- [x] El resumen guardado tiene `plan`; uno viejo sin `plan` se abre sin error.
- [x] `CLAUDE.md` ya no dice "recortar desde Deportes y Tecnología".
- [x] `python3 -m unittest discover -s tests -t .` pasa (320 tests). Se comprobó que `servidor` se importa, pero no se levantó el servidor real.

## Tests (unittest, sin red ni `claude`)
En `test_seleccion.py`: el caso de solo Deportes (12 candidatas, 4 medios), el reparto con cinco temas, el peso del pedido, el plan incompleto, el tope por medio, el lunes (tope 5) y el determinismo. En `test_corrector.py`: los chequeos "Secciones del plan" y "Pedido" y el mínimo de palabras condicionado, con resúmenes de ejemplo en `tests/fixtures/`. En `test_resumen.py`: el bloque del plan en el prompt. En `test_servicio.py` (con `claude` simulado): el plan se guarda en el resumen.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. Dejar solo Deportes y preparar el resumen: sale una sola sección con unas 9 notas (puede ser menos si el corrector avisa que el plan quedó incompleto), sin otras secciones.
3. Tildar todo y pedir "más economía": Economía tiene más notas que las demás y el resumen respeta el plan.
4. Abrir `datos/resumenes/AAAA-MM-DD.json` y revisar `plan`.
5. Leer en `CLAUDE.md` la regla nueva de recorte.

## Notas de implementación
- `seleccion.plan_de_secciones(candidatas, temas, pesos, tope_por_medio, total, pedidas)` devuelve `list[CupoSeccion]` (`seccion`, `cupo`, `pedidas`, `motivos`) en el orden de `TEMAS`. Para marcar "incompleto" sin cambiar el tipo de retorno hay una función aparte, `plan_completo(plan, total)`; `orden_de_recorte(plan)` da las secciones de menor a mayor prioridad (más `[pedido]`, más cupo, orden de `TEMAS`).
- Reparto: mínimo 1 por sección activa y el resto por D'Hondt con peso = `pesos.get(sección, 1.0) + PESO_POR_NOTA_PEDIDA (0.5) * notas [pedido]`. Decisión (más simple): `PESOS_PUNTAJE` es por lugar de la nota (título, bajada...), no por sección, así que `pesos` es un dict sección -> peso que hoy llega vacío; la spec 41 lo llena con el perfil.
- El tope por medio se descuenta del resumen entero al conceder cada nota, por eso nunca se piden más notas de las posibles. `MAXIMO_POR_SECCION = 9` (igual al objetivo) para cumplir "solo Deportes da 9".
- Las candidatas sin `seccion` no entran al plan. Si el plan queda vacío, el servicio no pasa plan (ni al prompt ni al corrector), no lo guarda y se exige el largo de siempre.
- Se guarda `plan = {"secciones": [...], "completo": bool}`. El corrector sumó "Secciones del plan" y "Pedido" (solo corren si se les pasa `plan` / `pedidas`); con plan incompleto el chequeo de largo queda "omitido" con el detalle en `chequeo.omitido`.
- Regla de recorte unificada en CLAUDE.md, `docs/investigacion.md`, la skill, el prompt y el mensaje del corrector. `docs/plan.md` y la skill del corrector no mencionan cantidades fijas.
- Se reescribieron las secciones de gustos y pedido de la skill (más cortas). El test del mensaje de recorte de `test_corrector.py` y uno de `test_servicio.py` (el pedido "más economía" ahora exige las 2 notas que encajan) se ajustaron.
- No verificado: pasos 2 a 4 de "Cómo probarlo" (servidor real con `claude`).
