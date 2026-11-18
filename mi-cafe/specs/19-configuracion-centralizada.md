# 19 - Configuración centralizada

**Estado:** hecha

## Depende de
18.

## Para qué
Hoy las constantes están repartidas: el puerto, las rutas de `datos/`, la zona horaria, los timeouts, las URLs y los topes se repiten o se redefinen en cada módulo (`ZONA` se define en `servidor.py` y en `indicadores.py`; `CARPETA_PROYECTO` en `servidor.py` y en `resumen.py`; `TIMEOUT_SEGUNDOS` con valores distintos en varios). Se juntan en un solo lugar.

## Qué tiene que hacer
1. Crear `micafe/config.py` con una única fuente de verdad (constantes simples o una `dataclass` congelada), con comentarios en español que citen la decisión de `specs/README.md` cuando corresponda:
   - Puerto 8000 y host 127.0.0.1 (decisión 4).
   - Zona `America/Argentina/Buenos_Aires` (decisión 5).
   - Carpeta raíz del proyecto y rutas: `datos/`, `datos/preferencias.json`, `datos/gustos.json`, `datos/indicadores.json`, `datos/acciones.json`, `datos/resumenes/`, `.claude/skills/...`, archivos del front.
   - Timeouts: `claude -p` 5 minutos (decisión 13) y los de las fuentes HTTP (hoy 15 segundos en acciones; revisar los otros).
   - Horas entre consultas a ArgentinaDatos y data912 (3).
   - URLs de las fuentes (DolarApi, ArgentinaDatos, BCRA v4.0, data912, Rava, RSS de los medios) y nombres vigentes (MSCI Merval).
   - Topes: 3 notas por medio, 5 los lunes (decisión 14); largo 550 a 650 palabras; reintentos del corrector (2); últimos 3 resúmenes para dedupe; últimos 30 votos de gustos.
2. Los valores no cambian: se copian tal cual están hoy. Si dos módulos tienen valores distintos para lo mismo, se deja el que usa la app en ese punto y se anota la diferencia en "Preguntas abiertas".
3. Permitir sobrescribir solo lo que sirve para pruebas y para correr en otra carpeta, con variables de entorno opcionales y documentadas (por ejemplo `MICAFE_DATOS` para la carpeta de datos). Sin archivos de configuración nuevos ni librerías. El puerto y el host no se sobrescriben: la regla es puerto fijo 8000 y solo 127.0.0.1.
4. Reemplazar las constantes duplicadas en cada módulo por imports de `micafe.config`. Los módulos reciben rutas por parámetro como hoy (los tests siguen pasando rutas temporales).
5. Resolver la dependencia `acciones.py` hacia `indicadores.py` anotada en la spec 18: los helpers compartidos de fechas y formato de montos pasan a un módulo común (`micafe/fuentes/utilidades.py` o `micafe/formato.py`), sin cambiar su comportamiento.
6. Tests: agregar uno que verifique que `config` apunta a las rutas esperadas y que `MICAFE_DATOS` redirige `datos/`.

## Fuera de alcance
Interfaz para editar configuración, archivos `.env`, secretos (la app no usa claves), cambiar cualquier valor actual.

## Skills a usar
- `verification-before-completion`.
- `brainstorming` solo si hay dudas sobre qué se considera configuración y qué es una constante del dominio.

## Archivos que toca
- `micafe/config.py` (nuevo), módulo común de utilidades (nuevo)
- Todos los módulos de `micafe/` (solo sacar constantes)
- `tests/test_config.py` (nuevo)
- `CLAUDE.md` (una línea: dónde está la configuración)

## Criterios de aceptación
- [x] No queda ninguna definición duplicada de `ZONA`, rutas de `datos/`, puerto ni timeouts fuera de `config.py`.
- [x] Los valores efectivos son los mismos que antes (comparar con `git diff`).
- [x] `python3 servidor.py` sigue en 127.0.0.1:8000 (por código: `HOST`/`PUERTO` de `config.py`; no se arrancó porque el puerto 8000 lo ocupa el servidor del usuario).
- [x] Sin `MICAFE_DATOS`, los datos se guardan en `datos/` de la raíz como siempre.
- [x] La suite pasa.
- [x] Regla intacta: el puerto es fijo y solo escucha en 127.0.0.1.

## Cómo probarlo
1. Buscar con `grep` en `micafe/` las palabras `8000`, `Buenos_Aires` y `"datos"`: solo aparecen en `config.py`.
2. `MICAFE_DATOS=/tmp/prueba python3 servidor.py`, guardar una preferencia y comprobar que el archivo está ahí y no en `datos/`.
3. Correr normal y recorrer la página.
4. `python3 -m unittest discover -s tests -t .`.

## Notas de implementación
- `micafe/config.py` junta puerto, host, zona, rutas, timeouts, URLs, nombres, topes y los feeds RSS. Los módulos importan de ahí; donde los tests parchean nombres del módulo (`servidor`, `noticias`, `resumen`, `corrector`, `caja`) se mantuvieron los nombres como alias importados.
- `MICAFE_DATOS` es la única variable de entorno (default idéntico: `datos/` de la raíz). `MICAFE_LOG` es de la spec 20, no se tocó.
- Nuevo `micafe/fuentes/utilidades.py`: helpers de fechas, formato de montos y copia local, sin cambios de comportamiento y con nombres públicos (antes `indicadores._monto`, etc.). `acciones.py` ya no importa `indicadores.py`. Tests de formato ajustados a `utilidades`.
- Se movió `SECCIONES` (estaba idéntica en `noticias.py` y `corrector.py`) y `CANTIDAD_PREVIOS`, `REINTENTOS`, etc. a config.
- Prueba de `MICAFE_DATOS`: servidor en puerto 0 con la variable apuntando a una carpeta temporal; el POST de preferencias creó `preferencias.json` ahí y no en `datos/`. Suite: 168 tests OK (167 y 1 salteado con `MICAFE_DATOS` definida).
- Valores distintos conservados, sin unificar (para "Preguntas abiertas" 4 de `specs/README.md`): timeout HTTP 10 s en indicadores y noticias, 15 s en acciones (data912 y Rava); User-Agent `MiCafe/1.0` (indicadores, noticias, data912) y `MiCafe/1.0 uso personal` (Rava).
