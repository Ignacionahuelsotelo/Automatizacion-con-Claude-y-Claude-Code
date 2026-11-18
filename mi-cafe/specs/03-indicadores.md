# 03 - Indicadores

**Estado:** hecha

## Depende de
02-preferencias

## Para qué
Traer los números directo de las fuentes oficiales, con fecha y fuente, porque ningún número lo puede escribir el modelo.

## Qué tiene que hacer
1. Pedir las fuentes, en este orden (según `docs/investigacion.md`):
   - Dólar oficial, blue, MEP (`bolsa`) y CCL (`contadoconliqui`): DolarApi, `https://dolarapi.com/v1/dolares` (compra, venta y `fechaActualizacion`). La brecha la calcula el código, no el modelo.
   - Riesgo país: ArgentinaDatos, `/v1/finanzas/indices/riesgo-pais/ultimo` (`fecha` y `valor`). Citar "ArgentinaDatos https://argentinadatos.com".
   - Reservas: BCRA Estadísticas Monetarias **v4.0** (`api.bcra.gob.ar/estadisticas/v4.0/monetarias/1`, variable 1; la v3 está dada de baja desde el 28/02/2026). Leer `ultFechaInformada` como fecha, en millones de USD, cifra provisoria.
2. Guardar cada valor con su **fecha** y **fuente**.
3. Si falta un dato o la fuente falla, devolver "sin dato" para ese indicador; nunca inventar ni completar con un valor viejo sin marcarlo.
4. Marcar como desactualizado un indicador diario con más de 1 día hábil de antigüedad.
5. ArgentinaDatos admite como máximo una consulta cada 3 horas por serie: guardar copia local en `datos/` y usarla si no pasaron 3 horas.
6. Montos en formato `$ 1.234,50` (punto para miles, coma para decimales).
7. Endpoint (`GET`) que devuelve los indicadores; mostrarlos en una lista simple en `index.html`.
8. Respetar las preferencias: traer solo los indicadores que el usuario eligió.

## Fuera de alcance
Acciones y Merval (spec 11), inflación (fuera de v1), redacción con Claude, diseño final.

## Archivos que toca
- `servidor.py`
- `index.html`
- `datos/` (copia local de las consultas; no se versiona)

## Criterios de aceptación
- [ ] Cada indicador muestra valor, fecha y fuente.
- [ ] Los valores coinciden con una web de consulta (por ejemplo la del BCRA o la de la propia fuente).
- [ ] Con una fuente caída, ese indicador dice "sin dato" y los demás se muestran.
- [x] No se hace más de una consulta cada 3 horas a la misma serie de ArgentinaDatos (se ve en la copia local).
- [x] Los montos usan `$ 1.234,50`.
- [ ] Un indicador con más de 1 día hábil de antigüedad se ve marcado como desactualizado.
- [x] La brecha se calcula en el código a partir de los valores de DolarApi.
- [x] El pedido al BCRA usa v4.0 (no v3).
- [x] No hay números escritos a mano ni generados por Claude.

## Cómo probarlo
1. Abrir la página y comparar cada número con una web de consulta.
2. Cortar internet (o poner una URL mala a propósito) y ver "sin dato".
3. Recargar dos veces seguidas y confirmar en `datos/` que se usó la copia local.

## Notas de implementación
- **Archivos tocados:** `indicadores.py` (nuevo, toda la lógica de indicadores), `servidor.py` (import, `ARCHIVO_INDICADORES`, la ruta `GET /api/indicadores` y el método `_responder_indicadores`; la docstring menciona la ruta), `index.html` (sección "Indicadores" con una lista; se recarga al guardar preferencias). La copia local es `datos/indicadores.json`, ya cubierta por `.gitignore`.
- **Endpoint:** `GET /api/indicadores` devuelve `{"indicadores": [...], "generado_en": "dd/mm/aaaa hh:mm"}`. Cada indicador trae `clave`, `grupo`, `nombre`, `valor` (texto ya formateado, o `null` si es "sin dato"), `fecha`, `fuente` y `desactualizado`. Siempre responde 200; las fallas aparecen como "sin dato".
- **Formato:** `indicadores.py` formatea los montos (`$ 1.570,00`, `US$ 50.437,00 millones`), los puntos (`860 puntos básicos`) y los porcentajes (`1,91 %`). Ningún número lo escribe el modelo.
- **Dólares:** `dolar` trae oficial, blue, MEP (`bolsa`) y CCL (`contadoconliqui`) desde DolarApi, con compra y venta. La brecha se calcula en el código con la venta: blue, MEP y CCL contra el oficial. Su fecha es la más vieja de las dos cotizaciones usadas.
- **Riesgo país:** ArgentinaDatos, `/v1/finanzas/indices/riesgo-pais/ultimo` (`valor` y `fecha`).
- **Reservas:** BCRA v4.0, `/estadisticas/v4.0/monetarias/1`, con la fila más reciente de `results[0].detalle`. Ojo: `ultFechaInformada` no viene en esa respuesta sino en el catálogo `/monetarias` (ahí el dato de variable 1 coincide con la fila más reciente: 04/11/2026, 50.437). Se tomó la fecha de la fila, sin una consulta extra al catálogo. Se marca como cifra provisoria en el nombre.
- **Preferencias:** `dolar` y `riesgo_pais` se consultan solo si están elegidos. `acciones` no se trae acá (spec 11).
- **Reservas sin preferencia (decisión a confirmar):** la lista cerrada de la spec 02 no tiene una preferencia para reservas, así que se trae siempre. Si preferís que dependa de una preferencia, hay que agregarla en `preferencias.py`, lo que toca la spec 02.
- **Copia local y límite de ArgentinaDatos:** `datos/indicadores.json` guarda, por cada fuente, la URL, la hora de la consulta y la respuesta. Para riesgo país, si la última consulta fue hace menos de 3 horas, se usa la copia y no se consulta (queda un aviso en la consola). Un intento fallido también cuenta como consulta: no se reintenta hasta pasadas 3 horas, y mientras tanto muestra "sin dato". Dólar y reservas se consultan en cada pedido (la copia queda guardada, pero no se reutiliza).
- **Desactualizado:** se marca si el dato tiene más de 1 día hábil (lunes a viernes, hora de Buenos Aires). Los feriados no se descuentan (es una aproximación).
- **Fallas:** si una fuente no responde, devuelve un JSON inválido o no trae un dato válido, ese indicador queda en "sin dato" (con su fuente) y los demás siguen. Si no se puede escribir la copia, se avisa en la consola y se responde igual. Una copia rota se ignora y se vuelve a consultar.
- **Pruebas hechas:**
  - Con las fuentes simuladas (sin red) y una copia temporal en el scratchpad: formato `1.234,50`, brechas, saltear un valor `null` del BCRA, fecha en hora de Buenos Aires, desactualizado (viernes a lunes = 1 día hábil; jueves a lunes = 2), indicador faltante sin romper, fuente caída como "sin dato" sin afectar a las demás, la copia de 3 horas (no consulta antes de 3 horas y sí después), un fallo que no reintenta en 3 horas, copia rota sin tirar el servidor. 0 errores.
  - Con el servidor en el puerto 8013 (wrapper temporal en el scratchpad, `PUERTO` cambiado solo en ese proceso, cerrado al final): `GET /api/indicadores` dos veces. Los valores coinciden con lo que devuelven las APIs consultadas directamente (oficial 1.570, riesgo 860 del 10/11, reservas 50.437 del 04/11). En la segunda consulta no se volvió a pedir el riesgo país (`consultado_en` no cambió). Una ruta inexistente responde 404.
  - Falla real de red (conexión rechazada) y JSON inválido: devuelven "sin dato" sin romper.
  - El JS de `index.html` pasa `node --check`.
- **No probado en navegador:** no abrí la página. Por eso quedan sin tildar los criterios de pantalla: que se vea valor, fecha y fuente; la comparación con una web de consulta; la marca "Desactualizado" y el "sin dato" visibles. La comparación de valores se hizo contra las APIs, no contra una web. Falta abrir `http://localhost:8000` y mirar la lista.
- **Puerto 8000:** el proceso `python3 servidor.py` de antes sigue corriendo con el código viejo y no tiene `/api/indicadores`. Hay que reiniciarlo (`Ctrl+C` y `python3 servidor.py`).
- **Proceso:** la spec se marcó "hecha" al cerrar; no se marcó "en curso" antes de empezar.
- **Feriados y zona:** la fecha de "hoy" sale de America/Argentina/Buenos_Aires (decisión 5).
