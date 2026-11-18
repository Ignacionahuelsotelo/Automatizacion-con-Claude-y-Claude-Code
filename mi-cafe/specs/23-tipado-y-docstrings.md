# 23 - Tipado y docstrings

**Estado:** hecha

## Depende de
22 (conviene tipar cuando la estructura ya es la definitiva).

## Para qué
Los módulos pasan diccionarios sueltos de mano en mano (indicador, nota, resumen, voto) y los docstrings son desparejos. Se documentan las formas de datos y se agregan anotaciones de tipos, sin cambiar el comportamiento.

## Qué tiene que hacer
1. Agregar anotaciones de tipos a todas las funciones públicas de `micafe/` (parámetros y retorno), usando `typing` y `from __future__ import annotations` de la librería estándar.
2. Definir las formas de datos que circulan, en un módulo `micafe/modelos.py`, con `TypedDict` (o `dataclass` solo donde no cambie el JSON que se guarda ni el que recibe la página): indicador (`nombre`, `valor`, `fecha`, `fuente`, `desactualizado`), nota, resumen guardado, voto, preferencias, respuesta de error. Las claves y los JSON no cambian.
3. Docstrings en español rioplatense en cada módulo, clase y función pública, con una línea de qué hace y, cuando no sea obvio, qué devuelve y qué errores levanta. Los que ya existen se conservan y se ajustan.
4. Dejar un comentario o docstring en los lugares donde vive una regla de `CLAUDE.md` (por ejemplo, "ningún número lo escribe el modelo", formato `$ 1.234,50`, MSCI Merval), indicando de dónde sale la regla.
5. Comprobación con herramientas estándar solamente: `python3 -m compileall micafe` y un test que importe todos los módulos. El chequeo de tipos con `mypy` u otra herramienta externa no se da por aprobado: va a preguntas abiertas.
6. Sin cambios de lógica. Si al tipar aparece un bug, se anota en "Preguntas abiertas" y no se arregla en esta spec.

## Fuera de alcance
Instalar `mypy`, `ruff` o similares, convertir a `dataclass` todo lo que hoy es un diccionario, cambiar JSON guardados, reescribir funciones.

## Skills a usar
- `verification-before-completion`.
- `systematic-debugging` si alguna anotación destapa un comportamiento raro.

## Archivos que toca
- `micafe/**/*.py`
- `micafe/modelos.py` (nuevo)
- `tests/test_importaciones.py` (nuevo)

## Criterios de aceptación
- [x] Toda función pública de `micafe/` tiene tipos y docstring en español.
- [x] `python3 -m compileall micafe` pasa sin errores.
- [x] Los archivos de `datos/` existentes se siguen leyendo igual y la API devuelve los mismos JSON.
- [x] No se instaló ninguna herramienta ni librería.
- [x] La suite pasa (189 tests) y el servidor anda igual (verificado levantando el handler en un puerto libre y pidiendo /, /api/preferencias, /api/gustos y /api/resumen; el 8000 lo ocupa el servidor viejo del usuario y no se tocó).

## Cómo probarlo
1. `python3 -m compileall micafe` y `python3 -m unittest discover -s tests -t .`.
2. Revisar a ojo tres módulos al azar: tipos y docstrings completos.
3. Recorrer la página y preparar un resumen.

## Notas de implementación
- `micafe/modelos.py` (nuevo): `TypedDict` de Indicador, Nota, NotaDeFeed, FuenteRSS, FallaDeFuente, resultados de noticias/indicadores/acciones/Merval, Preferencias, Voto, Chequeo, Revision, ResumenGuardado, AvisosDelResumen, RespuestaDeError y pedido/respuesta de preguntas. Ninguna clave ni JSON cambió; no se usaron `dataclass`.
- Anotaciones con `from __future__ import annotations` en todos los módulos con código; todas las funciones públicas (y la mayoría de las privadas) tienen tipos. Docstrings agregados donde faltaban (`logs.configurar`, `servicio.*`, `Manejador`, `main`, `utilidades.*`, etc.).
- Reglas de `CLAUDE.md` marcadas con su origen en `config.py` (MSCI Merval, 3 horas de ArgentinaDatos, topes), `corrector.py` (nombres vigentes, largo, enlaces), `noticias.py` (ventana), `indicadores.py` (ningún número lo escribe el modelo) y `utilidades.monto` (formato `$ 1.234,50`).
- `tests/test_importaciones.py` (nuevo): importa todos los módulos y exige docstring de módulo. Suite: 189 tests, OK. `python3 -m compileall micafe` sin errores.
- Sin cambios de lógica. No se encontró ningún bug al tipar.

## Preguntas abiertas
- El chequeo de tipos con `mypy` u otra herramienta externa no se hizo ni se da por aprobado (fuera de alcance: no se instala nada). Las anotaciones no están verificadas por un chequeador; solo compilan e importan.
- `Nota` (fecha como texto) y `NotaDeFeed` (fecha como `datetime`) son dos formas distintas de la misma idea; se dejaron separadas porque así circulan hoy.
