# 41 - Perfil de gustos

**Estado:** hecha

## Depende de
39-seleccion-por-puntaje y 40-plan-de-secciones.

## Para qué
Hoy a Claude se le pasan los últimos 30 votos 👍/👎 sueltos y solo desempatan. Un voto de hace un mes pesa igual que uno de ayer y el código no aprende nada. Que el código resuma los votos en un perfil (qué temas, medios y términos le gustan a la persona) con peso decreciente en el tiempo, que la selección y el plan lo usen, y que se pueda reiniciar sin borrar nada.

## Qué tiene que hacer
1. Módulo nuevo `micafe/dominio/perfil.py`, **puro**: lee los votos que le pasa `almacen.gustos` (recibe la lista y la fecha de hoy por parámetro; no lee disco ni la hora) y devuelve un `Perfil` (tipo en `modelos.py`) con puntajes por sección, por medio y por término.
2. Cálculo:
   - Cada voto pesa `0,5 ** (días / config.VIDA_MEDIA_GUSTOS_DIAS)` con `VIDA_MEDIA_GUSTOS_DIAS = 14` (👍 positivo, 👎 negativo).
   - Un voto a un **tema** vale `config.MULTIPLICADOR_VOTO_TEMA = 3`.
   - Un voto a una **nota** suma a su sección y a su medio con peso 1 y a los términos de su título con peso `config.PESO_TERMINO_TITULO = 0,5` (términos normalizados como en la spec 39, sin palabras vacías).
   - Todos los puntajes se acotan entre `-config.TOPE_PERFIL` y `+config.TOPE_PERFIL`, con `TOPE_PERFIL = 5`.
   - Los votos con fecha futura o ilegible se ignoran (no rompen).
3. `seleccion.puntuar` y `seleccion.plan_de_secciones` usan el perfil cuando llega (el parámetro `perfil` que dejó la 39): suma el puntaje de medio y de términos al de cada nota y ajusta los pesos de sección del plan. El pedido sigue pesando más que el perfil, y el perfil nunca rehabilita un tema destildado. Los ajustes quedan en `motivos` ("medio que te gusta", "tema que te gusta", "te gustó algo parecido").
4. `micafe/almacen/gustos.py`: campo `reiniciado_en` (fecha ISO) en el archivo. Al reiniciar se guarda la fecha y hora; los votos anteriores a `reiniciado_en` se **ignoran al leer para el perfil, pero no se borran**. Un `gustos.json` viejo, sin ese campo, se lee igual (sin reinicio). Los votos nuevos siguen guardándose como hoy, con el mismo tope de historial; el tope de 30 votos para el prompt deja de usarse y el historial guardado no se recorta más de lo que ya se recortaba.
5. `micafe/dominio/servicio.py` y `micafe/web/servidor.py`:
   - `GET /api/perfil` devuelve el perfil en un formato apto para mostrar: lista de las prioridades principales con su signo y una etiqueta en español (sin números de indicadores), la fecha de `reiniciado_en` si existe y la cantidad de votos que cuentan. Responde 200 aunque no haya votos (listas vacías).
   - `POST /api/perfil/reiniciar` exige un cuerpo `{"confirmar": true}`; sin eso, 400 con mensaje en español: "Confirmá el reinicio para ignorar lo aprendido." (no se usa "borrar" porque los votos no se borran). Responde 200 con el perfil vacío.
   - Los dos son JSON, locales y manejados por el mismo atrapado de `ErrorMiCafe`.
6. En el prompt (`resumen.py`), los votos sueltos se reemplazan por una sección `## Prioridades aprendidas`: las prioridades principales en texto ("te interesa más Economía", "poco interés en el medio X"), sin títulos de notas y con un máximo de líneas. El texto avisa que son preferencias suaves y que el pedido de hoy y el plan van antes.
7. `.claude/skills/resumen-diario/SKILL.md`: la regla de gustos pasa a "usá las prioridades aprendidas solo para desempatar dentro del plan".
8. Privacidad y logs: nunca se loguean votos, títulos ni términos aprendidos; solo cantidades.

## Fuera de alcance
Mostrar el perfil en la página, botón de reiniciar y etiquetas (spec 42); aprendizaje con un modelo; sincronización entre equipos; recortar o borrar el historial de votos.

## Archivos que toca
- `micafe/dominio/perfil.py` (nuevo), `micafe/dominio/seleccion.py`, `micafe/dominio/servicio.py`, `micafe/dominio/resumen.py`
- `micafe/almacen/gustos.py`
- `micafe/web/servidor.py`
- `micafe/config.py`, `micafe/modelos.py`
- `.claude/skills/resumen-diario/SKILL.md`
- `CLAUDE.md` (flujo y carpeta `datos/`, endpoints nuevos)
- `tests/test_perfil.py` (nuevo), `tests/test_gustos.py`, `tests/test_seleccion.py`, `tests/test_servidor.py`, `tests/test_resumen.py`

## Criterios de aceptación
- [x] Un 👍 de hoy pesa 1, uno de hace 14 días pesa 0,5 y uno de hace 28 días 0,25 (tolerancia numérica).
- [x] Un voto a tema vale el triple que el mismo voto a una nota.
- [x] Ningún puntaje del perfil sale del rango -5 a +5 aunque haya cientos de votos.
- [x] Después de reiniciar, los votos anteriores no cuentan (perfil vacío) y siguen en `datos/gustos.json`; los votos posteriores sí cuentan.
- [x] Un `gustos.json` viejo sin `reiniciado_en` se lee sin error.
- [x] `GET /api/perfil` responde 200 (también sin votos); `POST /api/perfil/reiniciar` sin `{"confirmar": true}` responde 400 en español.
- [x] Con un medio muy votado 👍, sus notas suben en la selección frente a otro medio con igual frescura, pero una nota que encaja con el pedido sigue primero.
- [x] El perfil no rehabilita un tema destildado.
- [x] El prompt trae `## Prioridades aprendidas` y ya no trae los votos sueltos.
- [x] Ningún voto, título ni término aparece en el log (test con `assertLogs`; solo se loguean cantidades).
- [x] `python3 -m unittest discover -s tests -t .` pasa (347 tests). `python3 servidor.py` arranca y responde los dos endpoints (probado con curl y datos temporales).

## Tests (unittest, sin red ni `claude`)
`tests/test_perfil.py` con fechas fijas (hoy se pasa como parámetro): decaimiento a 0, 14 y 28 días, multiplicador de tema, términos del título, acotado a +-5, votos futuros ignorados, reinicio, perfil vacío. `test_gustos.py`: `reiniciado_en` y lectura de archivo viejo (con carpeta temporal). `test_servidor.py`: los dos endpoints, con y sin confirmación y con cuerpo mal formado. `test_seleccion.py`: el perfil ordena y el pedido le gana. `test_resumen.py`: el bloque de prioridades.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, votar 👍 varias notas de un medio y tema, `curl http://127.0.0.1:8000/api/perfil` y ver las prioridades.
3. `curl -X POST http://127.0.0.1:8000/api/perfil/reiniciar -d '{}'`: 400. Con `-d '{"confirmar": true}'`: 200 y el perfil vuelve a vacío; `datos/gustos.json` sigue teniendo los votos y ahora `reiniciado_en`.
4. Preparar un resumen después de votar: las notas del medio favorito suben (ver `motivos` en la spec 42).

## Notas de implementación
- `micafe/dominio/perfil.py` (puro): `calcular(votos, hoy, reiniciado_en)`, `prioridades` y `lineas_para_pedido`. Tipo `Perfil` en `modelos.py`; constantes nuevas en `config.py`.
- Un voto exactamente en la fecha de `reiniciado_en` se ignora (`<=`), porque los votos y el reinicio se guardan con precisión de segundos.
- Selección: el aporte del perfil a una nota (0,18 por punto del medio + 0,09 por punto de cada término del título) se acota a +-0,9 (`MAXIMO_PUNTAJE_PERFIL`). Sumado a la frescura (2) queda por debajo de lo mínimo que da el pedido (3, categoría), así que el pedido siempre gana. Motivos: "medio que te gusta" y "te gustó algo parecido".
- Plan: `seleccion.pesos_de_secciones(perfil)` da `1 + 0,2 * puntaje` (mínimo 0,1) y `plan_de_secciones` agrega el motivo "tema que te gusta" a las secciones con peso mayor a 1. El perfil solo suma puntaje: el filtro de temas destildados sigue primero.
- `terminos_de_titulo` vive en `seleccion.py` (normaliza, saca palabras vacías y palabras de menos de 3 letras) y `perfil.py` lo importa, para no crear ciclos.
- `gustos.py`: `leer` sigue devolviendo `(votos, aviso)`; se sumaron `leer_reinicio` y `reiniciar`. `guardar` conserva `reiniciado_en`. Se sacaron `ultimos`, `lineas_para_pedido` y `CANTIDAD_GUSTOS_PARA_CLAUDE` (ya no se usaban); el historial no se recorta.
- API: `GET /api/perfil` devuelve `{"ok", "prioridades": [{tipo, nombre, signo, etiqueta}], "reiniciado_en", "votos_que_cuentan"}` (hasta 8, desde un puntaje de 0,5 en valor absoluto; sin puntajes). `POST /api/perfil/reiniciar` exige `{"confirmar": true}` (cuerpo vacío o sin eso: 400) y devuelve el mismo formato.
- Prompt: `armar_pedido` y `generar` reciben `prioridades` (antes `gustos`); el bloque lleva solo secciones y medios, nunca términos ni títulos.
- Resuelto: el perfil se calcula con `ahora` de `preparar_resumen`, de modo que los tests son determinísticos.
- El servidor se arrancó y se probó con curl contra una carpeta de datos temporal.
