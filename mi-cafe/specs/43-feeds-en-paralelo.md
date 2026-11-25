# 43 - Lectura de feeds en paralelo

**Estado:** hecha

## Depende de
Nada. Conviene hacerla antes de la 44 y la 45, que suman feeds (hoy hay 22; con esas specs pueden pasar de 40).

## Para qué
`noticias.obtener` lee los feeds de a uno, con 10 s de timeout cada uno. Con 22 feeds, un par de lentos ya hacen tarde la etapa "Trayendo noticias" y la carga de "Noticias de ayer"; con los feeds de las specs 44 y 45 sería peor. Leerlos a la vez con la librería estándar (`concurrent.futures`), sin cambiar el resultado. Era la pregunta abierta 6 de las specs 28 a 36.

## Qué tiene que hacer
1. En `micafe/config.py`, `HILOS_FEEDS = 6` (cantidad máxima de feeds que se leen a la vez).
2. En `micafe/fuentes/noticias.py`, `obtener` lee los feeds de las secciones activas con `concurrent.futures.ThreadPoolExecutor(max_workers=config.HILOS_FEEDS)`. Cada tarea llama a `leer(url)` y a `notas_del_feed` para un feed y devuelve notas o el error previsto.
3. **Resultado idéntico al secuencial:** los resultados se juntan en el orden de `FUENTES_RSS` (no en el orden en que terminan): `executor.map` o una lista de `Future` recorrida en orden. Por eso `candidatas`, `fallas`, `por_fuente`, el desempate por link repetido ("gana el primer feed en el orden de FUENTES") y las notas devueltas quedan igual que hoy.
4. **Un feed caído no frena a los demás:** las excepciones previstas (`OSError`, `ValueError`, `SyntaxError`, `http.client.HTTPException`) se atrapan dentro de la tarea y se convierten en una entrada de `fallas`, igual que hoy, con el mismo motivo en español. Una excepción no prevista no se traga: se propaga al terminar de leer el resto (sin `except Exception` sin justificar).
5. El parámetro `leer` sigue inyectable (los tests pasan un lector falso). Como se llama desde hilos, el lector no puede compartir estado mutable sin cuidado; la documentación de `obtener` lo dice.
6. Sin cambios en el log: se siguen logueando solo conteos (`leidas`, `en_ventana`, `elegidas`) y la falla de cada feed, en el orden de `FUENTES_RSS`. Nada de títulos ni links.
7. Sin dependencias nuevas: solo `concurrent.futures` de la librería estándar.

## Fuera de alcance
Agregar o quitar feeds (44 y 45); cambiar el timeout de 10 s o los topes; reintentos; copia local de feeds; leer en paralelo las acciones o los indicadores.

## Archivos que toca
- `micafe/config.py`
- `micafe/fuentes/noticias.py`
- `tests/test_noticias.py`, `tests/test_config.py`

## Criterios de aceptación
- [x] `config.HILOS_FEEDS` existe y vale 6; `noticias.py` no define otro número de hilos.
- [x] Con un lector falso que devuelve los mismos feeds, el resultado de `obtener` es igual al de la versión secuencial (mismas notas, mismo orden, mismas `por_fuente` y `fallas`).
- [x] Con un lector falso donde el primer feed tarda más que el último, el orden de `por_fuente` y de `fallas` sigue siendo el de `FUENTES_RSS`.
- [x] Un feed que falla (error de red, XML roto, no es RSS) aparece en `fallas` con su motivo en español y los demás feeds traen sus notas.
- [x] Un link repetido entre dos feeds se lo queda el primero en el orden de `FUENTES_RSS`, aunque el segundo termine antes.
- [x] Con feeds de 0,3 s cada uno y varios feeds, el tiempo total es claramente menor que la suma (test con tolerancia holgada).
- [x] Solo se leen los feeds de las secciones tildadas (la spec 37 sigue valiendo: ningún pedido de red a las demás).
- [x] `python3 -m unittest discover -s tests -t .` pasa (el arranque de `servidor.py` solo se comprobó importando el módulo).

## Tests (unittest, sin red ni `claude`)
En `test_noticias.py`, con un lector falso (diccionario url -> bytes o excepción) que usa `time.sleep` cortos y una lista con `threading.Lock` para registrar el orden de llamada:
- equivalencia con el resultado esperado de siempre (fixtures de `tests/fixtures/`);
- demoras invertidas (el primero lento, el último rápido) y orden conservado;
- fallas mezcladas (timeout, `HTTPError` 404, XML roto) sin frenar al resto;
- link repetido entre feeds;
- tiempo total menor que la suma (con margen) y a lo sumo `HILOS_FEEDS` lecturas simultáneas (contador con lock);
- `temas` con una sola sección: el lector no recibe las URLs de las demás.
En `test_config.py`: `HILOS_FEEDS` es un entero mayor que 0.

## Cómo probarlo
1. Tests: `python3 -m unittest discover -s tests -t .`.
2. `python3 servidor.py`, abrir http://localhost:8000 y tocar "Preparar el de hoy": la etapa "Trayendo noticias" tarda bastante menos que antes (comparar con el tiempo de `git stash` de esta spec si hace falta).
3. Mirar la consola del servidor: una línea `Feed ... leidas=, en_ventana=, elegidas=` por feed, en el orden de `FUENTES_RSS`.
4. Cortar internet (o poner mal la URL de un feed a propósito y volver a dejarla): la página avisa del feed caído y las demás notas aparecen.

## Notas de implementación
- `obtener` arma la lista de feeds de las secciones activas y la lee con `ThreadPoolExecutor(max_workers=config.HILOS_FEEDS).map`, que conserva el orden de `FUENTES_RSS`. Cada tarea devuelve `(notas, None)` o `(None, error previsto)`; el resto de `obtener` (fallas, log, desempate por link) sigue en el hilo principal, por eso el log queda en orden.
- Una excepción imprevista sale por `map` al recolectar; el `with` espera a que terminen los demás hilos antes de propagarla.
- Tests nuevos en `LecturaEnParalelo` (`tests/test_noticias.py`) y `HILOS_FEEDS` en `tests/test_config.py`. El arranque de `python3 servidor.py` y la prueba manual en la página no se probaron a mano.
