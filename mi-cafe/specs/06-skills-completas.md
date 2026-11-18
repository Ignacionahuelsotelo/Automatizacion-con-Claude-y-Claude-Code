# 06 - Skills completas

**Estado:** hecha

## Depende de
05-primer-resumen

## Para qué
Pasar de la skill simple a las reglas completas del resumen, para que salga con la estructura, el largo y los nombres correctos.

## Qué tiene que hacer
1. Reemplazar o ampliar la skill simple por las skills definitivas en `.claude/skills/`, con las reglas de `docs/investigacion.md`.
2. Estructura fija, siempre en este orden (de `docs/investigacion.md`):
   - Apertura: 1 frase con "lo más importante de hoy" (unas 25 palabras).
   - Indicadores: bloque que arma el servidor (unas 60 palabras, sin prosa); la skill no lo redacta.
   - Política: 2 notas. Economía: 2. Internacional: 2. Deportes: 1 o 2. Tecnología: 1.
   - Cada nota: título de hasta 10 palabras, 1 o 2 frases (40 a 50 palabras), una línea de "por qué importa", y medio, fecha y enlace.
   - Cierre opcional: "Lo que viene hoy", 1 línea de agenda, solo si surge de las notas.
   Máximo 3 notas por medio (5 los lunes) y, en temas polémicos, dos fuentes.
3. Largo objetivo de 550 a 650 palabras, contando el bloque de indicadores (confirmado); si se pasa, recortar desde Deportes y Tecnología, nunca los indicadores.
4. Nombres vigentes: el índice es **MSCI Merval** (desde 19/10/2026, no "S&P Merval"); Télam ya no existe como agencia.
5. Toda noticia con link; Clarín y La Nación solo para detectar temas, no como único enlace.
6. Ningún número lo escribe el modelo: la skill lo dice explícito y manda a usar los valores que pone el servidor.
7. Si no hay notas suficientes para una sección, omitirla o decir que no hay novedades, sin rellenar.

## Fuera de alcance
La verificación automática de las reglas (spec 07), diseño de la página, gustos.

## Archivos que toca
- `.claude/skills/` (skills nuevas o ampliadas)
- `servidor.py` (solo si hace falta pasarle a la skill datos extra, sin meter reglas ahí)

## Criterios de aceptación
- [x] El resumen tiene secciones claras y cada nota con 1 o 2 frases.
- [x] El largo está entre 550 y 650 palabras en al menos 3 corridas distintas.
- [x] Todas las notas tienen link.
- [x] No aparece "S&P Merval" ni Télam como agencia vigente.
- [x] Ningún medio tiene más de 3 notas.
- [x] Las reglas están en `.claude/skills/`, no en el código Python.

## Cómo probarlo
1. Preparar 3 resúmenes seguidos y contar palabras de cada uno.
2. Buscar a mano "S&P Merval" y "Télam" en el texto.
3. Revisar que cada nota tenga link y que ningún medio pase de 3.

## Notas de implementación

**Qué se hizo**
- `.claude/skills/resumen-diario/SKILL.md` (nuevo): la skill completa. Fija el orden (apertura, indicadores que no se redactan, Política, Economía, Internacional, Deportes, Tecnología, cierre opcional), la cantidad de notas por sección, el formato de cada nota en texto plano (título, 40 a 50 palabras de cuerpo, "Por qué importa:", medio y fecha, link en su propia línea), el largo, los nombres vigentes y las prohibiciones (no cifras de indicadores, no markdown, no saludos).
- Se borró `.claude/skills/resumen-basico/` (la skill simple de la spec 05), porque la spec pide reemplazarla.
- `resumen.py`: apunta a `resumen-diario`. Nuevas funciones `palabras_indicadores()` (cuenta las palabras del bloque tal como lo muestra la página) y el parámetro `tope` y `indicadores` en `generar()`. `armar_pedido()` agrega al pedido el tope por medio de hoy y la cantidad de palabras de los indicadores. Son datos, no reglas: las reglas siguen en la skill.
- `servidor.py`: en `POST /api/resumen` pasa a `resumen.generar` el `tope_por_medio` (3, o 5 los lunes) y la lista de indicadores para contar palabras. Antes solo pasaba las notas.

**Decisiones**
- Los indicadores no le llegan a Claude para que los redacte. Pero el largo de 550 a 650 incluye el bloque, y el bloque pesa más que las unas 60 palabras de la spec: con los indicadores activos hoy (dólar oficial, blue, MEP y CCL, tres brechas, riesgo país, reservas y acciones) suma 118 palabras. Por eso el pedido dice cuántas palabras suma el bloque (N) y la skill calcula el rango del texto: entre 550 − N y 650 − N. Con N = 118 son 432 a 532 palabras de texto.
- Se contaron las palabras con el mismo formato que muestra la página ("Nombre: valor (fecha X, fuente: Y)"). Los links cuentan como una palabra cada uno.
- Por qué "resumen.py" también se tocó: la spec solo nombra `servidor.py`, pero el pedido se arma en `resumen.py`, y ahí es donde van los datos extra.

**Pruebas hechas (en el puerto 8130; el 8000 no se tocó ni se reinició)**
- Cinco corridas reales de `POST /api/resumen`. Las corridas 1 y 2 quedaron fuera de rango (526 y 464 palabras con indicadores) y se usaron para ajustar la skill: el cuerpo de cada nota era de unos 30 palabras y Deportes salía con una sola nota.
- Corridas 3, 4 y 5 (después del ajuste): 571, 586 y 573 palabras con indicadores. Las tres dentro de 550 a 650.
- En esas tres: todos los links están en la lista de notas de ayer (`/api/noticias`), ningún medio pasa de 3 notas, no aparece "S&P Merval" ni "Télam". Cada nota tiene título de hasta 10 palabras, cuerpo de 40 a 50 palabras, "Por qué importa:" y link.
- Prueba directa de `armar_pedido` con tope 5: el pedido lo incluye. No se llamó a Claude para esta prueba, porque hoy es miércoles.

**Pendiente o no probado**
- No se probó el lunes con un resumen real (tope de 5), por el día de la semana.
- El pool de hoy tiene 13 notas y ninguna de Internacional ni de Tecnología (los feeds de esas secciones no trajeron ítems). Por eso no se vio el orden completo de 8 notas ni el cierre "Lo que viene hoy". Las secciones vacías se omiten y el resumen sale bien con eso.
- Con pocas notas el largo de 550 a 650 no se alcanza: el pool de hoy da unos 570 con 6 notas y 118 de indicadores. Si un día hay menos notas, el resumen queda más corto y la skill indica no rellenar.
- Dedupe contra los últimos 3 resúmenes no está: la skill no recibe el archivo de resúmenes. Va con la spec 07 (corrector) y la 08 (archivo).
- En temas polémicos, la regla de citar dos fuentes en una misma nota no se vio en ninguna corrida.
- Cómo se ve en el navegador no se verificó. Ojo: `index.html` muestra cada párrafo con `textContent` sin `white-space: pre-line`, así que los saltos de línea dentro de una nota se van a colapsar y el título, el "Por qué importa" y el medio van a aparecer pegados. Es un tema de diseño para la spec 08; no se cambió `index.html` acá.
- El criterio 2 se comprobó con el conteo del servidor (texto más bloque de indicadores), no a mano.
