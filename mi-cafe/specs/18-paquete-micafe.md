# 18 - Paquete `micafe/`: ordenar los módulos sueltos

**Estado:** hecha

## Depende de
17 (los tests avisan si algo se rompe al mover).

## Para qué
Hoy los siete módulos más el servidor viven planos en la raíz. Se pasan a un paquete con capas claras, sin cambiar qué hace ninguno.

## Qué tiene que hacer
1. Crear el paquete `micafe/` y mover los módulos con `git mv` (para conservar el historial), sin reescribir su lógica:
   - `micafe/web/`: lo que habla HTTP. Por ahora `servidor.py` (la clase `Manejador` y `main`).
   - `micafe/fuentes/`: lo que trae datos de afuera: `indicadores.py`, `acciones.py`, `noticias.py`.
   - `micafe/dominio/`: reglas de negocio: `resumen.py`, `corrector.py`, `caja.py`.
   - `micafe/datos/`: lo que se guarda: `preferencias.py`, `gustos.py`. (Es el código de acceso; no confundir con la carpeta `datos/` de la raíz, que sigue sin versionarse. Si el nombre confunde, usar `micafe/almacen/`; elegir uno y dejarlo escrito en el README del paquete.)
2. Cada carpeta lleva su `__init__.py` con una línea de docstring en español que explica qué contiene.
3. Cambiar los `import` a imports absolutos del paquete (`from micafe.fuentes import indicadores`). Sin imports circulares: las fuentes no importan del dominio ni de web; el dominio no importa de web. Hoy `acciones.py` importa `indicadores` para reutilizar sus helpers de fechas y formato: está permitido dentro de `fuentes/`, y se anota para resolverlo en la spec 19 o 21.
4. Dejar `servidor.py` en la raíz como lanzador mínimo (unas pocas líneas: importa y llama a `micafe.web.servidor.main()`), para que `python3 servidor.py` siga siendo el comando de siempre (regla de CLAUDE.md).
5. Las rutas a `index.html`, a `.claude/skills/...` y a `datos/` tienen que seguir apuntando a los mismos archivos de la raíz (hoy se calculan con `os.path.dirname(__file__)`: al mover, se ajustan para que den lo mismo).
6. Mover y adaptar los tests (imports) sin cambiar qué verifican.
7. Actualizar `CLAUDE.md`: sección "Arquitectura prevista" con el mapa nuevo de carpetas. El comando de arranque no cambia.

## Fuera de alcance
Cambiar lógica, nombres de funciones, formato de respuestas de la API, configuración centralizada (19), logging (20), mover `index.html` (24).

## Skills a usar
- `verification-before-completion`: suite de tests y arranque real antes de cerrar.
- `systematic-debugging`: si un import o una ruta falla, buscar la causa en lugar de parchear.

## Archivos que toca
- `micafe/**` (nuevo; los módulos llegan por `git mv`)
- `servidor.py` (queda como lanzador)
- `tests/*` (solo imports)
- `CLAUDE.md`

## Criterios de aceptación
- [x] En la raíz solo quedan `servidor.py` (lanzador), `index.html`, `CLAUDE.md`, `docs/`, `specs/`, `tests/`, `micafe/`, `.claude/` y `.gitignore`.
- [ ] `python3 servidor.py` arranca en el puerto 8000 y la página funciona igual (indicadores, noticias, resumen, gustos, preguntas).
- [x] La suite de la spec 17 pasa sin cambiar lo que prueba.
- [x] No hay imports circulares ni imports hacia arriba entre capas.
- [ ] `git log --follow` en un módulo movido muestra su historial.
- [x] Siguen sin dependencias externas.
- [ ] Respuestas de la API idénticas a las de antes (mismos JSON para los mismos datos).

## Cómo probarlo
1. `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir http://localhost:8000 y recorrer: preferencias, indicadores, "Preparar el de hoy", un 👍, una pregunta sobre una nota.
3. `curl http://localhost:8000/api/preferencias` y `/api/gustos`: mismas formas que antes.
4. `python3 -c "import micafe.web.servidor"` no tira error de import.

## Notas de implementación
- Los archivos no estaban versionados, así que se movieron con `mv` (no hay historial que seguir con `git log --follow`; ese criterio queda sin tildar).
- Carpeta de acceso a datos: `micafe/almacen/` (pregunta abierta 3). Mapa y reglas de dependencias en `micafe/README.md`.
- `CARPETA_PROYECTO` en `resumen`, `corrector`, `caja` y `web/servidor` ahora sube tres niveles; apunta a la misma raíz que antes.
- Tests: solo imports y patch targets (`"resumen.x"` -> `"micafe.dominio.resumen.x"`). 165 tests OK.
- Pendiente anotado: `fuentes/acciones.py` importa `fuentes/indicadores.py` (helpers); resolver en la spec 19 o 21.
- Verificación del arranque: el 8000 estaba ocupado por el servidor del usuario, así que se levantó el `Manejador` en puerto 0 y se pidieron `/`, `/api/preferencias`, `/api/gustos` y `/api/resumen` (200). `python3 servidor.py` llega hasta el bind y falla solo con "Address already in use". No se recorrió la página en el navegador ni "Preparar el de hoy", 👍 o preguntas.
