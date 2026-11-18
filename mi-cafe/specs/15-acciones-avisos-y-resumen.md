# 15 - Acciones: avisos, página y resumen guardado

**Estado:** hecha

## Depende de
13-acciones-data912, 14-merval-rava, 12-manejo-errores

## Reemplaza a
El punto 5 de `11-acciones.md` (solo mostrarlas si el usuario las eligió) se mantiene; esta spec reemplaza lo que `11` dice sobre mostrar "sin dato" siempre y la nota "La acción MSCI Merval y las demás acciones salen 'sin dato'" de `CLAUDE.md`.

## Para qué
Que las acciones y el MSCI Merval, ya con datos reales, se integren bien: avisos en español cuando algo falla, el bloque guardado con el resumen, el conteo de palabras y el estado del proyecto.

## Qué tiene que hacer
1. `acciones.py` devuelve, junto con los indicadores, una lista de `avisos` en español (mismo formato que ya usa `indicadores.py` desde la spec 12). Ejemplos: "No se pudo consultar Rava: tardó demasiado. Se usó data912 para el MSCI Merval.", "No se pudo consultar data912 para GGAL: no se pudo conectar.", "El dato de PAMP tiene fecha vieja (dd/mm/aaaa)." Sin trazas ni mensajes en inglés; el detalle técnico va a la consola del servidor.
2. Unir esos avisos con los de los demás indicadores en `/api/indicadores` y en la respuesta de `POST /api/resumen`, y mostrarlos en la caja `#avisos-indicadores` que ya existe (sin diseño nuevo).
3. Un indicador de acciones con respuesta 200 pero sin valor usable avisa también (hoy la spec 12 lo deja sin aviso).
4. Un HTTP 410 de data912 o de Rava avisa que la dirección dejó de existir y hay que actualizarla.
5. `index.html` muestra el valor, la fecha, la fuente y la marca de desactualizado igual que con los otros indicadores. Si el valor es `null`, "sin dato" más la fuente. No debería hacer falta tocarlo; si no hace falta, no se toca.
6. El bloque de indicadores que se guarda en `datos/resumenes/AAAA-MM-DD.json` incluye las acciones y el MSCI Merval con su valor real, fecha y fuente.
7. `resumen.palabras_indicadores()` cuenta las palabras del bloque tal como lo muestra la página (con valores reales las frases son más largas que con "sin dato"), así el pedido le pasa a Claude el N correcto.
8. Confirmar que el modelo no recibe ni escribe los valores de las acciones: el pedido a `claude -p` sigue sin indicadores, solo con N.
9. Actualizar `CLAUDE.md` (solo "Estado del proyecto"): ya no dice que las acciones salen "sin dato" hasta aprobar una fuente, sino que el MSCI Merval sale de Rava (con respaldo data912) y GGAL, YPFD y PAMP de data912, y que cada una cae en "sin dato" si su fuente falla.

## Fuera de alcance
- Cambiar las reglas de las skills (spec 16).
- Cambiar `docs/investigacion.md` (spec 16).
- Diseño nuevo de la página, preferencias una por una.

## Archivos que toca
- `acciones.py`
- `servidor.py` (unir avisos y bloque guardado)
- `resumen.py` (solo el conteo de palabras si hace falta)
- `index.html` (solo si hace falta)
- `CLAUDE.md` (solo estado)

## Criterios de aceptación
- [x] Con Rava caído, la página avisa en español y el índice sale con data912 o "sin dato".
- [x] Con data912 caído, la página avisa qué tickers fallaron y los demás indicadores se ven.
- [x] Un 410 simulado se avisa como dirección dada de baja.
- [x] Un dato con más de 1 día hábil aparece con la marca de desactualizado y su aviso.
- [x] Ningún aviso muestra trazas ni texto en inglés.
- [x] El archivo guardado en `datos/resumenes/` trae el MSCI Merval y las tres acciones con valor, fecha y fuente.
- [x] El conteo de palabras del resumen (texto más bloque) queda entre 550 y 650 con las acciones con valor real.
- [x] El resumen redactado no contiene ninguna cifra de acciones ni del índice.
- [x] `CLAUDE.md` ya no dice que las acciones salen "sin dato" por falta de fuente.
- [ ] "Preparar el de hoy" no borra las acciones de la página.

## Cómo probarlo
1. Abrir la página con "acciones" tildada y ver que están las cuatro con valor, fecha y fuente.
2. Romper a propósito Rava (URL mala) y después data912; en cada caso leer el aviso en la página y el error técnico en la consola.
3. Tocar "Preparar el de hoy" y abrir el JSON del día en `datos/resumenes/`: tiene que traer las cuatro acciones con valor.
4. Buscar a mano en el texto del resumen cifras de acciones o del índice: no tiene que haber ninguna.
5. Contar las palabras del resumen más el bloque (o mirar el conteo del servidor): entre 550 y 650.

## Notas de implementación
- `acciones.py`: nueva `obtener_todo()` (MSCI Merval + GGAL, YPFD, PAMP, con sus avisos). `obtener_merval()` y `obtener()` suman el aviso de dato desactualizado; el Merval avisa también cuando Rava falla ("se muestra sin dato", o "Se usó data912" si el respaldo estuviera activo) y el 410 de Rava se explica como dirección dada de baja (antes decía "HTTP 410").
- `servidor.py`: `indicadores_con_acciones()` ahora recibe y devuelve el diccionario completo, así los avisos de acciones se unen a los de los demás indicadores en `/api/indicadores` y en `POST /api/resumen`. El bloque guardado ya incluía las acciones con valor real.
- `resumen.palabras_indicadores()` ya contaba igual que la página (valor, fecha, fuente, "Desactualizado"); no hizo falta tocarlo. `index.html` tampoco.
- El pedido a `claude -p` sigue sin indicadores (solo N de palabras).
- `CLAUDE.md`: actualizado "Estado del proyecto".
- Prueba (servidor en puerto 8011, el 8000 no se tocó): con las cuatro acciones reales; Rava caído, data912 caído y 410 simulados desde un script (avisos en español, sin trazas); dato viejo simulado. Resumen real: bloque 168 palabras + texto 448 = 616. El corrector terminó con aviso (no aprobado tras 3 intentos) por una nota de Ámbito sin relación con acciones. Las únicas menciones de "acciones" en el texto son de Nvidia, sin cifras del índice ni de GGAL/YPFD/PAMP.
- Sin tildar: "Preparar el de hoy" no borra las acciones de la página (requiere el navegador; el código del front no se tocó y `mostrarAvisosDelResumen` / `datos.resumen.indicadores` usan la lista guardada con acciones, pero no lo vi en pantalla). La prueba rota de Rava/data912 se hizo con el módulo, no con la página en un navegador.
