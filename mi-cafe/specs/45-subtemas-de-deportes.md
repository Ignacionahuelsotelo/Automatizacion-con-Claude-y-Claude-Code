# 45 - Subtemas de Deportes

**Estado:** hecha

## Depende de
44-mas-temas (y por lo tanto 43). Usa la selección por puntaje (39) y el pedido en texto (35).

## Para qué
Deportes es un solo tema, pero a quien le interesa el fútbol argentino no necesariamente le interesa el automovilismo. Dividir Deportes en subtemas (Fútbol argentino, Fútbol internacional, Tenis, Básquet, Automovilismo y Otros), clasificar cada nota y dejar que el pedido ("fútbol argentino") y, más adelante, las preferencias (spec 49) los usen.

## Qué tiene que hacer
1. **Lista y palabras clave en `config.py`:** `SUBTEMAS` (orden fijo: "Fútbol argentino", "Fútbol internacional", "Tenis", "Básquet", "Automovilismo", "Otros") con, para cada uno salvo "Otros", una lista de palabras clave (clubes, torneos, competencias, deportistas conocidos; conjunto inicial a validar, ver pregunta abierta). "Otros" es lo que no encaja en ninguno. `SUBTEMAS` pertenece solo a Deportes; `config.TEMAS` no cambia.
2. **Campo opcional `subtema` en `FUENTES_RSS`:** una fuente puede declarar su subtema (por ejemplo un feed de Olé de tenis). Se agrega al tipo `FuenteRSS` de `modelos.py` como opcional.
3. **Feeds de Olé por deporte, a verificar** (con `curl -sS -A "MiCafe/1.0"` y el diagnóstico de la spec 32, y anotado con fecha en `docs/investigacion.md`): `https://www.ole.com.ar/rss/futbol-primera/`, `.../futbol-internacional/`, `.../tenis/`, `.../basquet/`, `.../automovilismo/`. Solo entran los que pasen (RSS válido, gratis, fecha con zona y link, notas en la ventana). Los que no existan o den 0 notas se descartan y se anota.
4. **Revisar el feed actual de Olé:** `https://www.ole.com.ar/rss/ultimas-noticias/` dio `en_ventana=0` en las pruebas de la fase anterior. La spec exige reprobarlo: si sigue en 0 (o con fechas sin zona horaria, o roto), se reemplaza por los feeds por deporte (que alcanzan para cubrir) o se corrige la URL; si responde bien, queda como feed general sin subtema y clasificado por palabras clave. Escribir en `docs/investigacion.md` qué se decidió y por qué. Olé debe quedar con al menos un feed de Deportes que traiga notas.
5. **Clasificar en `micafe/dominio/seleccion.py` (o `fuentes/noticias.py` si no rompe la regla de dependencias) con una función pura** `subtema_de(nota, fuente_subtema=None)`: primero el `subtema` de la fuente; si no hay, una categoría del RSS (spec 38) que coincida con un subtema o con sus palabras clave; si no, las palabras clave en título y bajada (normalizadas, como el pedido); si nada encaja, "Otros". El desempate si dos subtemas coinciden: el de la fuente, y si no, el primero en el orden de `SUBTEMAS`. Solo se clasifican las notas de la sección Deportes; el resto queda sin subtema.
6. **Se guarda en la nota:** `Nota` (y `NotaDeFeed`) suman `subtema` (texto o ausente); `GET /api/noticias` lo devuelve en las notas de Deportes (campo nuevo, el front viejo lo ignora sin romper).
7. **Pedido:** un pedido "fútbol argentino" o "tenis" ya consigue sinónimos de `SINONIMOS_TEMAS`; ahora además las notas con ese `subtema` suman al puntaje con el motivo `pedido: fútbol argentino (subtema)`. Agregar a `PESOS_PUNTAJE` la clave `"subtema"` (por defecto 5, entre bajada y título; se ajusta midiendo). Una nota que coincida por subtema y por título suma ambos. La clave `TEMA_DE_CLAVE_SINONIMO` cubre los subtemas nuevos para el aviso de Deportes destildado.
8. Por ahora **no** hay preferencias por subtema (la spec 49 las suma) ni cambia el plan de secciones: Deportes sigue siendo una sola sección con sus notas.
9. Los registros de log traen solo conteos (por subtema), nunca títulos.
10. `docs/investigacion.md` y `CLAUDE.md` (se cierra en la 51) quedan anotados con los subtemas y los feeds.

## Fuera de alcance
Subtemas de otros temas; elegir subtemas en la página (50); sumar o restar puntaje por subtema según preferencias (49); más deportes (rugby, Fórmula 1 aparte, etc.); cambiar el plan de secciones.

## Archivos que toca
- `micafe/config.py` (`SUBTEMAS`, `FUENTES_RSS`, `PESOS_PUNTAJE`, `TEMA_DE_CLAVE_SINONIMO`)
- `micafe/modelos.py`
- `micafe/fuentes/noticias.py` y/o `micafe/dominio/seleccion.py`
- `micafe/dominio/servicio.py` (que `GET /api/noticias` devuelva `subtema`)
- `docs/investigacion.md`
- `tests/test_config.py`, `tests/test_noticias.py`, `tests/test_seleccion.py`, `tests/test_servidor.py`, fixtures de Olé en `tests/fixtures/`

## Criterios de aceptación
- [x] `SUBTEMAS` existe en `config.py` en el orden fijo con "Otros" al final y palabras clave en cada uno de los demás.
- [x] Un feed con `subtema` en `FUENTES_RSS` clasifica todas sus notas en ese subtema.
- [x] Una nota sin subtema de fuente se clasifica por categoría o por palabras clave; si nada encaja, queda en "Otros".
- [x] Solo las notas de Deportes llevan `subtema`.
- [x] El feed de Olé "últimas noticias" se reprobó: queda documentado si se mantiene, se corrige o se reemplaza, y Olé aporta notas en la ventana.
- [x] Un pedido "fútbol argentino" sube las notas de ese subtema en "Noticias de ayer" y muestra la etiqueta "Por tu pedido".
- [x] Un pedido "tenis" con Deportes destildado avisa del tema destildado (spec 42).
- [x] `GET /api/noticias` devuelve `subtema` en las notas de Deportes y sigue respondiendo igual para las demás.
- [x] Ningún log trae títulos ni palabras del pedido.
- [x] `python3 -m unittest discover -s tests -t .` pasa y `python3 servidor.py` arranca.

## Tests (unittest, sin red ni `claude`)
- `test_noticias.py` / `test_seleccion.py`: clasificación por fuente, por categoría, por palabra clave en título y en bajada, "Otros", desempate, normalización de tildes y mayúsculas, notas que no son de Deportes sin subtema.
- `test_seleccion.py`: el pedido por subtema suma el peso nuevo; el pedido sigue ganándole al perfil.
- `test_config.py`: `SUBTEMAS` sin repetidos, "Otros" último, cada `subtema` de `FUENTES_RSS` está en `SUBTEMAS`.
- `test_servidor.py`: `/api/noticias` incluye `subtema` solo en Deportes.
- Fixture de Olé (RSS recortado) con notas de varios deportes y fechas con zona.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. A mano, sobre cada URL candidata de Olé: `curl -sS -A "MiCafe/1.0" URL | head` y contar ítems de ayer; anotar en `docs/investigacion.md`.
3. `python3 servidor.py`, tildar Deportes y preparar el resumen: en la consola, un `Feed Olé / Deportes: ... en_ventana=` mayor que 0.
4. Escribir "fútbol argentino" en el pedido: las notas de clubes argentinos van primero con "Por tu pedido".
5. `curl http://127.0.0.1:8000/api/noticias`: las notas de Deportes traen `subtema`.

## Notas de implementación
- **Feeds probados el 24/11/2026** (detalle en `docs/investigacion.md`): `futbol-primera`, `futbol-internacional`, `tenis` y `basquet` responden bien (200, RSS válido, `pubDate` con `+0000`, link) y entran con su `subtema`. `automovilismo` da 404 (y `motor/`, `deportes-motor/`) y se descartó; "Automovilismo" sigue en `SUBTEMAS` y se clasifica por palabras clave.
- **`ultimas-noticias`:** no estaba roto (200, fechas con zona); el `en_ventana=0` es estructural: Olé trae solo 10 ítems de las últimas horas. Se reemplazó por los cuatro feeds por deporte. En esta lectura solo tenis y básquet tenían 2 ítems de ayer cada uno; el fútbol depende de la hora (de mañana puede traer ayer).
- **Dónde vive la clasificación:** `subtema_de` está en `fuentes/noticias.py` (función pura, para que `/api/noticias` y los candidatos lleven el subtema sin romper la regla de dependencias). Se aplica al leer cada feed y solo a notas de sección Deportes. Busca palabra o frase completa sin tildes ni mayúsculas; la categoría del RSS se mira antes que título y bajada y coincide con el nombre del subtema o con sus palabras clave.
- **Pedido:** `seleccion._motivos_de_pedido` suma `PESOS_PUNTAJE["subtema"]` (5) con el motivo `pedido: <término> (subtema)` además de lo que sume el título o la bajada. Se agregaron a `SINONIMOS_TEMAS` y `TEMA_DE_CLAVE_SINONIMO` las claves fútbol internacional, tenis, básquet y automovilismo (el test de config exige que cada clave de `TEMA_DE_CLAVE_SINONIMO` exista en `SINONIMOS_TEMAS`).
- **Log:** una línea `Deportes por subtema: Tenis=2, ...` con solo conteos.
- **Preguntas abiertas:** las palabras clave son el conjunto inicial (sin validar a fondo con volumen); el peso 5 queda por defecto. `GET /api/noticias` devuelve `subtema` solo en Deportes; no se tocó `servicio.py` porque pasa las notas tal cual. `CLAUDE.md` se actualiza en la spec 51.
- No se probó a mano `python3 servidor.py` con una preparación de resumen real ni el pedido en la página; sí los tests (394 OK) y la clasificación sobre los XML reales bajados.
