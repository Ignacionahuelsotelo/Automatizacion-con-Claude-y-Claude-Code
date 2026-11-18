# 08 - Página completa y archivo de resúmenes

**Estado:** hecha

## Depende de
07-corrector

## Para qué
Armar la página definitiva y el flujo de punta a punta: un clic prepara todo, y cada resumen queda archivado.

## Qué tiene que hacer
1. Guardar cada resumen en `datos/resumenes/` con su fecha (un archivo por día), sin pisar otros días.
2. Al abrir la página, mostrar las preferencias y el último resumen guardado.
3. Botón **"Preparar el de hoy"**: dispara indicadores, noticias, redacción, corrector y guardado, y muestra el resultado.
4. Estado de "cargando" claro mientras `claude -p` trabaja, y botón deshabilitado para evitar doble clic.
5. Diseño: indicadores arriba, noticias con link debajo. Un solo `index.html`, sin librerías ni recursos externos.
6. Montos en formato `$ 1.234,50`; todos los textos en español rioplatense.
7. Mostrar fecha y fuente junto a cada indicador, y el aviso del corrector si lo hubo.

## Fuera de alcance
👍/👎 (spec 09), caja de preguntas (spec 10), acciones (spec 11), manejo fino de errores (spec 12).

## Archivos que toca
- `index.html`
- `servidor.py`
- `datos/resumenes/` (se genera en ejecución)

## Criterios de aceptación
- [x] Un clic en "Preparar el de hoy" arma indicadores, resumen y los muestra. (Probado con un `claude` falso; no se corrió con el `claude` real, ver notas.)
- [x] Mientras trabaja se ve "cargando" y el botón no se puede apretar de nuevo.
- [x] El resumen queda en `datos/resumenes/` con fecha. (Probado en una copia del proyecto.)
- [x] Al recargar, se ve el último resumen guardado sin volver a llamar a Claude.
- [x] `index.html` no carga nada de afuera.
- [x] Indicadores arriba y cada noticia con link.

## Cómo probarlo
1. Abrir la página y tocar el botón; esperar el resultado completo.
2. Recargar y verificar que aparece el mismo resumen.
3. Revisar `datos/resumenes/` y mirar la pestaña de red del navegador para confirmar que no hay pedidos externos.

## Notas de implementación

**Qué se hizo**
- `servidor.py`:
  - `POST /api/resumen` ahora guarda el resumen de hoy en `datos/resumenes/AAAA-MM-DD.json` (fecha de Buenos Aires) con: `fecha`, `generado_en` (dd/mm/aaaa hh:mm), `indicadores` (tal como se mostraron), `texto` y `chequeo`. El archivo se escribe a `.tmp` y después se reemplaza. Solo se toca el archivo del día: los otros días no se pisan. Responde `{ok, resumen}`.
  - Ruta nueva `GET /api/resumen`: devuelve `{ok, resumen}` con el resumen guardado más reciente, o `resumen: null` si no hay. No llama a Claude.
  - Si el resumen no se puede guardar (error de disco), responde 500 con mensaje.
- `corrector.py` (fuera de la lista de archivos de la spec, mismo criterio que en la spec 07): `leer_resumenes_previos` tiene un parámetro nuevo `anteriores_a`. El servidor lo usa con la fecha de hoy. Motivo: si se prepara el de hoy dos veces, el dedupe comparaba el resumen nuevo contra el archivo de hoy que se acaba de reescribir y marcaba todo como repetido. Ahora solo se miran los 3 días anteriores.
- `index.html`:
  - Orden nuevo: Indicadores (arriba), "Resumen de hoy" (botón "Preparar el de hoy", aviso del corrector, resumen), "Noticias de ayer" y, al final, "Mis preferencias". Las preferencias antes estaban arriba; se movieron al final para que lo primero sea lo del día.
  - Al abrir, se carga el último resumen guardado (`GET /api/resumen`). Si no hay, dice que todavía no hay uno.
  - Mientras `claude -p` trabaja: estado "Cargando: Claude está redactando el resumen con las notas de ayer. Puede tardar hasta 5 minutos." y botón deshabilitado. Al terminar, se redibujan los indicadores con los del resumen y el resumen.
  - Formato del texto (punto 2 de la spec): cada línea va en su lugar. Los encabezados de sección son `h3`, el título de cada nota es `h4`, "Por qué importa:" va en su párrafo, la línea de "Medio, fecha" va en letra chica, y el link va como enlace en línea aparte. Antes, el texto se partía en bloques, pero título, "Por qué importa" y medio quedaban pegados. Todo con `textContent`, sin HTML del modelo.
  - El aviso del corrector es el mismo `#aviso-corrector` de la spec 07; no se duplicó.
  - Estilos mínimos en el `<style>` del propio archivo. No hay librerías ni recursos externos.

**Decisiones**
- "Hoy" se toma en America/Argentina/Buenos_Aires (decisión 5). El archivo se nombra con la fecha en que se preparó, no con la fecha de las notas (que son de ayer).
- Se guardan también los resúmenes con aviso del corrector, para que al recargar se vea el mismo aviso.
- Al preparar de nuevo el mismo día, el archivo de hoy se reemplaza.
- No se agregó lock en el servidor: el botón deshabilitado evita el doble clic. Si llegan dos POST a la vez, el último que termina queda guardado.

**Pruebas hechas** (en una copia del proyecto en el scratchpad, en el puerto 8141; el 8000 no se tocó ni se reinició; `datos/` real no se modificó)
- `claude` falso en el PATH (responde `OK` al chequeo con modelo y arma un resumen con las notas del pedido para la redacción). Las noticias y los indicadores se parchearon con datos fijos.
- POST con largo fuera de rango: reintentos, aviso y el archivo guardado con `no_cumple`.
- POST aprobado: el archivo `2026-11-18.json` tiene las claves `fecha`, `generado_en`, `indicadores`, `texto` y `chequeo`. GET devuelve lo mismo que el POST.
- Segundo POST el mismo día: aprobado; no se compara contra el archivo de hoy.
- Dedupe contra el día anterior: se sembró `2026-11-17.json` con un link repetido; el resumen se marcó con "Nota repetida de un resumen anterior" y el archivo de ese día quedó con el mismo md5 (no se pisó). El archivo sembrado se borró después.
- Chrome headless con DevTools (sin instalar nada):
  - Al abrir, aparece el resumen guardado: títulos, secciones, links y la cabecera con fecha. Los indicadores van arriba con fecha y fuente.
  - Clic: el botón queda deshabilitado y aparece el estado de cargando. Un segundo clic no genera un POST (1 solo).
  - Al terminar, el resumen se muestra y el botón vuelve a estar habilitado.
  - Recargar muestra el mismo resumen.
  - Aviso del corrector visible cuando el resumen no cumple.
  - Pedidos de red: 11, todos a 127.0.0.1. Ninguno externo.
  - Capturas revisadas: el diseño y la separación de líneas se ven bien.
- `py_compile` de `servidor.py` y `corrector.py`; `node --check` del JS de `index.html`.

**Pendiente o no probado**
- No se corrió con el `claude` real (para no gastar el plan ni escribir un resumen real en `datos/`). Queda por hacer: tocar "Preparar el de hoy" con el `claude` real y revisar el resultado (primer punto de "Cómo probarlo").
- El servidor del puerto 8000 sigue corriendo el código anterior (se cargó antes de estos cambios). Para que tome `GET /api/resumen` y el guardado hay que reiniciarlo con `python3 servidor.py`. Hasta entonces, la página en 8000 muestra "No se pudo cargar el último resumen guardado" porque la ruta nueva no existe en ese proceso. No lo reinicié porque lo pediste.
- La spec 07 tenía sin tildar el aviso visible en navegador. Ahora se vio en Chrome headless (ver arriba), pero no toqué esa spec.
