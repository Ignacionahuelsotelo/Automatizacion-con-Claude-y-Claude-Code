# 13 - Acciones GGAL, YPFD y PAMP desde data912

**Estado:** hecha

## Depende de
03-indicadores, 08-pagina-completa. Reemplaza el punto de fuente de 11-acciones (ver "Reemplaza a").

## Reemplaza a
Los puntos 2, 3 y 6 de `11-acciones.md` y las constantes `FUENTE_ACCIONES` y el valor `None` fijo de `ACCIONES` en `servidor.py` (el "sin dato" permanente). BYMADATA queda descartada.

## Para qué
Que GGAL, YPFD y PAMP muestren su cierre real, con fecha y fuente, usando la fuente gratuita ya aprobada: data912.

## Qué tiene que hacer
1. Crear un módulo nuevo `acciones.py` (solo librería estándar: `urllib`, `json`, `datetime`) con la lógica de las acciones. `servidor.py` solo lo llama.
2. Para cada ticker (`GGAL`, `YPFD`, `PAMP`) pedir `https://data912.com/historical/stocks/{TICKER}`. La respuesta es una lista de filas con `date`, `o`, `h`, `l`, `c`, `v`.
3. Elegir la fila con la fecha más reciente que sea menor o igual a ayer (America/Argentina/Buenos_Aires, decisión 5 del README). El valor es `c` (cierre). Ignorar filas sin `date` válida o con `c` nulo, no numérico o menor o igual a 0.
4. Guardar cada valor con su **fecha** (la de la fila, no la de la consulta) y su **fuente** ("data912 https://data912.com, cierre en pesos").
5. El valor se formatea en el código con `$ 1.234,50`. El modelo no ve ni escribe estos números.
6. Marcar como desactualizado si la fecha del dato tiene más de 1 día hábil de antigüedad (misma regla que la spec 03, mismo helper si ya existe en `indicadores.py`).
7. Si data912 falla (sin conexión, timeout, HTTP distinto de 200, JSON inválido, lista vacía, ninguna fila válida), ese ticker queda en "sin dato" con su fuente; los demás siguen. Mensaje técnico a la consola; la página recibe un aviso en español (ver spec 15).
8. Copia local en `datos/acciones.json` con, por ticker, la URL, la hora de la consulta y la respuesta. Si la última consulta exitosa fue hace menos de 3 horas, se usa la copia. Una consulta fallida **no** se guarda como vigente: se reintenta en el pedido siguiente.
9. Timeout de cada consulta: 15 segundos. Una consulta por ticker, sin paralelismo agresivo (máximo 3 consultas por pedido).
10. Una copia rota o borrada se ignora y se vuelve a consultar, sin tirar el servidor.
11. Reemplazar en `servidor.py` el armado de acciones con valor `None` por una llamada a `acciones.py`. Mantener la regla actual: aparecen solo si "acciones" está en las preferencias.
12. Nombres para mostrar: "Grupo Galicia (GGAL)", "YPF (YPFD)", "Pampa Energía (PAMP)".

## Fuera de alcance
- El MSCI Merval (spec 14).
- Avisos en la página, resumen guardado y `CLAUDE.md` (spec 15).
- Variación porcentual, gráficos históricos, alertas, otras acciones, Yahoo Finance u otra fuente de respaldo para las acciones.
- Elegir las acciones una por una en las preferencias (sigue el checkbox "acciones").

## Archivos que toca
- `acciones.py` (nuevo)
- `servidor.py` (solo reemplazar el armado de acciones y el import)
- `datos/acciones.json` (se genera en ejecución, no se versiona)

## Criterios de aceptación
- [x] GGAL, YPFD y PAMP muestran valor, fecha y fuente.
- [x] La fecha mostrada es la de la fila de data912 y es menor o igual a ayer.
- [ ] Los valores coinciden con `https://data912.com/historical/stocks/{TICKER}` consultado a mano (verificado el 18/11/2026: GGAL 4.770, YPFD 6.040, PAMP 4.290).
- [x] Formato `$ 4.770,00`.
- [x] Con data912 caída, los tres dicen "sin dato" y el resto de los indicadores se muestra.
- [x] Con un solo ticker roto, solo ese queda en "sin dato".
- [x] Una segunda consulta dentro de las 3 horas usa `datos/acciones.json` (la hora de consulta no cambia).
- [x] Una consulta fallida no queda guardada como vigente.
- [x] Una fila con cierre nulo, 0 o negativo se ignora.
- [ ] Sin "acciones" en las preferencias, no se consulta ni se muestra nada.
- [x] No se agregó ninguna dependencia externa.
- [x] `ACCIONES` ya no trae `valor: None` fijo ni `FUENTE_ACCIONES` con BYMADATA.

## Cómo probarlo
1. Con "acciones" tildada, abrir `http://localhost:8000` y comparar los tres valores con la URL de data912 abierta en el navegador.
2. Recargar dos veces seguidas y confirmar en `datos/acciones.json` que la hora de consulta no cambió.
3. Cambiar a propósito la URL de un ticker por una mala: solo ese dice "sin dato".
4. Cortar internet (con la copia borrada): los tres dicen "sin dato" y la consola muestra el error técnico.
5. Corromper `datos/acciones.json` y recargar: el servidor sigue y vuelve a consultar.
6. Destildar "acciones": desaparecen.

## Notas de implementación
- Módulo nuevo `acciones.py`; reutiliza de `indicadores.py` los helpers de fechas, formato, días hábiles y copia local. `servidor.py` solo importa y llama a `acciones.obtener()`.
- `obtener()` devuelve `{"indicadores", "avisos"}`; los avisos todavía no se muestran en la página (spec 15), `servidor.py` los ignora.
- Una respuesta que no sea una lista no vacía (por ejemplo `{"Error": "..."}` para un ticker inexistente) cuenta como falla y no se guarda en `datos/acciones.json`. Si ninguna fila es válida, se descarta la entrada de la copia.
- La fila de hoy se ignora a propósito (regla "<= ayer"): el 18/11/2026 data912 ya traía GGAL 4.770 con fecha 18/11, y la página muestra 4.830 del 17/11. Por eso el criterio de coincidir con 4.770/6.040/4.290 se comprobó contra la fila del 17/11 (GGAL 4.830, YPFD 6.195, PAMP 4.232,50) y no contra esos valores.
- El MSCI Merval sigue "sin dato" en `servidor.py` (constante `MERVAL`, fuente "pendiente de la spec 14") hasta la spec 14.
- No se pudo probar con el servidor real en el puerto 8000 porque ya había otro proceso (PID 24641, código viejo) ocupándolo; se probó con el mismo `Manejador` en el puerto 8765. Hay que reiniciar el servidor para ver los cambios.
- Sin comprobar a mano: la comparación visual en el navegador y el caso "destildar acciones" por la UI (la lógica `if "acciones" not in prefs` quedó igual).
