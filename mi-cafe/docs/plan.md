# Plan: Mi Café

Fuente de investigación: [investigacion.md](investigacion.md)

## Ajuste de diseño importante
La investigación indica que **los números no los puede escribir la IA** (inventa cifras o usa datos viejos). Por eso el servidor trae los números directo de las fuentes oficiales y Claude (`claude -p`, con tu plan) solo redacta las noticias y responde preguntas. Ningún número sale de la IA.

## Cómo funciona, en una imagen mental
Mi Café es como una cafetería con cuatro roles:
- **El mozo** (la página web) muestra todo y recibe tus pedidos.
- **La cocina** (el servidor en Python) hace el trabajo cuando el mozo se lo pide.
- **El cocinero** (Claude, llamado con `claude -p`) escribe los resúmenes y responde preguntas.
- **El libro de recetas** (las skills del proyecto) le dice al cocinero cómo hacer cada cosa.

## Las piezas

| # | Pieza | Qué hace | Dónde vive |
|---|---|---|---|
| 1 | **Preferencias** | Guardan qué indicadores querés (dólar, riesgo país, acciones) y qué temas (política, economía, deportes…) | `micafe/almacen/preferencias.py` (guarda en `datos/preferencias.json`) |
| 2 | **Buscador de indicadores** | Pide los números a las fuentes oficiales: DolarApi, ArgentinaDatos, BCRA. Guarda cada valor con su **fecha y fuente**. Si falta un dato, dice "sin dato" | `micafe/fuentes/indicadores.py` y `acciones.py` |
| 3 | **Buscador de noticias** | Lee los RSS (Infobae, Página/12, Ámbito, Olé, elDiarioAR), se queda solo con las notas de **ayer** (los lunes, de viernes a domingo) y descarta las que no tienen fecha | `micafe/fuentes/noticias.py` |
| 4 | **El cocinero** | El servidor le pasa las notas y le pide el resumen con `claude -p`. Sigue las instrucciones de las skills | `micafe/dominio/resumen.py` (llama a `claude -p`) |
| 5 | **Skills del proyecto** | Las reglas: largo (550–650 palabras), estructura por secciones, 1–2 frases por nota, "por qué importa", máximo 3 notas por medio, nombres vigentes (MSCI Merval, Télam cerrada) | `.claude/skills/` |
| 6 | **Corrector** | Revisa el resumen: enlace en cada nota, sin repetidas de los últimos 3 días, largo correcto | `micafe/dominio/corrector.py` + skill `corrector` |
| 7 | **Memoria de gustos** | Guarda los 👍 y 👎 y se los pasa al cocinero la próxima vez | `micafe/almacen/gustos.py` (guarda en `datos/gustos.json`) |
| 8 | **Archivo de resúmenes** | Guarda cada resumen con su fecha para no repetir y poder releerlo | `micafe/almacen/resumenes.py` (guarda en `datos/resumenes/`) |
| 9 | **La página** | Tres archivos estáticos (HTML, CSS y JS) sin librerías ni build: indicadores arriba, noticias con link, 👍/👎, botón "Preparar el de hoy" y caja de preguntas | `micafe/web/estatico/` |

La carpeta `datos/` queda en `.gitignore`, así que nada personal se sube a GitHub. Solo se usa Python estándar, sin `pip install`.

## Cómo se conectan
1. Abrís la página y el servidor te manda tus preferencias y el último resumen guardado.
2. Tocás **"Preparar el de hoy"**. La cocina trae indicadores (pieza 2) y noticias de ayer (pieza 3).
3. Le pasa las noticias al cocinero (4), que sigue el libro de recetas (5) y tus gustos (7).
4. El corrector (6) revisa, el resumen se guarda (8) y la página lo muestra.
5. Cada 👍/👎 viaja al servidor y queda en `datos/gustos.json`.
6. La **caja de preguntas** manda tu pregunta y la nota a Claude, que responde solo con lo que dice esa nota.

## Orden de construcción (cada paso se prueba solo)

1. **Esqueleto:** carpetas, `.gitignore` con `datos/` y un servidor que muestra "Hola Café" en el navegador.
   *Prueba:* abrís `localhost` y ves la página.
2. **Preferencias:** guardar y leer tus elecciones.
   *Prueba:* cambiás una, reiniciás y sigue ahí.
3. **Indicadores:** dólar, riesgo país y reservas con fecha y fuente.
   *Prueba:* los números coinciden con una web de consulta.
4. **Noticias:** leer los RSS y filtrar por fecha.
   *Prueba:* ves una lista de notas de ayer con sus links.
5. **Primer resumen con Claude:** `claude -p` con una skill simple.
   *Prueba:* resumen corto con links.
6. **Skills completas y corrector:** estructura, largo, reglas anti-errores.
   *Prueba:* 550–650 palabras, sin repetidos, todo con enlace.
7. **Página completa:** diseño, botón "Preparar el de hoy" y estado de "cargando".
   *Prueba:* un clic arma todo de punta a punta.
8. **👍/👎:** guardar gustos y usarlos.
   *Prueba:* votás, preparás otro y notás el cambio.
9. **Caja de preguntas:** preguntar sobre una noticia.
   *Prueba:* la respuesta se apoya en esa nota.
10. **Acciones y pulido:** acciones conocidas y manejo de errores.
    *Prueba:* si una fuente falla, la página avisa y no se rompe.

## Riesgos
- **Merval y acciones:** no hay API oficial gratuita estable. Fuentes aprobadas (18/11/2026): Rava (página histórica, scraping) para el MSCI Merval y data912 (API no oficial) para GGAL, YPFD y PAMP; sin Yahoo ni BYMADATA. El respaldo del índice en data912 está desactivado (ningún endpoint lo trae). Ambas pueden cambiar sin aviso: se valida la fecha y, si no hay dato confiable, queda "sin dato".
- **Medios con muro de pago:** Clarín y La Nación solo se usan para detectar temas, no como único enlace.
- **Tiempos:** `claude -p` puede tardar. La página muestra "preparando…".
