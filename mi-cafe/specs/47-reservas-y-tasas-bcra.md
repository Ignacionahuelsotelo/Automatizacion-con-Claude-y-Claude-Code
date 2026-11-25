# 47 - Reservas elegibles y tasas del BCRA v4.0

**Estado:** hecha

## Depende de
46-dolar-mayorista-tarjeta-cripto (grupos nuevos de indicadores y fuera de la cuenta de palabras).

## Para qué
Las reservas se traen siempre (no tienen preferencia propia) y no hay tasas de interés. Que las reservas sean elegibles y sumar tasas de referencia del BCRA (BADLAR, TAMAR, plazo fijo a 30 días) y el tipo de cambio A3500. Todo sale de la API de Estadísticas Monetarias v4.0 (la v3 está dada de baja), sin suponer que los ids de la v3 siguen valiendo.

## Qué tiene que hacer
1. **Paso 0, verificación contra la API real (obligatorio antes de escribir código):** consultar el catálogo `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias` y buscar a mano el `idVariable` de cada serie por su descripción: reservas internacionales (hoy 1, a confirmar), BADLAR en pesos de bancos privados, TAMAR en pesos de bancos privados, tasa de plazo fijo a 30 días y tipo de cambio de referencia Comunicación A 3500. Después consultar `.../monetarias/{id}` de cada una y mirar el formato (`results[0].detalle`, `fecha`, `valor`), la unidad (% nominal anual, millones de US$, pesos por dólar) y la última fecha informada. Anotar en `docs/investigacion.md`, con la fecha de la prueba, id, descripción exacta del catálogo, unidad y última fecha de cada una. Si alguna serie no aparece en el catálogo, no se agrega y se anota en las preguntas abiertas.
2. **Ids en `config.py`:** los ids verificados se fijan como constantes (por ejemplo `BCRA_IDS = {"reservas": 1, "badlar": ..., "tamar": ..., "plazo_fijo_30": ..., "a3500": ...}`) y `URL_BCRA_VARIABLE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}"`. Ningún id queda escrito en `indicadores.py`. `URL_RESERVAS` se reemplaza por la plantilla (o se arma desde ella). Un test de `tests/test_config.py` verifica que los ids son enteros positivos y sin repetir, pero no llama a la red.
3. **Reservas elegibles:** nueva preferencia `"reservas"` en `micafe/almacen/preferencias.py` (`INDICADORES`). `indicadores.obtener` agrega las reservas solo si `"reservas"` está en `elegidos`. `por_defecto()` la incluye; un `preferencias.json` viejo sin `reservas` se lee igual, **y para no cambiarle el resumen** se interpreta como tildada solo cuando el archivo es de la versión vieja (documentar la regla en la migración de la spec 49; mientras esa spec no esté, la lectura de un archivo viejo agrega `reservas` por defecto). Pendiente decisión en preguntas abiertas si se prefiere dejarla destildada.
4. **Grupo nuevo `tasas`:** BADLAR, TAMAR y plazo fijo a 30 días con `grupo: "tasas"`, nombre para mostrar claro ("BADLAR (bancos privados)", "TAMAR (bancos privados)", "Plazo fijo a 30 días"). Nueva preferencia `"tasas"` en `INDICADORES`. El **A3500** se muestra dentro del grupo `dolar_otros` (es un tipo de cambio; nombre "Dólar A3500 (referencia BCRA)") y por eso aparece o no con esa preferencia.
5. **Formato:**
   - Tasas: `32,50 % TNA` (coma decimal, dos decimales, espacio antes del `%` y la sigla `TNA`; usa `utilidades.formatear_numero` como el resto).
   - A3500: `$ 1.234,50` (como los dólares, sin compra: solo valor).
   - Reservas: igual que hoy (`US$ 40.123,00 millones`, con la leyenda "cifra provisoria" en el nombre).
6. **Última fila por fecha:** de cada `detalle` se toma la fila con la **fecha más reciente** (no la primera), ignorando filas con fecha o valor inválido, como hace hoy `_reservas_ultimo`. Se generaliza en una sola función `_ultimo_de_serie(respuesta)` que usan reservas, tasas y A3500.
7. **Desactualizado:** si el dato es de más de 1 día hábil respecto de hoy (como los demás indicadores diarios); se muestra siempre la fecha del dato, no la de la consulta. Un dato con fecha futura se descarta ("sin dato").
8. **Fallas:** cada serie se consulta por separado; si una falla (red, 4xx, JSON roto, sin filas) ese indicador queda en "sin dato" y se agrega el aviso en español por fuente que ya existe ("No se pudo consultar BCRA: ..."); las demás siguen. Un aviso por fuente, no uno por serie (una sola frase si fallan varias).
9. **Cuántas consultas:** hasta 5 pedidos al BCRA por armado (reservas, tres tasas y A3500) y solo de los grupos elegidos. El BCRA tiene control de tráfico por IP y máximo de 3.000 filas por consulta; se pide el último tramo (por ejemplo con `limit` o `desde`, si la API lo permite; verificarlo en el paso 0) para no bajar series largas. Se reutilizan las consultas en paralelo con `ThreadPoolExecutor` y `config.HILOS_FEEDS` solo si hace falta; si no, de a una (decisión del paso 0 según tiempos medidos).
10. **Copia local:** el BCRA no pide límite de 3 horas, pero se guarda la copia de cada serie con su clave en `datos/indicadores.json` (como el resto) para poder mostrar el dato si la consulta falla, marcándolo desactivado si es viejo (regla de CLAUDE.md: nunca un valor viejo sin marcarlo). Si hoy la copia solo se usa en ArgentinaDatos, se deja igual y se anota; no se amplía el alcance.
11. **Prompt y skills:** las cifras de tasas y A3500 se suman a la lista de cifras prohibidas para el modelo (en las skills y en el corrector).
12. `FUENTE_BCRA` queda como está ("BCRA, Estadísticas Monetarias v4.0 https://www.bcra.gob.ar").

## Fuera de alcance
Inflación y UVA (48); otras variables del BCRA (base monetaria, etc.); gráficos o historial de tasas; scraping del BCRA; la pantalla de preferencias (50) y el esquema v2 (49).

## Archivos que toca
- `micafe/config.py` (ids, URL, fuente)
- `micafe/fuentes/indicadores.py`
- `micafe/almacen/preferencias.py`
- `micafe/dominio/servicio.py` (si arma los indicadores elegidos)
- `.claude/skills/resumen-diario/SKILL.md`, `.claude/skills/corrector/SKILL.md`
- `docs/investigacion.md`
- `tests/test_indicadores.py`, `tests/test_config.py`, `tests/test_preferencias.py`, fixtures nuevos de series del BCRA en `tests/fixtures/`

## Criterios de aceptación
- [x] `docs/investigacion.md` tiene la tabla de ids verificados contra el catálogo real, con fecha de la prueba y unidad, y `config.py` usa esos ids.
- [x] Sin `"reservas"` en las preferencias, no se consulta ni se muestra; con ella, se muestran como hoy.
- [x] Con `"tasas"` tildada aparecen BADLAR, TAMAR y plazo fijo a 30 días con formato `32,50 % TNA`, fecha y fuente BCRA.
- [x] El A3500 aparece con `$ 1.234,50` dentro de `dolar_otros`.
- [x] Si la serie trae filas desordenadas, se usa la de fecha más reciente.
- [x] Un dato de hace más de 1 día hábil se muestra con su fecha y "Desactualizado"; uno de fecha futura es "sin dato".
- [x] Si falla una serie (5xx, JSON roto), esa queda "sin dato" con un aviso en español y las demás se muestran.
- [x] Nunca hay más de 5 pedidos al BCRA por armado, y ninguno si no están tildados reservas, tasas ni `dolar_otros`.
- [x] Ningún id del BCRA está escrito fuera de `config.py`.
- [x] `python3 -m unittest discover -s tests -t .` pasa.
- [ ] `python3 servidor.py` arranca (no verificado: el puerto 8000 ya estaba ocupado por otro servidor; el módulo importa bien).

## Tests (unittest, sin red ni `claude`)
- `test_indicadores.py` con fixtures de cada serie (y variantes: filas desordenadas, vacía, valor no numérico, fecha futura, sin `results`, HTTP 500, JSON roto): última fila por fecha, formato `% TNA`, `$` del A3500, desactualizado con `ahora` fijo (viernes a lunes, feriado fuera de alcance), un aviso por fuente, cantidad de pedidos según preferencias (contador en un `pedir_json` falso).
- `test_config.py`: ids enteros, positivos y sin repetir; la plantilla de URL tiene `{id}`.
- `test_preferencias.py`: `reservas` y `tasas` válidas; archivo viejo.

## Cómo probarlo
1. Paso 0 a mano: `curl -s https://api.bcra.gob.ar/estadisticas/v4.0/monetarias | python3 -m json.tool | grep -i -B2 -A4 badlar` (y análogo para TAMAR, plazo fijo, A3500, reservas); luego `curl -s .../monetarias/{id}` de cada una. Anotar todo en `docs/investigacion.md`.
2. Tests: `python3 -m unittest discover -s tests -t .`.
3. `python3 servidor.py`, preparar el resumen con "Tasas" tildada: se ven las tres tasas con `% TNA` y la fecha del dato.
4. Destildar "Reservas": no aparece en el resumen ni hay pedido de red a esa serie (ver la consola con `MICAFE_LOG=DEBUG`).
5. Cortar la red: cada serie dice "sin dato" y hay un solo aviso del BCRA.

## Notas de implementación
- Paso 0 hecho el 24/11/2026: ids 1 (reservas), 7 (BADLAR), 44 (TAMAR), 1207 (plazo fijo 30 días) y 5 (tipo de cambio mayorista de referencia, A3500); tabla en `docs/investigacion.md`. No hubo error de certificado. Ninguna serie faltó.
- `config.py`: `BCRA_IDS` y `URL_BCRA_VARIABLE` (con `?limit=10`); se sacó `URL_RESERVAS`. Fixtures nuevos `bcra_tasa.json` (filas desordenadas) y `bcra_a3500.json`.
- `indicadores.py`: `_ultimo_de_serie(respuesta, hoy)` reemplaza a `_reservas_ultimo` y descarta filas de fecha futura; `_serie_bcra` arma cada indicador. Las series se piden de a una (sin hilos). Un solo aviso del BCRA aunque fallen varias series. Clave de copia local `bcra_{serie}`; la copia solo se escribe, igual que antes (no se usa como respaldo; no se amplió el alcance).
- Preguntas abiertas resueltas por la opción simple: agrupación propuesta (tasas en `tasas`, A3500 en `dolar_otros` con clave `dolar_a3500`); `reservas` y `tasas` son preferencias; `por_defecto()` las incluye.
- Migración: un `preferencias.json` sin clave `"version"` se lee con `reservas` tildada. `guardar` escribe `"version": 2` en disco (no vuelve en lo leído), así que quien destilda reservas después de esta spec no la recupera sola. La spec 49 puede reemplazar este marcador por su esquema v2.
- Skills y corrector: se sumaron A3500 y tasas a las cifras prohibidas. `app.js` no se tocó (los checkboxes salen de `opciones.indicadores`).
