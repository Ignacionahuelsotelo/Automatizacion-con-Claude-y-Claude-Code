# 26 - Pruebas automáticas de la página (Playwright)

**Estado:** hecha

**Aprobación (18/11/2026):** el usuario aprobó explícitamente solo la dependencia de desarrollo Playwright (Python) y su Chromium, en un entorno virtual aislado (`.venv-dev/`). Ninguna otra (ni pytest, ni ruff, ni mypy, ni coverage). Anotado en `specs/README.md`, pregunta 1.

## Depende de
25 y de la respuesta a la pregunta abierta sobre dependencias de desarrollo en `specs/README.md`. Playwright es una dependencia externa: sin aprobación explícita, esta spec no se empieza. La app no se ve afectada: sigue andando sin instalar nada.

## Para qué
Dejar pruebas de punta a punta del front que hoy solo se hacen a mano, sin que la app dependa de ellas.

## Qué tiene que hacer
1. Si la dependencia está aprobada: scripts en `tests/e2e/` que usan la skill `webapp-testing` (Playwright para Python), separados de la suite `unittest` y fuera del runtime de la app. La app no importa nada de ahí.
2. Los scripts levantan el servidor con fuentes simuladas o con `MICAFE_DATOS` apuntando a una carpeta temporal (spec 19), nunca contra `datos/` reales, y sin llamar a internet ni a `claude` (se usa un resumen guardado de ejemplo).
3. Casos mínimos: carga de la página, indicadores con fecha y fuente, "sin dato" visible, una nota con enlace, voto 👍/👎, caja de preguntas con respuesta simulada, aviso de fuente caída, aviso visible si el corrector no pasó.
4. Que fallen si la consola del navegador muestra errores o si hay pedidos a dominios que no son localhost.
5. Documentar cómo instalar y correr (en el README del proyecto, spec 27) marcando que es opcional y de desarrollo.
6. Si la dependencia no se aprueba: la spec se cierra como "no aplica" y las pruebas manuales de la spec 25 quedan como método de prueba del front.

## Fuera de alcance
Pruebas de rendimiento, pruebas contra internet real, integración continua, rediseño visual (por ahora sin design-taste-frontend).

## Skills a usar
- `webapp-testing`.
- `verification-before-completion`.
- `systematic-debugging` si algún caso falla de forma intermitente.

## Archivos que toca
- `tests/e2e/*` (nuevos)
- Un archivo de requisitos de desarrollo solo si se aprueba (por ejemplo `requisitos-dev.txt`), nunca requeridos para correr la app.

## Criterios de aceptación
- [x] Hay aprobación explícita de la dependencia, anotada en `specs/README.md` (o la spec se cerró como "no aplica").
- [x] `python3 servidor.py` y `python3 -m unittest discover -s tests -t .` funcionan sin instalar Playwright.
- [x] Las pruebas e2e pasan sin internet y sin `claude`.
- [x] Las pruebas no tocan `datos/` reales.
- [x] Documentado como opcional.

## Cómo probarlo
1. Instalar la herramienta como dice el README (solo en la máquina de desarrollo) y correr los scripts de `tests/e2e/`.
2. En otra máquina o entorno sin Playwright: arrancar la app y correr los tests `unittest`.
3. Romper a propósito un texto o un enlace del front y comprobar que un caso falla.

## Notas de implementación
- Archivos: `requisitos-dev.txt` (`playwright==1.65.2`; trae `greenlet` como dependencia suya), `.gitignore` (`.venv-dev/`), `tests/e2e/servidor_e2e.py`, `tests/e2e/e2e_pagina.py`, `tests/e2e/correr_e2e.sh` y la sección "Pruebas de la página" del README.
- `servidor_e2e.py` es el servidor real con las fuentes simuladas (indicadores, noticias, acciones, `claude`), `urllib.request.urlopen` bloqueado y datos de ejemplo en `MICAFE_DATOS`. Se niega a arrancar sin esa variable, con la `datos/` real o en los puertos 8000/8001. Cambia el puerto solo en memoria (`servidor.PUERTO`); `config.py` y la app no se tocaron. La caja de preguntas usa la lógica real (`caja.responder`); solo se simula la llamada a `claude`.
- `correr_e2e.sh` crea una carpeta temporal, levanta el servidor con `with_server.py` (de la skill) en el puerto 8765 y corre los casos.
- Los scripts se llaman `e2e_*.py`/`servidor_e2e.py`: `unittest discover -s tests` no los recoge y la suite sigue en 191 sin Playwright.
- Los 8 casos corren cada uno en una página limpia y fallan si la consola del navegador muestra errores o si hay pedidos fuera de localhost / 127.0.0.1.
- Verificado: cambiar "sin dato" por "sin datos" en `app.js` hizo fallar `caso_sin_dato_visible`; un `console.error` y un `fetch` a example.com hicieron fallar todos los casos (cambios deshechos). El hash de `datos/` fue idéntico antes y después.
- No se probó en otra máquina ni con Playwright instalado en otro sistema; no hay caso para "Preparar el de hoy" (no pedido por la spec).
