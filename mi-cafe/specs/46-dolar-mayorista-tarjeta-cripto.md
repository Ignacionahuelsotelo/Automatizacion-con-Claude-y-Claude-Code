# 46 - Dólar mayorista, tarjeta y cripto, y salida de los indicadores de la cuenta de palabras

**Estado:** hecha

## Depende de
Nada (se puede hacer en paralelo a las specs 43 a 45). Las specs 47 y 48 dependen de esta, porque acá se saca a los indicadores de la cuenta de 550 a 650 palabras y con más indicadores esa cuenta ya no tiene sentido.

## Para qué
DolarApi ya devuelve más casas en la misma respuesta de `/v1/dolares` que la que se consulta hoy. Sumar dólar mayorista, tarjeta y cripto sin una consulta más. Y como los indicadores van a ser muchos más (specs 47 y 48), dejan de descontarse del largo: el rango de 550 a 650 palabras cuenta solo las notas (decisión aprobada).

## Qué tiene que hacer
1. **Más cotizaciones:** en `micafe/fuentes/indicadores.py`, `COTIZACIONES` suma `("mayorista", "Dólar mayorista")`, `("tarjeta", "Dólar tarjeta")` y `("cripto", "Dólar cripto")` (las claves de `casa` se verifican contra la respuesta real de https://dolarapi.com/v1/dolares el día de hacer la spec y se anotan en `docs/investigacion.md` con fecha; si alguna se llama distinto, se usa el nombre real). Salen de la **misma respuesta** que oficial, blue, MEP y CCL: no hay una consulta nueva ni una copia local nueva.
2. **Sin una casa, sin dato:** si una de las tres casas no viene en la respuesta (o viene sin compra, venta o fecha válida), ese indicador queda en "sin dato" (`valor: None`) y los demás se muestran igual, con el mismo mecanismo de hoy (`_indicador`). Sin brechas nuevas: las brechas siguen siendo blue, MEP y CCL contra el oficial.
3. **Formato y fecha:** igual que los demás dólares (`venta $ 1.234,50 (compra $ 1.200,00)`, con la fecha de `fechaActualizacion` y "Desactualizado" si pasó más de 1 día hábil). El tarjeta se muestra como lo informa la API (el recargo ya viene en la venta); el código no calcula nada y el modelo tampoco escribe esos números.
4. **Grupo nuevo `dolar_otros`:** los tres indicadores nuevos llevan `grupo: "dolar_otros"` (no `"dolar"`). En `micafe/almacen/preferencias.py`, `INDICADORES` suma `"dolar_otros": "Otros dólares (mayorista, tarjeta y cripto)"`; `obtener(...)` solo los incluye si `"dolar_otros"` está en `elegidos`. `por_defecto()` los incluye (todo elegido, como hoy) y un `preferencias.json` viejo sin `dolar_otros` se lee igual y queda destildado (no se agrega solo), sin cambiarle el resumen a quien ya lo usa. Esto convive con el esquema v2 de la spec 49: allá la lista de indicadores acepta la misma clave.
5. **Página:** el bloque de indicadores y preferencias muestran los nuevos con los mismos componentes (la lista de indicadores elegibles ya sale del servidor en `opciones`; verificar que el checkbox nuevo aparece sin tocar `app.js` y, si hay que tocarlo, dejarlo anotado). Los textos son los de `nombre`, sin términos técnicos.
6. **Indicadores fuera de la cuenta de palabras (decisión aprobada):**
   - `micafe/dominio/corrector.py`: el chequeo "Largo" cuenta **solo el texto del resumen** (las notas, apertura y cierre incluidos si ya contaban) entre `MINIMO_PALABRAS` (550) y `MAXIMO_PALABRAS` (650); `palabras_indicadores` deja de sumarse al total y de aparecer en los mensajes de error y en el detalle del chequeo. Se mantiene la regla del plan: el mínimo solo se exige si el plan quedó completo, el máximo siempre, y si se pasa se recorta desde las secciones de menor prioridad, nunca los indicadores.
   - `micafe/dominio/resumen.py`: se borra `palabras_indicadores()` y la sección `## Palabras de los indicadores` del prompt (y el parámetro `palabras_de_indicadores` de `armar_pedido`); el prompt aclara que el rango de 550 a 650 palabras es de las notas y que los indicadores los pone el servidor y no cuentan. Actualizar `servicio.py` donde se la llamaba y el reintento del corrector.
   - Skills `.claude/skills/resumen-diario/SKILL.md` y `.claude/skills/corrector/SKILL.md`: el largo objetivo es de las notas; los indicadores no cuentan.
   - `CLAUDE.md`: la regla "Largo objetivo 550–650 palabras..." pasa a decir "cuenta solo las notas; los indicadores van aparte". Y la decisión 7 de `specs/README.md` ("Bloque de indicadores: cuenta dentro de las 550 a 650 palabras") queda marcada como reemplazada por esta spec.
7. **Lista de cifras prohibidas:** la skill de resumen y la del corrector (y el corrector con código, si hoy detecta números de indicadores en el texto) tienen una lista de cifras que el modelo no puede escribir: dólar oficial, blue, MEP, CCL, brechas, riesgo país, reservas, Merval y acciones. Sumar mayorista, tarjeta y cripto (y, de pasada, dejar escrito que lo mismo vale para las tasas y la inflación que llegan en las specs 47 y 48). Regla de CLAUDE.md: ningún número lo escribe el modelo; el modelo no repite cifras de indicadores en las notas.
8. **Copia local:** DolarApi no tiene límite de 3 horas (hoy no usa copia vigente: `reutilizar=False`); no se cambia.
9. **Fixtures:** `tests/fixtures/` suma (o ajusta) una respuesta de `/v1/dolares` con las siete casas (oficial, blue, bolsa, contadoconliqui, mayorista, tarjeta, cripto) y una variante sin `cripto` y otra con `tarjeta` sin fecha.

## Fuera de alcance
Reservas elegibles y tasas (47); inflación y UVA (48); brecha del mayorista, tarjeta o cripto; Bitcoin y cualquier otra cripto (decisión aprobada: afuera; el dólar cripto de DolarApi sí entra); cambiar la regla de "desactualizado"; la pantalla de preferencias (50).

## Archivos que toca
- `micafe/fuentes/indicadores.py`
- `micafe/almacen/preferencias.py`
- `micafe/dominio/corrector.py`, `micafe/dominio/resumen.py`, `micafe/dominio/servicio.py`
- `.claude/skills/resumen-diario/SKILL.md`, `.claude/skills/corrector/SKILL.md`
- `CLAUDE.md`, `docs/investigacion.md`, `specs/README.md` (nota sobre la decisión 7)
- `tests/test_indicadores.py`, `tests/test_preferencias.py`, `tests/test_corrector.py`, `tests/test_resumen.py`, `tests/test_servicio.py`, `tests/test_servidor.py`, fixtures nuevos

## Criterios de aceptación
- [x] Con las preferencias por defecto aparecen "Dólar mayorista", "Dólar tarjeta" y "Dólar cripto" con valor, fecha y fuente "DolarApi".
- [x] Si la respuesta de DolarApi no trae `cripto`, ese indicador dice "sin dato" y los otros dos siguen con valor.
- [x] No hay ninguna consulta de red nueva: una sola llamada a `/v1/dolares` por armado.
- [x] Los tres nuevos tienen `grupo` `"dolar_otros"` y se muestran solo si esa preferencia está tildada.
- [x] Un `preferencias.json` viejo se lee sin error y deja `dolar_otros` destildado.
- [x] El corrector cuenta solo el texto: un resumen de 560 palabras de notas pasa aunque los indicadores sumen 200 palabras; uno de 660 palabras de notas falla, sin importar los indicadores.
- [x] Con el plan incompleto, el mínimo sigue sin exigirse y el máximo sí.
- [x] El prompt ya no trae `## Palabras de los indicadores` y aclara que los indicadores no cuentan en el rango.
- [x] La skill y el corrector listan mayorista, tarjeta y cripto entre las cifras que el modelo no escribe.
- [x] `CLAUDE.md` ya no dice que los indicadores cuentan dentro de las 550 a 650 palabras.
- [x] `python3 -m unittest discover -s tests -t .` pasa y `python3 servidor.py` arranca.

## Tests (unittest, sin red ni `claude`)
- `test_indicadores.py`: las siete casas con fixture; falta de una casa; casa sin fecha o sin venta; `dolar_otros` ausente de `elegidos` no trae los tres; una sola consulta a DolarApi (contador en el `pedir_json` falso o en `urlopen` parcheado); formato `$ 1.234,50`; "desactualizado" con `ahora` fijo.
- `test_preferencias.py`: `dolar_otros` es un indicador válido, el viejo se lee igual.
- `test_corrector.py`: largo solo de notas en el límite (550, 650, 549, 651), plan incompleto, mensaje sin mención a indicadores.
- `test_resumen.py`: el prompt no trae la sección vieja; `armar_pedido` sin `palabras_de_indicadores`.
- `test_servicio.py` / `test_servidor.py`: el flujo completo con indicadores falsos y el largo bien contado.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `curl -s https://dolarapi.com/v1/dolares | python3 -m json.tool | grep casa`: confirmar los nombres de las casas y anotarlos en `docs/investigacion.md`.
3. `python3 servidor.py`, preparar el resumen: el bloque de indicadores muestra mayorista, tarjeta y cripto con su fecha.
4. En preferencias destildar "Otros dólares": al recargar, no aparecen.
5. Comparar el conteo de palabras que muestra el aviso del corrector con las notas solamente (copiar el texto de las notas en un contador de palabras).

## Notas de implementación
- Claves de `casa` verificadas el 24/11/2026: `mayorista`, `tarjeta` y `cripto` existen tal cual (anotado en `docs/investigacion.md`).
- `indicadores.obtener` trae el dólar si `dolar` o `dolar_otros` están en `elegidos`; `_dolares` arma cada grupo por separado y las brechas solo con `dolar`. Una casa ausente o sin fecha queda "sin dato" por el mecanismo de siempre.
- `por_defecto()` incluye `dolar_otros` solo porque sale de `INDICADORES`; un archivo viejo se lee igual y queda sin él. La página arma los checkboxes desde `opciones.indicadores`: no se tocó `app.js`.
- Corrector: el largo cuenta solo el texto y `revisar` ya no recibe `palabras_indicadores`. Resumen: se borró `palabras_indicadores()`, el parámetro de `armar_pedido` y el parámetro `indicadores` de `generar` (quedaba sin uso). El prompt trae una sección corta `## Largo` que aclara que el rango es de las notas y que los indicadores no cuentan.
- Fixture `dolarapi.json` ampliado a las siete casas; las variantes (sin `cripto`, `tarjeta` sin fecha) se arman en el test filtrando ese fixture, sin archivos nuevos.
- Cifras prohibidas: las skills de resumen y corrector ahora listan mayorista, tarjeta, cripto, brechas, tasas e inflación. El corrector con código no detecta números de indicadores (solo el chequeo con modelo, vía la skill).
- Pregunta abierta 7 de la tanda (nombres de casas): resuelta, eran correctos.
