# 02 - Preferencias

**Estado:** hecha

## Depende de
01-esqueleto

## Para qué
Guardar qué indicadores (dólar, riesgo país, acciones) y qué temas quiere el usuario (lista cerrada: Política, Economía, Deportes y Tecnología), y que sobrevivan a un reinicio.

## Qué tiene que hacer
1. Guardar las preferencias en `datos/preferencias.json`.
2. Endpoint para leerlas (`GET`) y otro para guardarlas (`POST`), con JSON.
3. Si el archivo no existe, devolver valores por defecto razonables y crearlo al primer guardado.
4. Validar lo que llega: solo indicadores y temas conocidos; ignorar o rechazar el resto con un mensaje claro.
5. Si el archivo está corrupto, no romper: usar los valores por defecto y avisar.
6. Una pantalla mínima en `index.html` para tildar/destildar y ver que se guarda (el diseño final es de la spec 08).

## Fuera de alcance
Gustos 👍/👎 (spec 09), diseño final de la página, y cómo se usan las preferencias para filtrar el resumen (specs 05 y 06).

## Archivos que toca
- `servidor.py`
- `index.html`
- `datos/preferencias.json` (se genera en ejecución, no se versiona)

## Criterios de aceptación
- [x] `GET` devuelve las preferencias guardadas o las de por defecto.
- [x] `POST` guarda y un `GET` posterior devuelve lo guardado.
- [ ] Cambiar una preferencia, reiniciar el servidor y recargar: sigue la elección. (Comprobado por API: se guarda, se reinicia el servidor y el `GET` devuelve lo mismo. Falta recargar la página en el navegador.)
- [x] Un valor desconocido no se guarda.
- [x] Un `preferencias.json` roto no tira el servidor.
- [x] `datos/preferencias.json` no aparece en `git status`.

## Cómo probarlo
1. Abrir la página, cambiar una preferencia.
2. Parar y volver a arrancar `servidor.py`.
3. Recargar y confirmar que la elección sigue.
4. Romper a mano el JSON y confirmar que el servidor avisa y sigue andando.

## Notas de implementación
- **Archivos tocados:** `preferencias.py` (nuevo, toda la lógica de preferencias), `servidor.py` (solo rutas, un helper `_responder_json`, `do_POST` y el import), `index.html` (pantalla mínima con casillas y un aviso). `datos/preferencias.json` se crea al guardar.
- **Indicadores:** se guardan como `dolar`, `riesgo_pais` y `acciones`, tal como dice la spec. El desglose del dólar (oficial, blue, MEP, CCL) lo decide la spec 03; por ahora no es una preferencia separada.
- **Temas:** lista cerrada `Política`, `Economía`, `Deportes`, `Tecnología` (decisión 6 de `specs/README.md`).
- **Formato del archivo:** `{"indicadores": [...], "temas": [...]}`, con las listas en el orden de la lista de conocidos y sin repetidos.
- **Por defecto:** si no hay archivo, todos los indicadores y temas quedan elegidos.
- **API:** `GET /api/preferencias` devuelve `{"preferencias", "opciones", "aviso"}`. `opciones` trae los indicadores (con su nombre para mostrar) y los temas, así la página no repite la lista. `POST /api/preferencias` recibe el objeto completo; responde 200 con `{"ok": true, ...}` o 400 con `{"ok": false, "errores": [...]}`.
- **Validación:** si llega un valor desconocido, se rechaza todo el POST y no se guarda nada a medias. Un cuerpo que no es JSON o que no es un objeto también da 400.
- **Archivo roto:** si el JSON no se lee o no tiene la forma correcta (o trae valores desconocidos a mano), el `GET` devuelve los valores por defecto con `aviso` no nulo y lo imprime en la consola. El servidor sigue andando. Un `POST` posterior reemplaza el archivo roto por uno válido.
- **Escritura:** se escribe en `preferencias.json.tmp` y después se reemplaza con `os.replace`, para no dejar un archivo a medio escribir si se corta.
- **Ruta del archivo:** `servidor.py` define `ARCHIVO_PREFERENCIAS` y se la pasa al módulo; `preferencias.py` no conoce rutas fijas, así que es fácil de probar.
- **Pruebas hechas:** con el servidor levantado en el puerto 8001 (ver abajo), se probó: GET sin archivo (defecto), POST válido seguido de GET, POST con valor desconocido (400, no cambia el archivo), POST con cuerpo que no es JSON o es una lista (400), reinicio del servidor (la elección se mantiene), archivo JSON roto (GET 200 con aviso y valores por defecto, el servidor sigue vivo), POST que repara el archivo, rutas inexistentes (404). `git status` no muestra nada de `datos/` y `git check-ignore` confirma la regla. Se borró el archivo de prueba al final.
- **Puerto 8000 (no se cerró):** al empezar había un proceso `python3 servidor.py` de este proyecto ya escuchando en el 8000 (arrancado 20:49, con el código de la spec 01). Se intentó cerrarlo para usar el 8000 y el cierre fue denegado por permisos, así que quedó corriendo. Las pruebas se hicieron en el 8001 con un arranque temporal desde el scratchpad, sin tocar el proyecto. **Ese proceso del 8000 sigue con el código viejo:** hay que reiniciarlo (`Ctrl+C` y `python3 servidor.py`) para que tenga `/api/preferencias`.
- **Pendiente:** no se abrió el navegador. Falta probar la pantalla: tildar, reiniciar, recargar y ver el aviso con un JSON roto. Por eso el criterio de "sigue la elección" queda sin tildar. El JS de `index.html` pasó una revisión de sintaxis con node, pero no se ejecutó en un navegador.
- **Diseño:** la pantalla es mínima, como pide la spec; el diseño final es de la spec 08.
