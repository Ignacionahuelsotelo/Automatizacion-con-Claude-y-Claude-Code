# 07 - Corrector

**Estado:** hecha

## Depende de
06-skills-completas

## Para qué
Revisar el resumen antes de mostrarlo: que cada nota tenga enlace, que no repita notas de los últimos 3 días y que el largo sea el correcto.

## Qué tiene que hacer
1. Crear la skill del corrector en `.claude/skills/` y un paso extra en el servidor que corre después de redactar.
2. Chequeos que se pueden hacer con código, sin modelo: cantidad de palabras (550 a 650, incluyendo el bloque de indicadores), links presentes en cada nota, links que pertenecen a las notas pasadas, máximo 3 notas por medio (5 los lunes).
3. Deduplicar por URL y por título contra los últimos 3 resúmenes guardados en `datos/resumenes/` (si todavía no hay, no se chequea). También detectar la misma noticia en dos secciones del mismo resumen.
   - Glosario de vigencia: detectar "S&P Merval" y "Télam" como agencia vigente.
   - Un chequeo con modelo (skill del corrector): que lo que dice cada nota esté respaldado por el texto de su enlace; atribución correcta del medio.
4. Si el resumen no pasa, reintentar la redacción indicando qué falló (2 reintentos como máximo).
5. Si después de los reintentos sigue sin pasar, mostrar el resumen con un aviso visible de qué reglas no cumple; no ocultar el problema.
6. Devolver al navegador el resultado del chequeo (qué se verificó y qué no pasó).

## Fuera de alcance
Guardar los resúmenes (spec 08; acá solo se leen los existentes si los hay), diseño final.

## Archivos que toca
- `servidor.py`
- `.claude/skills/corrector/SKILL.md` (nuevo)
- `corrector.py` (nuevo; ver notas)
- `resumen.py` y `index.html` (fuera de la lista original; ver notas)

## Criterios de aceptación
- [x] Un resumen sin link en una nota es detectado y reenviado a corregir.
- [x] Un resumen de menos de 550 o más de 650 palabras es detectado.
- [x] Una nota repetida (mismo link o título casi igual) de los últimos 3 resúmenes es detectada.
- [ ] Tras agotar los reintentos, el resumen se muestra con aviso y no se cuelga. (El servidor lo devuelve con el aviso y no se cuelga; el aviso visible en la página no se miró en un navegador.)
- [x] Los chequeos numéricos los hace código, no el modelo.

## Cómo probarlo
1. Probar el corrector con textos armados a mano: uno sin link, uno corto, uno con nota repetida.
2. Correr un resumen real y mirar el resultado del chequeo.
3. Forzar el fallo (por ejemplo bajando el máximo de palabras) y ver el aviso.

## Notas de implementación

**Qué se hizo**
- `corrector.py` (nuevo): chequeos con código y ciclo de revisión. Chequeos: largo (texto más bloque de indicadores, entre 550 y 650), enlaces (cada nota con link y todos los links de las notas de ayer), tope por medio (3, o 5 los lunes, que pasa el server), repetidas dentro del resumen (mismo link o título casi igual, aunque sea en otra sección), repetidas contra los últimos 3 resúmenes, "S&P Merval" y Télam como agencia (con "ex Télam" permitido). Después, si nada falló, el chequeo con modelo.
- `.claude/skills/corrector/SKILL.md` (nuevo): el chequeo con modelo. Recibe el resumen y la lista de notas de ayer, responde `OK` o una línea `- ` por problema. No reescribe nada.
- `servidor.py`: `POST /api/resumen` pasa por `corrector.revisar`. La respuesta suma el campo `chequeo` (`aprobado`, `intentos`, `verificado`, `no_cumple`, `omitido`).
- `resumen.py`: se extrajo `ejecutar_claude(pedido, carpeta)` desde `generar` (mismo comportamiento) para que el corrector lo reuse. `armar_pedido` y `generar` aceptan `correcciones` y `borrador` para el reintento. Ojo: no estaba en la lista de archivos de la spec, pero no hay otra forma de pasarle al reintento qué falló sin duplicar `claude -p`.
- `index.html`: un párrafo `#aviso-corrector` que muestra qué no cumple, cuando `chequeo.aprobado` es falso. La spec pide el aviso visible, pero `index.html` no estaba en su lista. La spec 08 (punto 7) también lo menciona; si preferís que quede solo en 08, se puede sacar.

**Decisiones**
- Reintentos: 1 redacción + 2 reintentos como máximo (3 redacciones). Si el chequeo con modelo no se puede ejecutar (falla o timeout de `claude`), no se reintenta la redacción: queda como "no se pudo revisar" en el aviso.
- El modelo solo se llama cuando pasan los chequeos de código, para no gastar llamadas en resúmenes que ya fallan.
- Si la redacción de un reintento falla con `ErrorResumen`, el error se propaga como antes (la página muestra el error, no un resumen parcial).
- "Título casi igual": similitud de caracteres (difflib) ≥ 0.85 sobre el texto normalizado (sin tildes, mayúsculas ni puntuación).
- Resúmenes anteriores: se leen de `datos/resumenes/AAAA-MM-DD.json`, los 3 más nuevos, con la clave `"texto"`. Esto es un supuesto para la spec 08, que todavía define el formato. Si no hay carpeta o archivos, el chequeo se omite y lo dice en `omitido`.
- Para que el corrector no reescriba el resumen: el modelo solo informa, el reintento lo hace la redacción con la lista de problemas y el borrador anterior.

**Limitaciones del chequeo con modelo**
- El corrector solo recibe título, medio y link de cada nota (lo que tiene la lista). No abre los links ni tiene el texto del artículo, así que "respaldado por el texto de su enlace" se revisa contra el título y el medio. Para leer el artículo habría que traer más datos desde `noticias.py`, que la spec no pide.

**Pruebas hechas (en el puerto 8131; el 8000 no se tocó ni se reinició)**
- Script de pruebas en scratchpad (28 casos, sin llamar a Claude; más una prueba suelta de nota sin link que vuelve con la corrección): texto armado a mano con nota sin link, resumen de menos de 550, de más de 650, mismo link dos veces, título casi igual en dos secciones, repetida de un resumen anterior por link y por título, tope 3 y 5, "S&P Merval", Télam y "ex Télam", link ajeno, veredicto del modelo, reintentos (pasa al 2.º, agota 3 intentos, rechazo del modelo, falla técnica del modelo) y lectura de resúmenes previos. Todos pasaron.
- Servidor de prueba con un `claude` falso en el PATH (sin gastar plan): 3 intentos por largo con aviso; 2 intentos por largo con aprobación final; rechazo del modelo con reintento y aprobación al 3.º intento.
- Corrida real con `claude -p`: 3 intentos y no aprobado. El corrector detectó que una nota de elDiarioAR sobre la interna peronista no cita las otras fuentes (Página/12) en un tema polémico. Largo 583 palabras con indicadores, 6 notas con link, sin "S&P Merval" ni Télam. La respuesta trae el aviso y el resumen. Se corrió una sola vez: la redacción no logró corregir ese punto en los 3 intentos.
- Se verificó la sintaxis de `index.html` con `node --check`; no se miró en un navegador.

**Pendiente o no probado**
- El aviso visible en la página no se vio en un navegador (criterio 4 sin tildar).
- Dedupe contra resúmenes reales: `datos/resumenes/` todavía no existe (spec 08). Se probó con archivos armados en una carpeta temporal.
- El chequeo de "respaldo" con modelo tiene la limitación de arriba (solo títulos).
- Las notas no se leen completas, así que un tema polémico que requiere dos fuentes depende de lo que diga el modelo.
