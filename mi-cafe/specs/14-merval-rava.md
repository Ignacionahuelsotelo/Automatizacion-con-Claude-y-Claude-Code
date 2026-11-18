# 14 - MSCI Merval desde Rava, con respaldo en data912

**Estado:** hecha

## Depende de
13-acciones-data912 (usa el mismo módulo `acciones.py`, la misma copia local y el mismo formato de errores).

## Reemplaza a
Los puntos 2, 3 y 6 de `11-acciones.md` en lo que toca a MMSCI (el "sin dato" permanente por falta de fuente). BYMADATA queda descartada.

## Para qué
Mostrar el cierre del MSCI Merval con fecha y fuente, usando Rava como fuente principal y data912 como respaldo si Rava falla.

## Qué tiene que hacer
1. En `acciones.py`, sumar la consulta del índice. Fuente principal: Rava, página histórica por fecha, `https://www.rava.com/cotizaciones/historico/merval/AAAA/MM/DD/` (ej. `/2026/11/17/`). Es scraping, no API: el formato puede cambiar.
2. Empezar por ayer (America/Argentina/Buenos_Aires). Si esa página responde 404 (fin de semana, feriado o día sin rueda), retroceder un día por vez, hasta 7 días como máximo. Cada día es una consulta; entre consulta y consulta, no más de 8 en total por pedido. Si se agotan, pasar al respaldo.
3. De la página, leer el bloque `<script type="application/ld+json">` (FAQPage) con solo librería estándar (`re` y `json`, o `html.parser`). Del texto de la respuesta tomar el cierre y la fecha. Ejemplo de texto: "El MERVAL cerro a 81.794 el 17 de noviembre de 2026". Convertir el número de formato argentino (punto de miles) a número y la fecha a `dd/mm/aaaa`.
4. Validar antes de aceptar: el cierre es numérico y mayor que 0, y la fecha leída del texto coincide con la fecha de la URL pedida. Si no coincide o no se puede leer, esa página no vale (ir al paso 2 con el día anterior o al respaldo, según corresponda; un JSON-LD ausente o ilegible en una página que sí respondió 200 va directo al respaldo).
5. El nombre para mostrar es siempre **MSCI Merval** (nunca "MERVAL" ni "S&P Merval"), aunque Rava lo titule "MERVAL". Lo pone el código.
6. Formato del valor: `81.794 puntos` (punto para miles, sin símbolo `$`, porque es un índice y no un monto). Con decimales: coma (`81.794,50 puntos`). Lo formatea el código.
7. Fuente mostrada: "Rava https://www.rava.com (cierre del índice)" cuando sale de Rava; "data912 https://data912.com" cuando sale del respaldo. La fecha es la del cierre, no la de la consulta.
8. **Respaldo data912.** Si Rava falla o no trae dato válido (sin conexión, timeout, HTTP distinto de 200 o 404 agotados, JSON-LD ilegible, validación fallida), consultar data912 con la misma regla que las acciones (spec 13: última fila con fecha menor o igual a ayer, `c` válido). El endpoint y el ticker del índice en data912 **no están confirmados**. Antes de implementar, verificar a mano cuál existe y dejarlo anotado en las "Notas de implementación". Candidatos a probar, en este orden:
   - `https://data912.com/historical/stocks/MERV`
   - `https://data912.com/historical/stocks/MMSCI`
   - `https://data912.com/live/arg_stocks` (buscar si trae el índice entre los símbolos)
   Si ninguno devuelve una serie diaria del índice con fecha y cierre, el respaldo queda **desactivado**: no se inventa un equivalente (ni se usa un ETF, un CEDEAR ni otra serie distinta del índice) y, si Rava falla, el índice queda en "sin dato".
9. Si el respaldo devuelve un valor, la fuente lo dice ("data912") para que se vea que no vino de Rava, y se agrega un aviso en español (ver spec 15).
10. Si ni Rava ni el respaldo dan dato válido, "sin dato" (con la fuente consultada). Nunca completar con un valor viejo sin marcarlo.
11. Marcar como desactualizado si la fecha tiene más de 1 día hábil de antigüedad (regla de la spec 03).
12. Copia local en el mismo `datos/acciones.json`, clave `merval`: fuente usada, URL, hora de consulta y el dato leído. Si la última consulta exitosa fue hace menos de 3 horas, se usa la copia sin pedir de nuevo (así se cuida a Rava). Una consulta fallida no queda como vigente.
13. Timeout de cada consulta a Rava: 15 segundos. Enviar un `User-Agent` identificable genérico (por ejemplo "MiCafe/1.0 uso personal"). Respetar `robots.txt` (hoy abierto): si cambia a bloquear la ruta, no consultar y tratarlo como falla de Rava.
14. El índice aparece primero entre las acciones y solo si "acciones" está tildada.

## Fuera de alcance
- Avisos en la página, resumen y `CLAUDE.md` (spec 15).
- Variación porcentual, mínimo y máximo del día (aunque el JSON-LD los traiga).
- Tiempo real o cotización intradiaria.
- Yahoo Finance (`^MERV`, `MMSCI.BA`) o BYMADATA como fuentes.

## Archivos que toca
- `acciones.py`
- `servidor.py` (solo si hace falta pasar el índice a la lista; sin reglas nuevas)
- `datos/acciones.json` (se genera en ejecución, no se versiona)

## Criterios de aceptación
- [x] El MSCI Merval muestra valor, fecha y fuente "Rava".
- [x] Los valores coinciden con Rava abierto a mano (verificado el 18/11/2026: 13/11 = 85.096; 17/11 = 81.794).
- [x] Un día sin rueda (por ejemplo un sábado o un feriado) retrocede hasta el último día con página y muestra esa fecha, no la de hoy.
- [x] El nombre mostrado es "MSCI Merval" y en ningún lado aparece "S&P Merval".
- [x] Formato `81.794 puntos`, sin `$`.
- [x] Si la fecha del texto del JSON-LD no coincide con la de la URL, el dato se rechaza.
- [ ] Con Rava caído y respaldo confirmado, muestra el valor de data912 con fuente "data912" y aviso.
- [x] Con Rava caído y respaldo no confirmado o también caído, "sin dato" y el resto de los indicadores se muestra.
- [x] En "Notas de implementación" quedó anotado qué endpoint de data912 se probó para el índice y el resultado (o que no existe).
- [x] Segunda consulta dentro de las 3 horas usa la copia local.
- [x] No más de 8 consultas a Rava por pedido.
- [x] No se agregó ninguna dependencia externa.

## Cómo probarlo
1. Abrir `http://localhost:8000` y comparar el MSCI Merval con `https://www.rava.com/cotizaciones/historico/merval/AAAA/MM/DD/` de la fecha mostrada.
2. Probar un lunes o un día posterior a un feriado: la fecha mostrada tiene que ser el último día hábil con rueda.
3. Cambiar a propósito la URL base de Rava por una mala: tiene que aparecer el valor de data912 (si el respaldo está confirmado) con su aviso, o "sin dato" (si no lo está).
4. Con un HTML de prueba sin bloque JSON-LD (servido a mano o simulado en la función), confirmar que cae al respaldo.
5. Punto a validar en esta spec: abrir en el navegador los endpoints candidatos de data912 del punto 8 y anotar cuál trae el índice (o que ninguno). Hasta que se anote, el respaldo cuenta como no confirmado.
6. Recargar dos veces y confirmar en `datos/acciones.json` que no se volvió a consultar.

## Notas de implementación
- `acciones.py`: nueva `obtener_merval(ruta_copia, ahora)` (devuelve `{"indicador", "avisos"}`). Rava por scraping del FAQPage JSON-LD con `re` y `json`; arranca en ayer y retrocede ante 404 hasta 8 consultas en total (ayer + 7 días). Otro error HTTP, timeout o JSON-LD ilegible/con fecha distinta a la de la URL va directo al respaldo. `servidor.py` ahora usa ese indicador en vez del "sin dato" fijo; queda primero entre las acciones.
- Validado con red real el 18/11/2026: 17/11 = 81.794 y, retrocediendo desde fin de semana (lunes 16 con ayer domingo, o sábado 14), 13/11 = 85.096 con la fecha 13/11/2026. Segunda llamada: 0 consultas (copia en la clave `merval` de `datos/acciones.json`, 3 horas). Rava con URL base mala: 8 consultas y "sin dato". Se simuló JSON-LD con fecha distinta (rechazado) y sin JSON-LD (sin dato). robots.txt de Rava hoy: `Disallow:` vacío; se lee antes de consultar.
- **Respaldo data912 (probado el 18/11/2026):** `/historical/stocks/MERV` y `/historical/stocks/MMSCI` responden HTTP 200 con `{"Error":"Nahh no tengo ese ticker loko"}`; `/live/arg_stocks` trae 97 símbolos y ninguno es el índice (y es en vivo, no serie diaria). **Ningún candidato sirve: el respaldo queda desactivado** (`TICKER_RESPALDO = None`). Si Rava falla, "sin dato". El camino del respaldo está armado pero no se probó con datos reales; el aviso "viene de data912" es de la spec 15.
- Sin tildar de verdad: "Con Rava caído y respaldo confirmado..." (no hay respaldo confirmado, no aplica). Tampoco se probó en el navegador ni con el servidor de la página; se probó el módulo directo, sin tocar el puerto 8000. Si Rava falla, el aviso se devuelve en `avisos` pero todavía no se muestra (spec 15).
- Fecha de corte `<= ayer` y feriados: el retroceso depende de los 404 de Rava; "desactualizado" usa la regla de días hábiles de la spec 03 (sin feriados).
