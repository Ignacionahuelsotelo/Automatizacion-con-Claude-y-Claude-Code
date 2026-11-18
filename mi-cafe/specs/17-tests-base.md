# 17 - Red de seguridad: tests automatizados con unittest

**Estado:** hecha

## Depende de
Nada nuevo (las specs 01 a 15). Es la primera del refactor: tiene que existir antes de mover código, para poder comprobar que el comportamiento no cambia.

## Para qué
Hoy "se prueba a mano". Antes de tocar la estructura hace falta una red de seguridad automática que fije el comportamiento actual (tests de caracterización), sin internet, sin llamar a `claude` y sin tocar `datos/`.

## Qué tiene que hacer
1. Crear la carpeta `tests/` con un `__init__.py` vacío, usando solo `unittest` y `unittest.mock` de la librería estándar (nada de pytest: ver preguntas abiertas en `specs/README.md`).
2. Se corre con `python3 -m unittest discover -s tests -t .` desde la raíz y tiene que terminar en menos de 10 segundos.
3. Ningún test usa red, ni llama a `claude`, ni escribe en `datos/`: las fuentes se reemplazan con `unittest.mock` y las copias locales van a un directorio temporal (`tempfile.TemporaryDirectory`).
4. Guardar ejemplos fijos de respuestas en `tests/fixtures/` (JSON de DolarApi, ArgentinaDatos, BCRA v4.0 y data912, una página de Rava con JSON-LD, un RSS chico). Son datos inventados o recortados, sin nada personal.
5. Tests de lo que ya hace el código, un archivo por módulo actual:
   - `test_indicadores.py`: formato `$ 1.234,50`, brecha calculada, "sin dato" si la fuente falla, copia local con la regla de 3 horas.
   - `test_acciones.py`: última fila con `date` menor o igual a ayer (data912); Rava con la fecha del JSON-LD igual a la de la URL; retroceso de hasta 7 días y 8 consultas; formato `81.794 puntos`; respaldo desactivado; dato desactualizado.
   - `test_noticias.py`: ventana de "ayer" en America/Argentina/Buenos_Aires, lunes de viernes a domingo, descarte de notas sin fecha, tope 3 por medio (5 los lunes), feed caído se descarta y queda el aviso.
   - `test_resumen.py`: `armar_pedido` (notas, tope, gustos, reintento con borrador), `palabras_indicadores`, y errores de `claude` (no está, falla, timeout) con `subprocess` simulado.
   - `test_corrector.py`: enlace en cada nota, repetidas contra los últimos 3 resúmenes, largo 550 a 650, máximo 2 reintentos y aviso visible si no pasa.
   - `test_preferencias.py` y `test_gustos.py`: leer, guardar, validación, archivo roto o ausente, últimos 30 votos.
   - `test_caja.py`: validación del pedido y respuesta con `claude` simulado.
   - `test_servidor.py`: levantar el servidor en un puerto libre (puerto 0) con las fuentes simuladas y probar rutas: `/` 200, ruta inexistente 404, JSON inválido 400, error inesperado 500 con aviso en español, `/api/resumen` GET sin resumen y con resumen.
6. Si un test descubre un bug real del código actual, no se arregla en esta spec: se anota en "Preguntas abiertas" de `specs/README.md` y el test se deja marcado con `@unittest.expectedFailure` y un comentario que explique por qué.
7. Actualizar la línea de "Pruebas" de `CLAUDE.md`: ahora hay tests automáticos con `unittest`; las pruebas manuales de cada spec siguen valiendo para lo que depende de internet y de `claude`.

## Fuera de alcance
Mover o renombrar módulos (spec 18), cambiar código de la app, tests de la página (spec 26), cobertura medida con herramientas externas, pytest u otras dependencias.

## Skills a usar
- `verification-before-completion`: correr la suite completa y mostrar la salida antes de dar la spec por hecha.
- `systematic-debugging`: si un test del comportamiento actual falla, buscar la causa antes de tocar el test o el código.

## Archivos que toca
- `tests/__init__.py`, `tests/test_*.py`, `tests/fixtures/*` (nuevos)
- `CLAUDE.md` (solo la línea de pruebas)
- Ningún `.py` de la app.

## Criterios de aceptación
- [x] `python3 -m unittest discover -s tests -t .` pasa en una máquina sin internet y sin `claude` en el PATH.
- [x] Hay al menos un test por cada regla de `CLAUDE.md` que se pueda comprobar sin red (formato de montos, ventana de ayer, tope por medio, enlace en cada nota, dedupe, largo, "sin dato", nombre MSCI Merval).
- [x] Después de correr la suite, `datos/` no cambió (ni archivos nuevos ni modificados).
- [x] No se instaló nada: solo librería estándar.
- [ ] `python3 servidor.py` sigue andando igual y ningún `.py` de la app cambió. (No tildado: no arranqué el servidor ni abrí la página; solo comprobé que no edité ningún `.py` de la app. Ya hay un servidor corriendo en el puerto 8000.)
- [x] Todo en español rioplatense (nombres de tests, comentarios, mensajes).

## Cómo probarlo
1. Desde la raíz: `python3 -m unittest discover -s tests -t . -v` y comprobar que pasa.
2. Cortar el internet (o desactivar el wifi) y repetir: tiene que pasar igual.
3. `git status` antes y después: `datos/` sin cambios.
4. Romper a propósito una regla (por ejemplo, cambiar el tope de 3 a 4 en una copia) y comprobar que un test falla. Deshacer el cambio.
5. `python3 servidor.py` y abrir http://localhost:8000: la página anda como antes.

## Notas de implementación

- Se creó `tests/` con `__init__.py` vacío, `utiles.py` (ayudas: fixtures, fechas fijas, silenciar consola, armar RSS), `fixtures/` (DolarApi, ArgentinaDatos, BCRA v4.0, data912, página de Rava con JSON-LD y un RSS, todo inventado) y un `test_*.py` por módulo: indicadores, acciones, noticias, resumen, corrector, preferencias, gustos, caja y servidor. Son 165 tests; la suite tarda menos de 1 segundo.
- Comando: `python3 -m unittest discover -s tests -t .` (agregar `-v` para ver cada test).
- Fechas fijas: "hoy" es el miércoles 18/11/2026 12:00 y, para los lunes, el 16/11/2026, ambos en America/Argentina/Buenos_Aires.
- Fuentes simuladas con `unittest.mock` (`_pedir_json`, `_pedir_html`, `leer` de noticias, `shutil.which` y `subprocess.run` de `resumen`). Las copias locales, preferencias, gustos y resúmenes van a `tempfile.TemporaryDirectory`. El servidor de prueba se levanta en el puerto 0 y se le redirigen las constantes `ARCHIVO_*` y `CARPETA_RESUMENES` a una carpeta temporal.
- Todo lo que la app imprime en consola (avisos, trazas, log de pedidos) se silencia durante los tests.
- Verificado: pasa con `claude` fuera del PATH; `datos/` no cambió tras 3 corridas seguidas; cambiando `TOPE_POR_MEDIO` de 3 a 4 fallan 4 tests (se deshizo el cambio).
- No se encontraron bugs reales en el código actual, así que no hay `@unittest.expectedFailure`.
- Observaciones (no son bugs, no se tocaron): `caja.nota_del_resumen` y `corrector.leer_resumenes_previos` toman la carpeta real de `datos/resumenes` como valor por defecto fijado al importar, por eso los tests la reemplazan con `mock` o pasan la carpeta a mano; en `corrector`, cualquier párrafo suelto sin enlace (que no sea apertura ni cierre) se cuenta como nota sin enlace.
- Pendiente de comprobar a mano: cortar el wifi (los tests no hacen red, pero no se probó sin conexión de verdad) y que `python3 servidor.py` siga andando.
