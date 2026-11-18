# 33 - Candidatas: tope por medio y por sección

**Estado:** hecha

## Depende de
32-diagnostico-de-feeds (hay que haber medido el problema antes).

## Para qué
`noticias.obtener` aplica el tope (3, o 5 los lunes) por medio sobre todas las secciones juntas, así que las notas más nuevas de un medio pueden ocupar todo su cupo en una sola sección y dejar a otras sin candidatas (Infobae está en las cinco secciones y es la única fuente de Tecnología). Que cada sección tenga sus propias candidatas.

## Qué tiene que hacer
1. Cambiar la selección de candidatas en `noticias.obtener` para que el tope se cuente por **(medio, sección)** en lugar de solo por medio: hasta 3 notas (5 los lunes) por cada par, las más nuevas. La deduplicación por link y el orden por sección no cambian.
2. La regla de CLAUDE.md "máximo 3 notas por medio" **no se toca**: sigue valiendo para el resumen y la hacen cumplir la skill `resumen-diario` y el corrector (`Tope por medio`, sobre el resumen completo). `tope_por_medio` se sigue pasando al pedido y al corrector con el mismo valor. Lo que cambia es que la lista de candidatas puede tener más de 3 notas del mismo medio. Confirmar leyendo `corrector.py` que el corrector cuenta el tope en el resumen entero (hoy lo hace) y que un test lo cubre.
3. Constante nueva en `micafe/config.py` con comentario: `CANDIDATAS_POR_MEDIO_Y_SECCION = 3` y `CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES = 5` (mismos valores que los topes actuales, desacoplados de la regla del resumen).
4. El texto del pedido (`## Tope de notas por medio para hoy`) y la skill `resumen-diario` aclaran que la lista puede traer más notas por medio que el tope, y que el tope se cumple al elegir (el resumen no puede pasar el tope en total).
5. La página sigue mostrando todas las candidatas ordenadas por sección. Si la lista resulta demasiado larga se decide aparte (pregunta abierta 3).
6. Documentar la distinción en `CLAUDE.md` (sección "Reglas") sin cambiar la regla.

## Fuera de alcance
Cambiar la regla de 3 por medio para el resumen; cambiar cuántas notas lleva cada sección del resumen (2, 2, 2, 1 o 2 y 1: ver pregunta abierta 2); agregar fuentes (spec 34).

## Archivos que toca
- `micafe/fuentes/noticias.py`
- `micafe/config.py`
- `micafe/dominio/resumen.py` (texto del pedido)
- `.claude/skills/resumen-diario/SKILL.md`
- `CLAUDE.md`
- `tests/test_noticias.py`, `tests/test_resumen.py`, `tests/test_corrector.py`

## Criterios de aceptación
- [x] Con un fixture donde un medio tiene 5 notas en Política más recientes que 2 en Tecnología, la lista incluye 3 de Política y las 2 de Tecnología (antes dejaba 3 de Política).
- [x] Un lunes el cupo por (medio, sección) es 5.
- [x] Un resumen que repite 4 notas de un mismo medio sigue siendo rechazado por el corrector (test existente o nuevo).
- [x] `tope_por_medio` en el resultado y en el pedido sigue siendo 3 (5 los lunes).
- [x] Los demás criterios de la spec 04 (ventana, fechas, links, deduplicación) siguen pasando.
- [x] `python3 -m unittest discover -s tests -t .` pasa.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`: en "Noticias de ayer" aparecen más notas por sección que antes (comparar con la medición de la spec 32) y no se repite ningún link.
3. Preparar el resumen: ninguna sección queda vacía si hay candidatas, y ningún medio supera 3 notas en el resumen.

## Notas de implementación
- `noticias.obtener` cuenta el cupo por (medio, sección) con `CANDIDATAS_POR_MEDIO_Y_SECCION` (3) y `..._LUNES` (5), nuevas en `config.py`. `tope_por_medio` sigue siendo 3 (5 los lunes) en el resultado, el pedido y el corrector.
- El pedido y la skill aclaran que la lista puede traer más notas de un medio que el tope. CLAUDE.md documenta la distinción.
- El test existente `TopePorMedio` del corrector ya cubría el rechazo de 4 notas de un medio sobre el resumen entero.
- Tamaño: el máximo teórico son (pares medio-sección) x 3, unos 36 con las fuentes actuales (60 los lunes); medido: 24 notas, unos 6,6 mil caracteres. No hizo falta un tope total por sección.
- Medición con red real (18/11/2026): Internacional pasó de 0 a 3, Economía de 3 a 9, Política de 6 a 9; ver `docs/investigacion.md`.
- No verificado: pasos 2 y 3 de "Cómo probarlo" (la página y preparar un resumen real con `claude`).
