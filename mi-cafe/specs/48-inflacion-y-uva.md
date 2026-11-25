# 48 - Inflación mensual e interanual y UVA

**Estado:** hecha

## Depende de
46-dolar-mayorista-tarjeta-cripto (grupos de indicadores y largo sin indicadores). Convive con la 47 (puede hacerse antes o después).

## Para qué
La decisión 1 del 11/11/2026 dejó la inflación fuera de la v1; ahora se suma (decisión aprobada). Mostrar la inflación mensual, la interanual y el valor de la UVA, con su fecha y fuente, sin que el modelo escriba ningún número.

## Qué tiene que hacer
1. **Fuentes (verificar a mano antes de programar, y anotar con fecha en `docs/investigacion.md`):**
   - Inflación mensual: `https://api.argentinadatos.com/v1/finanzas/indices/inflacion` (serie con `fecha` y `valor`, en %).
   - Inflación interanual: `https://api.argentinadatos.com/v1/finanzas/indices/inflacionInteranual`.
   - UVA: verificar si ArgentinaDatos tiene una ruta (por ejemplo `/v1/finanzas/indices/uva`); si no existe o no responde bien, usar la variable de la UVA del BCRA v4.0 (se busca el id en el catálogo `/monetarias`, como en la spec 47, y se fija en `config.py`). Anotar cuál se eligió y por qué; el id nunca va escrito fuera de `config.py`.
2. **Constantes en `micafe/config.py`:** `URL_INFLACION`, `URL_INFLACION_INTERANUAL`, `URL_UVA` (o el id del BCRA), y los nombres de fuente (`FUENTE_ARGENTINADATOS` ya existe; para la UVA del BCRA, `FUENTE_BCRA`).
3. **Cada serie con su clave de copia local y `reutilizar=True`:** claves distintas en `datos/indicadores.json` (`"inflacion"`, `"inflacion_interanual"`, `"uva"`), y se consultan con `_respuesta(..., reutilizar=True)` para respetar la regla de ArgentinaDatos (una consulta cada 3 horas por serie, `config.HORAS_ENTRE_CONSULTAS`). Si la copia es vigente (menos de 3 horas, misma URL) no se consulta; si es vieja, se consulta; si la consulta falla, se registra el motivo y se avisa como hoy. Una falla en una serie no afecta a las otras.
4. **Qué dato se toma:** de cada serie, la fila con la **fecha más reciente** (no la primera ni la última del arreglo), con valor numérico y fecha válida y no futura. La inflación es un porcentaje mensual o interanual; la UVA es un valor en pesos.
5. **Formato (con `utilidades.formatear_numero`):**
   - Inflación mensual: `2,50 % mensual` (el texto exacto del nombre y la unidad se fija en el test y la página lo muestra tal cual).
   - Inflación interanual: `32,50 % interanual`.
   - UVA: `$ 1.234,56`.
   - Sin dato: valor `None` y la página dice "sin dato", como en el resto.
6. **Fecha como mes:** la inflación es mensual, así que su fecha se muestra como **"octubre 2026"** (mes en español, sin día), no `dd/mm/aaaa`. Una función pura `utilidades.mostrar_mes(fecha)` hace la conversión con una lista fija de meses en español (sin `locale`). La UVA muestra su fecha normal (`dd/mm/aaaa`).
7. **Desactualizado:** la inflación está desactualizada si su mes es de **más de 2 meses** respecto del mes de hoy (por ejemplo, con hoy en noviembre 2026, el dato de septiembre ya es desactualizado y el de octubre no); se avisa con "Desactualizado" y la frase habitual en `avisos`. La UVA, que es diaria, usa la regla de siempre (más de 1 día hábil). Hoy el INDEC publica con cerca de un mes de atraso: un dato de octubre en noviembre es normal.
8. **Grupo y preferencia:** `grupo: "inflacion"` para las dos inflaciones y la UVA con `grupo: "uva"`, o los tres en un único grupo `"inflacion"` (se decide acá: mantener un solo grupo `"inflacion"` con los tres indicadores para no llenar la pantalla de Preferencias; queda en preguntas abiertas). Nueva preferencia `"inflacion"` en `almacen/preferencias.py` (`INDICADORES`), por defecto tildada; un archivo viejo sin ella se lee igual y queda destildada.
9. **Modelo:** el modelo nunca escribe estas cifras; se suman a la lista de cifras prohibidas de las skills y del corrector (regla de CLAUDE.md: ningún número lo escribe el modelo).
10. **Docs:** `docs/investigacion.md` (fuentes y formato) y, en la spec 51, `CLAUDE.md` (la decisión 1 del 11/11/2026 en `specs/README.md` queda marcada como reemplazada por esta spec).

## Fuera de alcance
IPC núcleo, EMAE o la serie de datos.gob.ar (otra fuente); proyecciones y expectativas; gráficos o histórico; inflación por rubro; la pantalla de preferencias (50).

## Archivos que toca
- `micafe/config.py`
- `micafe/fuentes/indicadores.py`, `micafe/fuentes/utilidades.py` (`mostrar_mes`)
- `micafe/almacen/preferencias.py`
- `.claude/skills/resumen-diario/SKILL.md`, `.claude/skills/corrector/SKILL.md`
- `docs/investigacion.md`, `specs/README.md` (nota sobre la decisión 1 del 11/11)
- `tests/test_indicadores.py`, `tests/test_utilidades.py`, `tests/test_config.py`, `tests/test_preferencias.py`, fixtures nuevos de las tres series

## Criterios de aceptación
- [x] Con `inflacion` tildada se ven la inflación mensual, la interanual y la UVA con valor, fecha y fuente.
- [x] La fecha de la inflación se ve como "octubre 2026" y la de la UVA como `dd/mm/aaaa`.
- [x] Una inflación de septiembre 2026 con hoy en noviembre 2026 se marca "Desactualizado"; una de octubre no.
- [x] Con una copia de menos de 3 horas no se hace ningún pedido de red a esa serie; con una copia de más de 3 horas sí.
- [x] Una consulta fallida no se guarda como vigente y deja el aviso en español; las otras series siguen.
- [x] Si una serie viene desordenada, se toma la fila de fecha más reciente; una fecha futura se descarta.
- [x] Sin `inflacion` en las preferencias no se pide nada de red de esas series.
- [x] Ningún número de estas series aparece escrito por el modelo (están en la lista de cifras prohibidas).
- [x] `python3 -m unittest discover -s tests -t .` pasa.
- [ ] `python3 servidor.py` arranca (no verificado).

## Tests (unittest, sin red ni `claude`)
- `test_indicadores.py` con `ahora` fijo y un archivo de copia en carpeta temporal: copia vigente (a 2 h 59 min) no consulta, vencida (3 h 1 min) sí consulta, copia con otra URL consulta, falla de red no deja vigente, serie desordenada, valor no numérico, fecha futura, redondeos y formato (`2,50 % mensual`, `$ 1.234,56`), desactualizado a 2 y a 3 meses, un pedido por serie y ninguno si no está tildada.
- `test_utilidades.py`: `mostrar_mes` con los 12 meses y con fecha inválida.
- `test_config.py`: las URLs son `https` y la clave de copia de cada serie es única.
- `test_preferencias.py`: `inflacion` válida y archivo viejo.

## Cómo probarlo
1. Verificar las rutas: `curl -s https://api.argentinadatos.com/v1/finanzas/indices/inflacion | python3 -m json.tool | tail`, igual con `inflacionInteranual` y con la UVA; anotar en `docs/investigacion.md`.
2. Tests: `python3 -m unittest discover -s tests -t .`.
3. `python3 servidor.py`, preparar el resumen: se ve la inflación con "octubre 2026" (o el último mes publicado).
4. Volver a preparar el resumen en menos de 3 horas: en la consola aparece "sale de la copia local" para esas series y `datos/indicadores.json` tiene las claves nuevas.
5. Editar a mano `consultado_en` de una copia a 4 horas atrás: se vuelve a consultar.

## Notas de implementación
- Rutas verificadas el 24/11/2026 (una consulta por ruta): `/inflacion`, `/inflacionInteranual` y `/uva` de ArgentinaDatos responden 200 con listas de `{fecha, valor}`. La UVA existe ahí, así que no se usó el BCRA (su catálogo no tiene el valor de la UVA). Anotado en `docs/investigacion.md`. Los fixtures (`argentinadatos_inflacion.json`, `..._interanual.json`, `..._uva.json`) son recortes con la forma real, desordenados y con fechas futuras a propósito.
- `config.py`: `URL_INFLACION`, `URL_INFLACION_INTERANUAL`, `URL_UVA`; la fuente es `FUENTE_ARGENTINADATOS`. `utilidades`: `mostrar_mes` (devuelve `None` si no es fecha) y `meses_entre`. `indicadores`: `_inflacion_y_uva` y `_ultima_de_lista`; copia local con claves `inflacion`, `inflacion_interanual` y `uva` y `reutilizar=True`. Un solo aviso de ArgentinaDatos aunque fallen varias de las tres series.
- Desvío en la regla de desactualizado: la spec dice "más de 2 meses" pero sus ejemplos y criterios piden que septiembre con hoy en noviembre (2 meses de diferencia) ya sea "Desactualizado" y octubre no. Se siguió el ejemplo: desactualizado si la diferencia de meses calendario es 2 o más.
- Defaults unificados: sin archivo de preferencias, `por_defecto()` tilda todos los indicadores (inflación incluida). Un archivo viejo (sin `version`) migra con `reservas` tildada y con `dolar_otros`, `tasas` e `inflacion` destildados; un archivo guardado desde la spec 47 respeta lo que tenga. No hizo falta tocar la lógica de migración.
- La copia local de la UVA guarda la serie completa tal como la devuelve la API (cientos de KB); no se recortó para no ampliar el alcance.
- Skills `resumen-diario` y `corrector`: inflación (mensual e interanual) y UVA sumadas a las cifras prohibidas. `app.js` no se tocó (los checkboxes salen de `opciones.indicadores`).
- `python3 servidor.py` no se probó arrancando (puerto 8000 posiblemente ocupado); la spec queda con ese criterio sin tildar.
