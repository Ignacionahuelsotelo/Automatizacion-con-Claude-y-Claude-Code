# 09 - Gustos (👍/👎)

**Estado:** hecha

## Depende de
08-pagina-completa

## Para qué
Que el usuario vote las notas y que esos votos influyan en el próximo resumen.

## Qué tiene que hacer
1. Mostrar 👍 y 👎 en cada nota de la página.
2. Cada voto viaja al servidor y se guarda en `datos/gustos.json` (con fecha, y con lo que se necesite para identificar la nota; ver preguntas abiertas).
3. Poder cambiar o quitar un voto.
4. Al preparar un resumen nuevo, el servidor le pasa los gustos al cocinero (Claude) como contexto, y la skill indica cómo usarlos.
5. Los gustos influyen en la selección y el énfasis de las notas, pero no pueden saltarse las reglas (largo, links, máximo por medio, ventana de ayer).
6. Si `gustos.json` no existe o está roto, seguir sin gustos y no romper.

## Fuera de alcance
Aprendizaje complejo o puntajes; la caja de preguntas; sincronizar gustos entre dispositivos.

## Archivos que toca
- `index.html`
- `servidor.py`
- `.claude/skills/` (instrucciones para usar los gustos)
- `datos/gustos.json` (se genera en ejecución)

## Criterios de aceptación
- [x] Un voto queda en `datos/gustos.json` y sobrevive a un reinicio. (Probado en una copia del proyecto, con reinicio del servidor de prueba.)
- [x] Se puede cambiar o quitar un voto. (API y navegador: votar de nuevo quita el voto, tocar el otro lo cambia.)
- [x] El pedido a `claude -p` incluye los gustos guardados. (Con `claude` falso: se revisó el texto del pedido.)
- [ ] Votar y preparar otro resumen produce un cambio perceptible de selección. (No comprobado: requiere el `claude` real; el falso no elige por gustos.)
- [x] Con `gustos.json` roto o ausente, el resumen se prepara igual. (Probado con roto, con formato raro, con entradas malas y ausente.)
- [x] El resumen sigue cumpliendo todas las reglas del corrector. (Con `claude` falso, el corrector aprueba el resumen con gustos en el pedido. Que el modelo real cumpla las reglas no se comprobó.)

## Cómo probarlo
1. Votar 👎 varias notas de un tema y 👍 de otro.
2. Preparar otro resumen y comparar con el anterior.
3. Borrar `datos/gustos.json` y confirmar que todo sigue funcionando.

## Notas de implementación

**Qué se hizo**
- `gustos.py` (módulo nuevo, como pidió el implementador): lee, valida y guarda `datos/gustos.json`. Cada voto tiene `tipo` ("nota" o "tema"), `clave`, `voto` ("me_gusta" o "no_me_gusta"), `votado_en` (con zona horaria de Buenos Aires) y, en las notas, `titulo`, `medio` y `seccion`. Quitar un voto es mandar `voto: null` y se borra la entrada. Hay como mucho un voto por nota o tema. Escribe a `.tmp` y reemplaza. Tiene un lock porque el servidor atiende en hilos.
- `servidor.py`: rutas nuevas `GET /api/gustos` (devuelve `votos` y `aviso`) y `POST /api/gustos` (registra, cambia o quita un voto; 400 si el pedido no sirve, 500 si no se puede escribir). Al preparar el resumen, lee los gustos y le pasa las líneas al pedido. Si el archivo falta o está roto, sigue sin gustos.
- `resumen.py` (fuera de la lista de archivos de la spec, mismo criterio que en las specs 07 y 08): `armar_pedido` y `generar` aceptan `gustos` (lista de líneas). Si la lista está vacía, no se agrega nada al pedido. Es el único lugar donde se arma el pedido a `claude -p`.
- `index.html`: 👍 y 👎 en cada nota de "Noticias de ayer" y en cada tema de "Mis preferencias". El botón del voto activo queda marcado (`aria-pressed`). Tocar el voto que ya está marcado lo quita. El mensaje va en "Noticias de ayer" para las notas y en "Mis preferencias" para los temas. Si el archivo de gustos tiene un problema, el aviso se muestra en "Noticias de ayer". Todo con `textContent`.
- `.claude/skills/resumen-diario/SKILL.md`: sección nueva "Cómo usar los gustos (opcional)". Los gustos sirven para desempatar y para el énfasis. No cambian cantidades por sección, orden, tope por medio, ventana, links ni largo, y una nota fuera de la lista no se usa.

**Decisiones**
- **Votos de temas (decisión 10 del README).** La spec solo pide 👍/👎 en las notas, pero la decisión 10 dice "notas y temas", así que los temas también se votan (en "Mis preferencias"). Si no se quiere, se quitan los botones de `crearBotonesVoto("tema", …)` en `index.html` y no cambia nada más.
- **Dónde se vota una nota.** En "Noticias de ayer", que tiene todas las notas candidatas con sus datos completos. No se agregaron votos dentro del texto del resumen (las notas del resumen son un subconjunto de esta lista).
- **Identificación de la nota.** Por su link, que es único y es la misma clave que usa la deduplicación (decisión 9). Título, medio y sección se guardan para armar el pedido sin volver a leer los feeds.
- **30 votos.** Son los 30 más recientes por `votado_en`. Cambiar un voto lo vuelve el más reciente. Los votos que quedan fuera no se borran del archivo.
- **Archivo roto.** Al votar, si `gustos.json` está roto o tiene entradas que no se entienden, se ignoran esas entradas y el archivo se reescribe limpio con el voto nuevo. Las entradas ignoradas se pierden; el aviso lo dice.
- **Temas en el pedido.** Un voto a tema queda como `- Tema Economía: me gusta.` y no lleva ninguna cifra, así que no afecta a los indicadores.

**Pruebas hechas** (en una copia del proyecto en el scratchpad, en el puerto 8143; el 8000 no se tocó ni se reinició; `datos/` real no se modificó; los feeds y los indicadores se simularon con datos fijos y fechas de ayer; `claude` fue un script falso que arma un resumen con las notas del pedido y responde OK al corrector)
- API: alta, cambio, quitar (`voto: null`), y los 4 errores de validación (tema desconocido, nota sin link, JSON inválido, voto desconocido). Nota sin título y cuerpo que no es objeto también dan 400. Un error no cambia el archivo. Tras reiniciar el servidor, el voto sigue guardado.
- Pedido a `claude -p`: con votos, la sección "## Gustos de la persona" aparece con la nota (título, medio, sección) y el tema. Con 35 votos en el archivo, llegan 30 (los más nuevos). Con `gustos.json` roto, con formato raro (una lista en vez de objeto), con entradas malas o ausente, el resumen responde 200, queda aprobado por el corrector y el pedido no lleva la sección.
- Navegador (Chrome headless por DevTools, sin instalar nada): 26 botones en las notas (13 notas), 8 en los temas. Votar 👍 marca el botón y muestra "Voto guardado." (un solo POST). Tocar 👎 lo cambia. Tocarlo de nuevo muestra "Voto quitado." Un 👎 a un tema queda marcado tras recargar. Las capturas se revisaron y los botones se ven bien.

**Pendiente o no probado**
- El cambio perceptible en la selección (criterio 4) no se comprobó: con el `claude` real no se corrió (no se gastó el plan ni se escribió un resumen real en `datos/`). Queda por hacer: votar, preparar el de hoy con el `claude` real, y comparar con el anterior.
- Que el modelo real respete los gustos sin romper las reglas no se comprobó; las reglas las sigue chequeando el corrector (código y modelo), que se ejecutó igual con los gustos presentes.
- El servidor del puerto 8000 sigue corriendo el código anterior: para que tome `/api/gustos` y los gustos en el pedido hay que reiniciarlo con `python3 servidor.py`. No lo reinicié.
- Antes de subir el cambio conviene revisar que `datos/gustos.json` no aparezca en git (`.gitignore` ya tiene `datos/`).
