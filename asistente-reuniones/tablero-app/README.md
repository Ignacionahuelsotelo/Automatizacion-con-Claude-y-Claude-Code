# Mesa de operaciones

Tablero local del asistente de reuniones. Lee `../tareas/tareas.json`, `../reuniones/*/resumen-dia.md` y `../logs`,
se actualiza solo cuando esos archivos cambian y puede correr `/preparar-dia` y `/cerrar-reunion`.

**Abrirlo:** doble clic en `Abrir tablero.command` (o `npm run build && npm start`) y entrar a http://127.0.0.1:3210.

## Seguridad
- Solo escucha en `127.0.0.1`: no es accesible desde la red. Rechaza cualquier `Host` u `Origin` ajeno.
- Los botones corren solo dos comandos fijos; el texto que escribís nunca se pasa a una terminal (las notas van a un archivo).
- Claude se lanza con una lista cerrada de permisos (`src/lib/comandos.ts`): puede leer calendario, Gmail y Drive y dejar
  borradores, pero no enviar mails, no crear ni mover eventos y no borrar nada.
- Un solo comando a la vez, máximo 20 minutos y 5 USD por corrida.
- Cabeceras CSP, `X-Frame-Options`, `nosniff`. Los documentos se muestran como texto, nunca como HTML.

## Probar sin gastar
`CLAUDE_BIN=/ruta/a/un/script npm run dev` reemplaza a `claude` por un script de prueba.
