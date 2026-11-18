# 21 - Almacén JSON compartido

**Estado:** hecha

## Depende de
20.

## Para qué
Leer y escribir JSON en `datos/` está repetido: `preferencias.py`, `gustos.py`, la copia de `indicadores.py` y `acciones.py`, y `guardar_resumen` / `leer_ultimo_resumen` (que viven dentro de `servidor.py`, donde no corresponden). Se junta la lógica en un solo lugar probado y se saca el guardado de resúmenes del servidor.

## Qué tiene que hacer
1. Crear `micafe/almacen/json_seguro.py` (o similar) con dos funciones: leer un JSON devolviendo un valor por defecto y un aviso si falta o está roto, y escribir de forma atómica (archivo temporal más `os.replace`, como hace hoy `guardar_resumen`), creando la carpeta si no existe.
2. Hacer que preferencias, gustos y las copias de indicadores y acciones usen esas funciones, sin cambiar el formato de sus archivos ni sus avisos. Lo que hoy es una copia de 3 horas sigue igual, y una consulta fallida no se guarda como vigente.
3. Crear `micafe/almacen/resumenes.py` con lo de resúmenes: `guardar` (solo escribe el archivo de la fecha de hoy, `datos/resumenes/AAAA-MM-DD.json`), `leer_ultimo` (saltea archivos rotos o con otra forma) y `leer_previos` (hoy `corrector.leer_resumenes_previos`). `RE_ARCHIVO_RESUMEN` y `CARPETA_RESUMENES` dejan de vivir en `corrector.py`.
4. Los archivos existentes en `datos/` tienen que seguir leyéndose sin migrar nada: mismo nombre, misma forma. Probarlo con copias reales de `datos/` (sin versionarlas).
5. Errores de escritura: `OSError` se convierte en el error de almacenamiento de la spec 20, con el mismo mensaje actual ("Revisá los permisos de la carpeta datos/.").
6. Tests con directorio temporal: escritura atómica (no queda `.tmp`), archivo roto, archivo con otra forma, carpeta sin permisos, fecha de hoy sin pisar otros días.

## Fuera de alcance
Cambiar a SQLite u otro formato, migraciones, tocar el contenido de los JSON, borrar resúmenes viejos.

## Skills a usar
- `verification-before-completion`.
- `systematic-debugging` ante cualquier diferencia entre un archivo viejo y uno nuevo.

## Archivos que toca
- `micafe/almacen/*` (nuevos)
- `micafe/datos` o `almacen` de preferencias y gustos, `fuentes/indicadores.py`, `fuentes/acciones.py`, `dominio/corrector.py`, `web/servidor.py`
- `tests/*`

## Criterios de aceptación
- [x] Hay una sola implementación de lectura tolerante y de escritura atómica.
- [x] `servidor.py` ya no define `guardar_resumen` ni `leer_ultimo_resumen`.
- [x] Con los `datos/` actuales (copia), se lee el mismo último resumen y la misma copia de indicadores; preferencias y gustos reales no existen en `datos/`, se probaron con tests (la página no se miró en un navegador).
- [x] Un JSON roto en cualquier archivo de `datos/` no tira el servidor y se avisa en español.
- [x] Regla intacta: `datos/` sigue en `.gitignore` y no se versiona nada de lo personal.
- [x] La suite pasa.

## Cómo probarlo
1. Copiar `datos/` a un lugar seguro, correr la app y comparar la pantalla antes y después.
2. Romper a mano `datos/gustos.json` (texto basura): la app arranca y avisa.
3. Preparar el resumen de hoy y verificar `datos/resumenes/AAAA-MM-DD.json` sin archivo `.tmp` al lado.
4. `python3 -m unittest discover -s tests -t .`.

## Notas de implementación
- `micafe/almacen/json_seguro.py`: `leer(ruta, por_defecto)` devuelve `(datos, estado)` con estado `None`, `FALTA` o `ROTO` (cada módulo arma su aviso, que no cambió); `escribir` es atómico, crea la carpeta, limpia el `.tmp` si falla y propaga `OSError`.
- `micafe/almacen/resumenes.py`: `guardar`, `leer_ultimo`, `leer_previos` y `RE_ARCHIVO_RESUMEN`; reciben `carpeta` (el servidor pasa `CARPETA_RESUMENES`, así los tests lo siguen parchando).
- La conversión de `OSError` a `ErrorAlmacenamiento` (mismos mensajes) sigue en `servidor.py`, porque agrega los avisos del pedido.
- `corrector.py` ya no tiene `CARPETA_RESUMENES`, `RE_ARCHIVO_RESUMEN` ni `leer_resumenes_previos`; `caja.py` toma la carpeta de `config`.
- Tests nuevos en `tests/test_almacen.py`; se movieron los de resúmenes previos y de guardado. Suite: 178 tests OK.
