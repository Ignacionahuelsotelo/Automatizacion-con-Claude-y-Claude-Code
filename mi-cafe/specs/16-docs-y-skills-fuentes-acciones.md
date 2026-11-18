# 16 - Docs y skills: coherencia con las fuentes de acciones

**Estado:** hecha

## Depende de
Nada del código: se puede hacer en paralelo con 13 a 15. Conviene cerrarla después de 14, para anotar el resultado de la validación del respaldo del índice.

## Para qué
Que `docs/investigacion.md` y las skills queden coherentes con la decisión tomada: MSCI Merval desde Rava con respaldo en data912; GGAL, YPFD y PAMP desde data912; sin Yahoo ni BYMADATA.

## Qué tiene que hacer

### A. `docs/investigacion.md`
Hoy ya menciona Rava y data912 (verificados el 18/11/2026), pero también Yahoo como respaldo, y no define el respaldo del índice. Ajustar estos puntos (los números de línea son los de la lectura del 18/11/2026):
1. **TL;DR, viñeta "Indicadores" (línea 8):** cambiar "data912 (con Yahoo `.BA` de respaldo) para las acciones" por "data912 para las acciones (y como respaldo del índice si Rava falla)".
2. **Tabla de indicadores, fila MSCI Merval (línea 48):** agregar que el cierre se valida contra la fecha de la URL, que el código retrocede hasta 7 días buscando el último día con página, que el formato es "81.794 puntos", y el respaldo data912 (endpoint a confirmar, ver spec 14). Mantener "Rava lo titula MERVAL: el nombre MSCI Merval lo pone el código".
3. **Tabla, fila Acciones líderes (línea 49):** aclarar que se toma la última fila con `date` menor o igual a ayer y que el valor es `c` en pesos, formateado `$ 4.770,00`.
4. **Tabla, fila Respaldo de acciones, Yahoo (línea 50):** pasar a "No se usa (decisión del 18/11/2026)". Dejar los datos de la prueba (qué anda y qué no con `^MERV` y `MMSCI.BA`) como antecedente, no como parte del flujo.
5. **Recomendaciones, punto 3 de indicadores (línea 93):** reescribir: MSCI Merval desde Rava (JSON-LD), respaldo data912 si Rava falla o no trae dato válido; GGAL, YPFD y PAMP desde data912 `/historical/stocks/{ticker}` con la última fila con `date` menor o igual a ayer. Sin Yahoo. Si ninguna fuente responde o la fecha no es la del último día hábil, "sin dato".
6. **Caveats, líneas 124 y 125:** sacar "con Yahoo `.BA` de respaldo"; reemplazar la línea 125 (que habla de "antes de cambiar el código") por una nota de qué endpoint de data912 resultó válido para el índice, o que no existe y el respaldo está desactivado (copiar el resultado de la validación de la spec 14).
7. **Sección nueva corta "Formato y controles de acciones"** (dentro de Indicadores, antes de "Formato"): lista de controles anti-errores propios de estas fuentes:
   - Valor numérico mayor que 0; fecha válida y no futura.
   - En Rava, la fecha del texto del JSON-LD coincide con la de la URL.
   - Retroceso de hasta 7 días en Rava; si se agota, respaldo.
   - Desactualizado si el dato supera 1 día hábil; mostrar siempre la fecha del dato y no la de la consulta.
   - Copia local en `datos/acciones.json`, 3 horas, y una consulta fallida no se guarda como vigente.
   - Formato: acciones `$ 1.234,50`; índice `81.794 puntos`.
   - Sin dato antes que dato dudoso. Nunca un valor viejo sin marcarlo.
8. **Línea 3 (resumen introductorio):** cambiar "BYMA para el Merval" por "Rava para el MSCI Merval y data912 para las acciones". Es la única mención que sigue hablando de BYMA como fuente vigente.
9. La fila tachada de BYMADATA (línea 51) se deja como está.

### B. Skills en `.claude/skills/`
Leídas el 18/11/2026. Ninguna menciona la fuente de las acciones (Rava, data912, BYMADATA, Yahoo): no hay nada que corregir de fuente. Ninguna decide el "sin dato": el único lugar que lo nombra es `resumen-diario`, para prohibirle escribirlo. Lo único que conviene ajustar es que el MSCI Merval (un índice en puntos, que hoy no está nombrado en las listas de "cifras de indicadores") quede dentro de lo que el modelo no puede escribir.

1. **`resumen-diario/SKILL.md`**
   - Sección "Indicadores", línea 31: "El dólar, el riesgo país, las reservas y las acciones" pasa a "el dólar, el riesgo país, las reservas, el MSCI Merval y las acciones".
   - Línea 33: "Si una nota trae una cifra de dólar, riesgo país, reservas, acciones o inflación" pasa a incluir "MSCI Merval" (y puntos del índice).
   - Línea 98: "No pongas indicadores, ni cifras de indicadores, ni tablas." Agregar "(incluidos el MSCI Merval y las acciones)".
   - No cambiar: la regla de nombre vigente de la línea 82 (MSCI Merval, no "S&P Merval"), la línea 99 ("No escribas 'sin dato'") ni las reglas de largo (el N ya incluye lo que muestre la página).
2. **`corrector/SKILL.md`**
   - Punto 3 (línea 14): "El resumen no puede traer cifras de dólar, riesgo país, reservas ni acciones" pasa a "...reservas, MSCI Merval (puntos o variaciones) ni acciones".
   - No cambiar nada más (no revisa nombres vigentes ni "sin dato": lo hace el código).
3. **`preguntas-nota/SKILL.md`**
   - Línea 16: "No des cifras de indicadores (dólar, riesgo país, reservas, acciones) que no estén en la nota." Agregar "MSCI Merval" a la lista.
   - No cambiar nada más.
4. Ninguna skill debe nombrar Rava, data912 ni los tickers: las fuentes viven en la investigación y en el código, no en las instrucciones del modelo.

## Fuera de alcance
Cambios de código Python, cambios de estructura, largo o estilo de las skills, `docs/plan.md` (ver preguntas abiertas en `specs/README.md`).

## Archivos que toca
- `docs/investigacion.md`
- `.claude/skills/resumen-diario/SKILL.md`
- `.claude/skills/corrector/SKILL.md`
- `.claude/skills/preguntas-nota/SKILL.md`

## Criterios de aceptación
- [x] `docs/investigacion.md` ya no menciona Yahoo como parte del flujo ni BYMA como fuente vigente del Merval.
- [x] La investigación dice Rava como principal y data912 como respaldo del índice, y data912 para GGAL, YPFD y PAMP.
- [x] Está anotado el resultado de la validación del endpoint del índice en data912 (o que no existe).
- [x] La investigación trae la lista de controles de acciones y el formato (`$ 1.234,50` y `81.794 puntos`).
- [x] Las tres skills nombran el MSCI Merval en la lista de cifras que el modelo no puede escribir o dar.
- [x] Ninguna skill menciona Rava, data912 ni Yahoo.
- [x] No cambió nada de las reglas de largo, orden, nombres vigentes ni formato de nota.
- [x] Todo sigue en español rioplatense.

## Cómo probarlo
1. Buscar a mano en `docs/investigacion.md` las palabras "Yahoo" y "BYMA": solo debe quedar Yahoo como antecedente descartado y BYMADATA tachada.
2. Buscar "Merval" en las tres skills: aparece en `resumen-diario`, `corrector` y `preguntas-nota` dentro de las listas de cifras prohibidas.
3. Buscar "Rava" y "data912" en `.claude/skills/`: no hay ninguna aparición.
4. Preparar un resumen de punta a punta: sigue entre 550 y 650 palabras, sin cifras de índice ni acciones, y el corrector responde OK.
5. Preguntar en la caja de preguntas por una nota "¿a cuánto cerró el Merval?": responde "La nota no dice eso." (si la nota no lo trae).

## Notas de implementación
- `docs/investigacion.md`: aplicados los 9 puntos. Cambio respecto de la spec: el respaldo del índice en data912 quedó **desactivado** (probado el 18/11/2026: `MERV` y `MMSCI` devuelven "no tengo ese ticker" y `/live/arg_stocks` no incluye el índice). Por eso el Merval es solo Rava y, si falla, "sin dato"; el TL;DR, la tabla, las recomendaciones, los controles y los Caveats lo dicen así. Yahoo queda solo como antecedente descartado.
- Skills: `resumen-diario` (3 líneas), `corrector` (punto 3) y `preguntas-nota` (línea 16) nombran el MSCI Merval. Ninguna menciona Rava, data912 ni Yahoo.
- `docs/plan.md`: se actualizó la sección "Riesgos" por pedido expreso y según la decisión 7 de `specs/README.md` (la spec la dejaba fuera de alcance).
- Sin probar: los pasos 4 y 5 de "Cómo probarlo" (resumen de punta a punta y pregunta por el Merval), que requieren correr `claude -p`. Los criterios de aceptación tildados se verificaron leyendo y buscando con grep, no corriendo la app.
