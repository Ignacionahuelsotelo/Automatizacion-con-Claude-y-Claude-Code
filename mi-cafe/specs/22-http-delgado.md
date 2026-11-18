# 22 - Capa HTTP delgada y servicio de resumen

**Estado:** hecha

## Depende de
21.

## Para qué
`Manejador` hoy mezcla HTTP con negocio: `_responder_resumen` (unas 50 líneas) orquesta noticias, indicadores, gustos, redacción, corrector y guardado, y se repite el mismo bloque de leer el cuerpo JSON en tres métodos. Se separa para que el dominio se pueda probar sin HTTP.

## Qué tiene que hacer
1. Crear `micafe/dominio/servicio.py` (o `micafe/servicios/`) con las operaciones que hoy están dentro del manejador, sin conocer nada de HTTP: `obtener_indicadores`, `obtener_noticias`, `preparar_resumen` (incluye los avisos de indicadores y noticias, los gustos, el corrector con sus reintentos y el guardado), `ultimo_resumen`, `guardar_preferencias`, `guardar_voto`, `responder_pregunta`. Devuelven datos o levantan los errores de la spec 20.
2. `indicadores_con_acciones` pasa de `servidor.py` al servicio.
3. En `web/`, separar:
   - una tabla de rutas `(método, ruta) -> función` en vez de la cadena de `if/elif`;
   - helpers para leer el cuerpo JSON (una sola vez, con límite de tamaño razonable y el mismo mensaje "El cuerpo no es JSON válido." con 400) y para responder JSON, texto y archivos;
   - el manejo de `ErrorMiCafe` y de errores inesperados en un único lugar.
4. Mantener exactamente las mismas rutas, métodos, códigos y formas de JSON (`/`, `/api/preferencias`, `/api/indicadores`, `/api/noticias`, `/api/resumen` GET y POST, `/api/gustos`, `/api/preguntas`; resto 404). Mantener `send_error` en español y el hilo por pedido (`ThreadingHTTPServer`).
5. Mantener el aislamiento: solo escucha en 127.0.0.1 y un pedido lento (`claude -p`) no frena a los demás.
6. Tests del servicio sin HTTP (con fuentes y `claude` simulados): resumen armado de punta a punta, reintento del corrector, aviso cuando guarda con error, resumen sin acciones si no están en preferencias. Los tests de rutas de la spec 17 siguen pasando.

## Fuera de alcance
Cambiar la API, agregar rutas, autenticación, async, frameworks web, servir el front desde archivos separados (24).

## Skills a usar
- `verification-before-completion`.
- `brainstorming` si hay dudas sobre dónde corta el servicio y dónde la capa web.
- `resumen-diario` y `corrector`: no se tocan, pero hay que correr un resumen real para comprobar que se siguen cumpliendo (550 a 650 palabras, links, sin cifras del modelo).

## Archivos que toca
- `micafe/dominio/servicio.py` (nuevo)
- `micafe/web/servidor.py` (y módulos nuevos de `web/` si hace falta, por ejemplo `rutas.py`)
- `tests/test_servicio.py` (nuevo), `tests/test_servidor.py`

## Criterios de aceptación
- [ ] `web/` no importa nada de `fuentes/` ni de `almacen/`: solo del servicio.
- [x] No quedan bloques repetidos de lectura de cuerpo JSON.
- [x] Respuestas idénticas a las de antes (mismas rutas, códigos y JSON).
- [ ] Un resumen real de punta a punta sigue dando 550 a 650 palabras, con link en cada nota, máximo 3 por medio (5 los lunes) y sin repetidas.
- [x] Un pedido lento no bloquea a otro (probar dos pestañas).
- [x] La suite pasa.

## Cómo probarlo
1. `python3 -m unittest discover -s tests -t .`.
2. Recorrer la página completa y comparar con la versión anterior.
3. `curl -X POST -d 'basura' http://localhost:8000/api/gustos`: 400 con el mensaje de siempre.
4. Mientras se prepara el resumen, abrir otra pestaña y comprobar que las preferencias cargan.

## Notas de implementación
- `micafe/dominio/servicio.py` concentra las operaciones (incluido `indicadores_con_acciones`). Las que validan devuelven `(datos, errores)` para conservar los 400 con lista de errores; los fallos de escritura levantan `ErrorAlmacenamiento`. `preparar_resumen(ahora=None)` devuelve `{"resumen", "avisos"}`.
- `web/servidor.py` quedó con una tabla `RUTAS_JSON {(método, ruta): función}`, `cuerpo_json()` (una sola lectura, tope de 1 MB; si se pasa, 413 con "El cuerpo es demasiado grande.", caso nuevo que antes no existía), `_responder_json/_texto/_archivo` y un único `_atender` que maneja `ErrorMiCafe` y errores inesperados.
- `web/` solo importa `config`, `errores`, `logs` y `dominio.servicio`. Los tests ahora parchean los nombres en `servicio` (rutas de `datos/` y fuentes).
- Verificado con un servidor en puerto 0: POST basura a `/api/gustos` da 400 con el mensaje de siempre, 404 en el resto, y con un resumen lento simulado (2 s) otro pedido respondió al instante.
- NO verificado: un resumen real con `claude -p` (550 a 650 palabras, links, tope por medio); el recorrido manual de la página; las dos pestañas con `claude` real. Los tests del servicio lo cubren con `claude` simulado.
