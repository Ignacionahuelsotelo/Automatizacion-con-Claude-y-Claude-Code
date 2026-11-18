# 04 - Noticias

**Estado:** hecha

## Depende de
02-preferencias

## Para qué
Leer los RSS de los medios y quedarse solo con las notas de ayer, para tener la materia prima del resumen.

## Qué tiene que hacer
1. Leer los RSS de Infobae, Página/12, Ámbito, Olé y elDiarioAR. URLs de `docs/investigacion.md`, tabla de fuentes:
   - Infobae: `https://www.infobae.com/arc/outboundfeeds/rss/` (y por sección: `/category/{sección}/`).
   - Página/12: `.../arc/outboundfeeds/rss/portada`, `/secciones/el-pais/notas`, `/secciones/economia/notas`, `/secciones/el-mundo/notas`.
   - Ámbito: `https://www.ambito.com/rss/ultimas-noticias.xml`, `/rss/economia.xml`, `/rss/pages/finanzas.xml`.
   - Olé: `https://www.ole.com.ar/rss/ultimas-noticias/` (acceso no confirmado).
   - elDiarioAR: `https://www.eldiarioar.com/rss/`.
   Varias URLs salen de directorios de terceros: probar cada feed al instalar y dejar las URLs en un solo lugar fácil de cambiar.
2. Parsear con la librería estándar (`xml.etree`, `urllib`); sin dependencias externas.
3. Quedarse solo con las notas de **ayer**; los lunes, de viernes a domingo.
4. Descartar las notas sin fecha.
5. Cada nota conserva título, medio, fecha y **link**.
6. Máximo 3 notas por medio; los lunes, máximo 5 por medio (la ventana es más larga).
7. Clarín y La Nación (muro de pago) solo sirven para detectar temas, nunca como único enlace; no usarlos como fuente de links en esta spec.
8. Si un RSS falla, seguir con los demás e informar cuál falló.
9. Endpoint (`GET`) que devuelve la lista; mostrarla en `index.html` como lista simple con links.
10. Respetar los temas elegidos en las preferencias.
11. Asignar cada feed a las secciones donde se usa, según la prioridad de la investigación: Política (Infobae, elDiarioAR; Página/12 de contraste), Economía (Ámbito, Infobae; Página/12 de contraste), Internacional (Página/12 "El Mundo", Infobae), Deportes (Olé, Infobae deportes), Tecnología (Infobae tecnología).
12. Convertir `pubDate` a la zona horaria de Buenos Aires antes de decidir si cae en la ventana.

## Fuera de alcance
Resumir con Claude, deduplicar contra resúmenes anteriores (spec 07), diseño final, cualquier cifra de indicadores.

## Archivos que toca
- `servidor.py`
- `index.html`

## Criterios de aceptación
- [x] La lista contiene solo notas del día de ayer (o de viernes a domingo si hoy es lunes).
- [x] Ninguna nota sin fecha aparece.
- [x] Todas las notas tienen link que abre.
- [x] No hay más de 3 notas por medio (5 si hoy es lunes).
- [ ] Con un RSS caído se ven las notas de los otros y un aviso del que falló. (Verificado en el servidor: la falla viene en `fallas` y las notas de los otros siguen. El aviso visible en `index.html` no lo vi en el navegador.)
- [x] No se usa ninguna librería externa.
- [x] Una nota publicada a las 23:30 de ayer (hora argentina) entra y una de las 00:10 de hoy no.
- [x] Cada nota queda asignada a una sección.

## Cómo probarlo
1. Abrir la página y revisar fechas y links de la lista.
2. Cambiar la fecha del sistema a un lunes (o simularlo en una prueba) y ver que entra viernes a domingo.
3. Poner una URL de RSS inválida y ver el aviso sin que se rompa el resto.

## Notas de implementación

- **Qué hice:** `noticias.py` (nuevo) lee los RSS, filtra por la ventana de ayer (los lunes, de viernes a domingo), descarta notas sin fecha o sin link http/https, aplica el tope por medio y arma la lista. `servidor.py` solo suma el import, la ruta `GET /api/noticias` y su handler (`_responder_noticias`). `index.html` suma la sección "Noticias de ayer" (lista con links, aviso de feeds caídos, mensaje si no hay notas) y la recarga al guardar preferencias.
- **Endpoint:** `GET /api/noticias` devuelve `notas` (cada una con `titulo`, `medio`, `seccion`, `fecha` en `dd/mm/aaaa hh:mm` y `link`), `fallas` (`medio`, `seccion`, `motivo`), `ventana` (`desde`/`hasta`, `hasta` inclusivo), `tope_por_medio` y `generado_en`. Siempre responde 200; las fallas van en `fallas`.
- **URLs de feeds:** en `FUENTES` de `noticias.py`, un solo lugar. Se probaron el 11/11/2026 y todas responden salvo las de Página/12 que daban 404:
  - Las rutas `pagina12.com.ar/rss/...` dan 404. Se usan las de `pagina12.com.ar/arc/outboundfeeds/rss/secciones/.../notas/` (con barra final, la forma a la que redirige la ruta sin barra).
  - Infobae internacional y tecnología responden bien pero hoy vienen **sin ítems**. No es una falla, así que no se avisa. Se dejan porque pueden traer notas en otros días.
  - Olé respondió, pero ayer no tuvo notas en su feed.
  - Quedaron fuera a propósito la portada de Página/12, el feed general de Infobae y "últimas noticias" de Ámbito. Responden, pero la spec no les asigna sección. Las rutas `/rss/...` de Página/12 se descartaron por el 404.
- **Asignación a secciones:** Política (Infobae politica, elDiarioAR, Página/12 el-país), Economía (Infobae economía, Ámbito economía y finanzas, Página/12 economía), Internacional (Página/12 el-mundo, Infobae internacional), Deportes (Olé, Infobae deportes), Tecnología (Infobae tecnología). Clarín y La Nación no se usan.
- **Decisiones a confirmar:**
  - **Internacional** no está en la lista cerrada de temas (spec 02), así que no tiene casilla. Se muestra siempre. Si preferís que dependa de otro tema (por ejemplo Política), se cambia `SECCIONES_SIEMPRE` en `noticias.py`.
  - **Tope por medio** (3, o 5 los lunes) se aplica al total del medio, no por sección, como dice la spec. Efecto: Infobae y Página/12 tienen más feeds que cupo, y se quedan las notas más nuevas. En la prueba real, Infobae aportó 1 nota a Política y 2 a Deportes; Economía de Infobae y de Página/12 quedó sin lugar. Si querés cupo por sección, hay que cambiar la regla.
  - **Feeds de temas no elegidos** no se leen, así que sus fallas tampoco se avisan.
- **Ventana y zona:** "ayer" en America/Argentina/Buenos_Aires. Un `pubDate` sin zona horaria se descarta (no se puede ubicar en la ventana). Las notas se ordenan por sección (orden fijo) y dentro de cada una, la más nueva primero.
- **Sin caché:** cada `GET /api/noticias` vuelve a leer los feeds elegidos (hasta 10 segundos de espera por feed). Si molesta, se puede agregar una copia local con vencimiento.
- **Fuera de alcance, no hecho:** dedupe contra resúmenes anteriores (spec 07), resumen con Claude, cifras.
- **Pruebas hechas:**
  - Sin red, con fechas fijas y feeds simulados (36 comprobaciones, 0 fallas): ventana de miércoles y de lunes; tope 3 y 5; 23:30 de ayer entra y 00:10 de hoy no; fecha en UTC convertida a hora de Buenos Aires; lunes con viernes 00:00 y domingo 23:59 adentro y lunes 00:00 afuera; sin fecha, fecha rota, sin link o `javascript:` descartados; link repetido una vez; fallas por 404, red, XML roto y no-RSS sin cortar las demás; temas no elegidos sin leer su feed; Internacional siempre; solo librería estándar (revisado con `ast`).
  - Con feeds reales (`urllib`): 12 notas de ayer, sin fallas, con sección, medio, fecha y link. Los 12 links responden 200 siguiendo redirecciones. Un feed inválido y uno con 404 se informan en `fallas` y no rompen el resto.
  - Servidor de prueba en el puerto 8100 (wrapper en el scratchpad, cerrado al terminar). `GET /api/noticias` responde 200 y `GET /api/noesta` responde 404.
  - El JS de `index.html` pasa `node --check`.
- **No probado en navegador:** no abrí la página. Quedan sin tildar el aviso visible de un RSS caído y la revisión visual de fechas y links en la lista. Hay que abrir `http://localhost:8000` (después de reiniciar el servidor) y mirarla.
- **Puerto 8000:** el proceso `python3 servidor.py` que sigue corriendo es el de antes y no tiene `/api/noticias`. Hay que reiniciarlo (`Ctrl+C` y `python3 servidor.py`). No lo toqué.
- **Proceso:** se marcó "en curso" antes de empezar.
