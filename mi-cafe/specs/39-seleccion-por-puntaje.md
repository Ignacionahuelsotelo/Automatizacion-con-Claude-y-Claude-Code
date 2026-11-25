# 39 - Selección de candidatas por puntaje

**Estado:** hecha

## Depende de
37-internacional-como-tema (filtro estricto de temas) y 38-bajada-y-categorias (más texto para comparar).

## Para qué
Hoy las candidatas se cortan solo por fecha, 3 por medio y sección (`micafe/fuentes/noticias.py:186-196`), el pedido del usuario no llega a la selección (`micafe/dominio/servicio.py:146`) ni al corrector (`servicio.py:177-185`) y depende de que Claude lo interprete. Si la persona escribe "fútbol argentino" y una nota de River es más vieja que diez de otros deportes, puede no llegar ni a la lista. Que el código ordene las candidatas con un puntaje explicable y le pase a Claude las mejores.

## Qué tiene que hacer
1. Módulo nuevo `micafe/dominio/seleccion.py` con funciones **puras** (sin red, sin disco, sin `claude`, sin leer la hora del sistema: la fecha llega por parámetro):
   - `terminos_del_pedido(texto) -> list[str]`: normaliza (minúsculas, sin tildes, sin signos), saca palabras vacías ("de", "la", "quiero", "noticias", "sobre", "hoy"…; la lista vive en `config`), expande sinónimos con `config.SINONIMOS_TEMAS` y devuelve términos sin repetidos. Un pedido vacío da `[]`.
   - `puntuar(notas, prefs, terminos, perfil=None) -> list[NotaPuntuada]`: calcula el puntaje de cada nota y sus `motivos` (lista de textos cortos tipo "pedido: river", "frescura", "medio preferido"). `perfil` queda en `None` hasta la spec 41; con `None` no suma nada.
   - `elegir_candidatas(notas, prefs, terminos, perfil=None, tope_por_medio_y_seccion, maximo) -> Seleccion`: descarta las notas de temas destildados, puntúa, ordena de mayor a menor puntaje (empate: más nueva primero, luego orden estable por link), respeta el tope por (medio, sección) y corta en `config.MAXIMO_CANDIDATAS_PARA_CLAUDE = 40`. Devuelve las candidatas, los `motivos` por nota y `pedido_sin_notas`.
2. Un término del pedido "encaja" con una nota si aparece (como palabra, normalizado) en el título, la bajada o las categorías. Peso: título > bajada > categoría (valores en `config.PESOS_PUNTAJE`, junto con frescura y medio). El puntaje del pedido pesa más que cualquier otro factor por defecto, de modo que una nota que encaja con "River" queda primera aunque sea más vieja (dentro de la ventana de "ayer").
3. `config.SINONIMOS_TEMAS`: diccionario de término del pedido a lista de términos equivalentes, por ejemplo `"fútbol argentino"` → liga profesional, AFA, Boca, River, Racing, Independiente, San Lorenzo, Copa Argentina, Primera División, Selección. Se arma con un conjunto inicial razonable para los cinco temas y se puede ampliar a mano; las claves se normalizan al comparar.
4. Subir `config.CANDIDATAS_POR_MEDIO_Y_SECCION` a ~8 (y su variante de lunes en proporción), para que la selección tenga de dónde elegir. `noticias.obtener` sigue aplicando ese tope por fecha, y después `elegir_candidatas` recorta a `MAXIMO_CANDIDATAS_PARA_CLAUDE`. El tope de 3 por medio para el **resumen** no cambia.
5. Un tema destildado **nunca** entra, ni por el pedido ni por sinónimos: el filtro de temas se aplica antes de puntuar. (Decisión aprobada: un pedido sobre un tema destildado no trae nada de ese tema.)
6. `pedido_sin_notas = True` cuando hay términos de pedido y ninguna nota habilitada encaja con ninguno (incluido el caso en que el pedido solo habla de un tema destildado). Esto cierra lo pendiente de `specs/36-pedido-de-noticias-pagina.md:53` en el backend; la página lo muestra en la spec 42. Se guarda en el resumen como `pedido_sin_notas`.
7. `micafe/dominio/servicio.py` pasa el pedido a la selección, antes de armar el prompt, y guarda en el resumen `pedido_sin_notas`. `micafe/dominio/resumen.py` marca con `[pedido]` las notas que encajan, junto con sus motivos, y aclara en el texto que las notas con esa marca son las que se pidieron hoy.
8. El pedido **nunca se loguea**: ni el texto, ni los términos, ni los sinónimos. El log puede decir cuántas notas encajaron.
9. Con pedido vacío o sin términos, la selección se comporta como hoy (frescura y orden por sección) y `pedido_sin_notas` es `False`.

## Fuera de alcance
Plan de cuántas notas por sección (spec 40); perfil de gustos (spec 41, acá solo queda el parámetro `perfil`); mostrar etiquetas o avisos en la página (spec 42); búsqueda difusa, stemming o modelos de lenguaje para puntuar; cambiar la regla de 3 notas por medio en el resumen.

## Archivos que toca
- `micafe/dominio/seleccion.py` (nuevo)
- `micafe/config.py` (`SINONIMOS_TEMAS`, `PESOS_PUNTAJE`, palabras vacías, `CANDIDATAS_POR_MEDIO_Y_SECCION`, `MAXIMO_CANDIDATAS_PARA_CLAUDE`)
- `micafe/modelos.py` (`NotaPuntuada`, `Seleccion`)
- `micafe/dominio/servicio.py`, `micafe/dominio/resumen.py`
- `micafe/fuentes/noticias.py` (solo el tope por medio y sección)
- `.claude/skills/resumen-diario/SKILL.md` (explicar la marca `[pedido]`)
- `CLAUDE.md` (flujo: la selección usa el pedido)
- `tests/test_seleccion.py` (nuevo), `tests/test_servicio.py`, `tests/test_resumen.py`, `tests/test_noticias.py`

## Criterios de aceptación
- [x] Con pedido "fútbol argentino", una nota con "River" en el título o la bajada queda primera aunque sea más vieja que otras de Deportes.
- [x] Sin tildes ni mayúsculas el resultado es el mismo ("FUTBOL Argentino" = "fútbol argentino").
- [x] Un tema destildado nunca aparece en la selección, aunque el pedido lo nombre.
- [x] Cada nota seleccionada trae `motivos` no vacíos cuando suma puntaje por algo.
- [x] Si el pedido no encaja con ninguna nota habilitada, `pedido_sin_notas` es `True` y se guarda en el resumen; con pedido que encaja o sin pedido es `False`.
- [x] La selección tiene como máximo 40 notas y respeta el tope por (medio, sección).
- [x] El prompt marca con `[pedido]` solo las notas que encajan.
- [x] El pedido no aparece en ningún registro del log (test con `assertLogs` y un pedido con texto reconocible).
- [x] Las funciones de `seleccion.py` son deterministas: mismas entradas, misma salida.
- [x] `python3 -m unittest discover -s tests -t .` pasa (296 tests); `python3 servidor.py` no se levantó: solo se comprobó que `micafe.web.servidor` importa.

## Tests (unittest, sin red ni `claude`)
`tests/test_seleccion.py` con notas armadas a mano y fechas fijas:
- normalización de tildes y mayúsculas, palabras vacías, expansión de sinónimos y pedido vacío;
- la nota vieja con "River" gana a una nueva sin relación;
- título pesa más que bajada y bajada más que categoría;
- tema destildado excluido aunque coincida con el pedido;
- `pedido_sin_notas` en los tres casos (encaja, no encaja, pedido de tema destildado);
- tope por (medio, sección) y tope total de 40;
- desempate estable;
- `test_servicio.py`: el pedido llega a la selección y `pedido_sin_notas` queda en el resumen guardado; `test_resumen.py`: la marca `[pedido]`.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, escribir "fútbol argentino" y preparar el resumen: en Deportes aparecen notas de clubes argentinos y las de ese pedido van primero.
3. Pedir "tecnología" con Tecnología destildada: el resumen sale sin Tecnología (el aviso en pantalla llega con la spec 42; mientras tanto se ve `pedido_sin_notas: true` en `datos/resumenes/AAAA-MM-DD.json`).
4. Revisar la consola del servidor: no aparece el texto del pedido.

## Notas de implementación
- `micafe/dominio/seleccion.py` (puro): `terminos_del_pedido`, `puntuar`, `elegir_candidatas`. Tipos `NotaPuntuada` y `Seleccion` en `modelos.py`. `Seleccion` trae `candidatas`, `motivos` (por link, solo las que suman), `encajan` (links) y `pedido_sin_notas`.
- Pesos en `config.PESOS_PUNTAJE`: título 10, bajada 5, categoría 3, frescura hasta 2. Cada término suma una sola vez, por su mejor lugar. Un término del pedido en el título vale más que cualquier frescura.
- Decisión (más simple): la frescura es relativa a la tanda (0 la más vieja, 2 la más nueva), así no hace falta la hora del sistema. No hay "medio preferido" porque las preferencias no tienen medios; `prefs` se usa solo para el filtro de temas y `puntuar` lo recibe reservado.
- Una clave de `SINONIMOS_TEMAS` presente en el pedido suma la frase, sus sinónimos y se consume del texto (así "fútbol argentino" no deja "argentino" suelto). Se cargaron claves para los cinco temas y "fútbol"/"deportes".
- Cupo de candidatas: 8 por medio y sección (13 los lunes). `noticias.obtener` lo sigue aplicando y `elegir_candidatas` lo vuelve a aplicar con el mismo valor (se calcula en `servicio.py` según el tope del día).
- Las notas sin `seccion` (fixtures viejos) no se filtran por tema. El filtro de temas ya se hacía al leer feeds; ahora también al seleccionar.
- Claude y el corrector reciben la misma lista seleccionada (si no, el corrector aceptaría links que Claude nunca vio). La lista "Noticias de ayer" de la página (`/api/noticias`) no cambia.
- `pedido_sin_notas` se guarda siempre (True o False) en el resumen. El log solo dice "encajaron N notas de M candidatas", y solo si hubo términos.
- Tests existentes de `test_noticias.py` y `test_config.py` se ajustaron al cupo nuevo.
- No verificado a mano: pasos 2 a 4 de "Cómo probarlo" (servidor real con `claude`).
