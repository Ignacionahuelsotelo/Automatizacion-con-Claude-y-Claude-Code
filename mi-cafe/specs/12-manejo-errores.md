# 12 - Manejo de errores y pulido

**Estado:** hecha

## Depende de
11-acciones (y, en general, todas las anteriores)

## Para qué
Que si una fuente falla, la página avise y no se rompa, y dejar el proyecto prolijo.

## Qué tiene que hacer
1. Revisar cada punto de falla: APIs de indicadores, RSS, `claude -p`, lectura/escritura de `datos/`, JSON roto.
2. Cada falla se muestra en la página en español, diciendo qué fuente falló, sin trazas técnicas.
3. Una falla parcial no tira el resto: se muestra lo que sí se pudo traer.
4. El servidor registra el error (consola) y sigue andando.
5. Alertar de forma visible si una API devuelve 410 (versión dada de baja) o un dato con fecha vieja.
5. Revisar que todos los textos, comentarios y mensajes estén en español rioplatense.
6. Actualizar `CLAUDE.md` con los comandos reales para correr el proyecto y con el estado actual (ya hay código).

## Fuera de alcance
Funcionalidades nuevas, tests automatizados con librerías externas, despliegue fuera de localhost.

## Archivos que toca
- `servidor.py`
- `index.html`
- `CLAUDE.md` (solo estado y comandos)

## Criterios de aceptación
- [x] Con una API caída, la página lo avisa y muestra "sin dato" en ese indicador.
- [x] Con un RSS caído, la página lo avisa y muestra las demás notas.
- [ ] Con `claude -p` caído, la página muestra un error claro y sigue usable.
- [x] Un archivo de `datos/` roto o borrado no tira el servidor.
- [x] No quedan mensajes de error en inglés ni trazas visibles en la página.
- [x] `CLAUDE.md` refleja cómo correr el proyecto.

## Cómo probarlo
1. Desconectar internet y preparar el resumen: ver los avisos.
2. Romper una URL de RSS y una de API a propósito, una a la vez.
3. Borrar o corromper un archivo de `datos/` y recargar.

## Notas de implementación

**Estado: hecha (18/11/2026).** Quedan sin tildar el criterio de `claude -p` caído en la página, porque el servidor se probó pero el clic real en el navegador no (ver "Pendiente").

### Qué se hizo
- **Avisos visibles en la página (`index.html`):** hay una caja de avisos en Indicadores (`#avisos-indicadores`) y la de Noticias (`#avisos-noticias`) ahora tiene la clase `aviso`. Muestran en español qué fuente falló, o qué dato tiene fecha vieja. Son frases sin trazas.
- **Indicadores (`indicadores.py`):** cada consulta fallida deja un motivo en español (sin conexión, tardó demasiado, respondió HTTP N, versión dada de baja). `obtener()` devuelve `avisos`. Un HTTP 410 avisa que hay que actualizar la dirección. Un dato con más de 1 día hábil de antigüedad agrega su aviso. La copia local guarda el motivo también.
- **RSS (`noticias.py`):** `_motivo` devuelve texto en español (antes podía salir "HTTP 410" o un texto de Python en inglés). Un 410 se avisa como versión dada de baja. Los feeds caídos siguen descartándose y avisándose (decisión 3).
- **`servidor.py`:**
  - Cada `do_GET` y `do_POST` está protegido: un error no previsto va a la consola con su traza y responde 500 con un aviso en español. El servidor sigue andando.
  - `send_error` responde en español (404 ya era español; 501 y 400 antes salían en inglés, con HTML).
  - Las respuestas de error de guardado (preferencias, gustos, resumen) ya no incluyen el error técnico del sistema operativo; ese detalle va a la consola.
  - La respuesta de `POST /api/resumen` trae `avisos` (indicadores y noticias), también cuando falla `claude`.
  - `leer_ultimo_resumen` ignora archivos que no tienen `fecha` de texto, además de los rotos o borrados.
- **`resumen.py`, `caja.py`:** los errores de `claude` (no encontrado, código de salida, lectura de la skill) dicen algo claro en español. El texto crudo de `claude` (stderr) va a la consola, no a la página.
- **`gustos.py`, `preferencias.py`:** los avisos de archivo roto ya no incluyen el error técnico; ese detalle va a la consola.
- **Página tras un fallo de `claude`:** el texto de error se muestra y después se vuelve a cargar el último resumen guardado, para que la página no quede vacía.
- **Textos y comentarios:** revisados en español. No quedó ningún mensaje de error en inglés en lo que ve la página.
- **`CLAUDE.md`:** solo la sección "Estado del proyecto": ya hay código, cómo correrlo (`python3 servidor.py`, http://localhost:8000), cómo se prueba (a mano) y que `datos/` no se versiona.

### Desvío de "Archivos que toca"
La spec lista solo `servidor.py`, `index.html` y `CLAUDE.md`. Las fallas nacen en `indicadores.py`, `noticias.py`, `resumen.py`, `caja.py`, `gustos.py` y `preferencias.py`, y ahí estaba el texto técnico que iba a la página. Por eso se tocaron también. No se agregó ninguna funcionalidad nueva ni dependencia.

### Cómo se probó
Todo en una copia del proyecto en el scratchpad (`/private/tmp/claude-501/-Users-ignaciosotelo-Desktop-Automatizacion-con-Claude-y-Claude-Code-mi-cafe/dc4de262-903c-4346-8b82-e8ae7fc33578/scratchpad/copia-12`), con un lanzador que cambia el puerto (8012 a 8023, uno por prueba) y simula las fallas. Los servidores de prueba se apagan solos por temporizador. `claude` nunca se ejecutó de verdad.
- **API caída (DolarApi):** `/api/indicadores` devuelve "sin dato" para los dólares y las brechas, con aviso "No se pudo consultar DolarApi: no se pudo conectar". Reservas (dato real) sigue. En Chrome headless, la página muestra el aviso visible.
- **API 410 (ArgentinaDatos):** aviso "la versión de la API fue dada de baja (HTTP 410), hay que actualizar la dirección".
- **Dato viejo:** riesgo país con fecha 02/01/2026 genera aviso de desactualizado.
- **RSS caídos (Infobae Política con timeout, Olé con 410):** `/api/noticias` devuelve las 12 notas que sí se leyeron y los dos motivos. En Chrome headless se ven los dos avisos.
- **`claude` caído:** no instalado (502, "No se encontró el comando"), código de salida 1 (502, sin el stderr en la página) y timeout (504, "tardó más de 5 minutos"). En todos los casos la respuesta trae `avisos`.
- **Éxito de `POST /api/resumen`** (con salida falsa de `claude`): responde 200 con `resumen` y `avisos`.
- **`datos/` roto:** preferencias, gustos, copia de indicadores y resúmenes con JSON roto, con forma incorrecta o con `fecha` que no es texto. Todas las rutas responden 200 (o 400 en un POST con cuerpo roto) y el servidor sigue. Después se borra `datos/` entero: todo responde y `POST /api/preferencias` lo vuelve a crear.
- **Protocolo y errores inesperados:** ruta inexistente (404 en español), PUT y DELETE (501 en español), `index.html` sin permiso de lectura (500 en español, traza en consola). El servidor sigue andando después.
- **Página:** `node --check` del script de `index.html` sin errores. Render con Chrome headless (`--dump-dom`) con API caída y con RSS caídos.
- **Proyecto:** `datos/` del proyecto sin cambios. El servidor del 8000 sigue escuchando y no se reinició ni se cerró.

### Pendiente o a decidir
1. **Criterio de `claude -p` caído en la página:** el servidor se verificó, pero el clic en "Preparar el de hoy" con `claude` caído solo se revisó leyendo el código, no en un navegador. Conviene probarlo a mano (desinstalando o renombrando `claude` por un momento).
2. **Falla de ArgentinaDatos guardada 3 horas:** `_respuesta` reutiliza la copia, también cuando la última consulta falló. Así una caída breve de ArgentinaDatos deja "sin dato" hasta 3 horas. Es el comportamiento de la spec 03, pero choca con el aviso de la spec 12. ¿Qué preferís: reintentar si la última consulta falló?
3. **Respuestas válidas sin dato:** si una fuente responde 200 pero sin un valor usable, el indicador queda "sin dato" sin aviso. Solo se avisan fallas de conexión, HTTP y datos viejos.
4. **Numeración de la spec:** hay dos ítems "5" en "Qué tiene que hacer". No lo cambié.
5. **Servidor del 8000:** no se reinició ni se cerró. Mi única interacción fue un `GET /` de comprobación (11:12:52), que quedó en `datos/servidor-8000.log`.

