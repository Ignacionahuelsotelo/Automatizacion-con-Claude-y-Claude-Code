# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado del proyecto

Mi Café es un resumen diario de noticias argentinas (indicadores + notas de ayer). **Ya hay código**: las specs 01 a 51 están hechas (ver `specs/README.md`). El refactor (specs 17 a 25) ordenó el código en el paquete `micafe/`, sumó tests con `unittest`, configuración central, logging y errores unificados, y separó la página en tres archivos. La spec 26 dejó pruebas e2e opcionales en `tests/e2e/` (Playwright, solo como dependencia de desarrollo en `.venv-dev/`); las specs 28 a 36 sumaron chequeo de Claude, progreso en tiempo real, votos en el resumen, más feeds y el pedido de noticias en texto. Las specs 37 a 42 adaptaron el resumen (selección por puntaje, plan de secciones y perfil de gustos). Las specs 43 a 51 sumaron: lectura de feeds en paralelo (`HILOS_FEEDS`), más temas (8 en `config.TEMAS`) y subtemas de Deportes, más indicadores (dólar mayorista, tarjeta y cripto, A3500, tasas, inflación, UVA), preferencias v2 con su pantalla (`#preferencias`) y estos documentos al día. La suite tiene 477 tests (24/11/2026).

Las acciones tienen fuente: el MSCI Merval sale de Rava (con respaldo en data912, hoy desactivado porque ningún endpoint trae el índice) y GGAL, YPFD y PAMP de data912. Cada una cae en "sin dato" si su fuente falla.

## Cómo correrlo

- Requisitos: Python 3 (solo librería estándar, sin `pip install`) y Claude Code instalado, con `claude` en el PATH (el resumen y las preguntas llaman a `claude -p`).
- Comando: `python3 servidor.py`, y abrir http://localhost:8000 (puerto fijo 8000, solo en 127.0.0.1).
- Si una fuente falla (API, RSS o `claude`), la página lo avisa en español y sigue andando. Los errores técnicos van a la consola del servidor.
- Tests: `python3 -m unittest discover -s tests -t .` (sin red ni `claude`: usan datos de `tests/fixtures/` y carpetas temporales). Todo cambio de código lleva su test. La página tiene pruebas e2e opcionales en `tests/e2e/` (requieren Playwright); el resto se prueba a mano siguiendo "Cómo probarlo" de cada spec en `specs/`.
- Variables de entorno opcionales: `MICAFE_DATOS` (carpeta de datos, por defecto `datos/` en la raíz) y `MICAFE_LOG=DEBUG` (sube el nivel del log; por defecto INFO). El puerto y el host no se cambian.
- `datos/` (preferencias, gustos, copia de indicadores y resúmenes) no se versiona.

- `README.md`: presentación del proyecto, cómo correrlo y mapa de carpetas.
- `docs/plan.md`: plan aprobado (piezas, conexión y orden de construcción en 10 pasos, cada uno con su prueba).
- `docs/investigacion.md`: fuentes (RSS, APIs), formato y controles anti-errores. Es la referencia para las skills y para el servidor.
- `docs/preferencias.md`: preferencias de trabajo (español; el resto sin completar).

## Arquitectura

- **Servidor local en Python, solo librería estándar** (sin `pip install`). `servidor.py` en la raíz solo lanza `micafe.web.servidor.main`. Trae indicadores y RSS por su cuenta y llama a Claude con `claude -p` (usa el plan del usuario).
- **Paquete `micafe/`**:
  - `config.py`: única fuente de verdad de puerto, zona, rutas, timeouts, URLs y topes.
  - `errores.py` (jerarquía `ErrorMiCafe`), `logs.py` (logging), `modelos.py` (tipos compartidos) y `textos.py` (`normalizar_texto`: minúsculas, sin tildes ni signos).
  - En `config.py` viven también: `HILOS_FEEDS` (feeds que se leen a la vez), `TEMAS` (los 8 temas elegibles, en orden; Policiales quedó afuera porque solo Infobae tiene feed válido), `TEMAS_POR_DEFECTO` (los 5 originales, únicos tildados sin archivo de preferencias), `SUBTEMAS` (de Deportes: Fútbol argentino, Fútbol internacional, Tenis, Básquet, Automovilismo y Otros), `CATEGORIAS_A_TEMA` (reclasificación por `<category>`; hoy ningún feed la usa), `BCRA_IDS` (ids de las series del BCRA v4.0) y los pesos del puntaje y de las preferencias.
  - `web/`: HTTP (`servidor.py`) y la página en `web/estatico/` (`index.html`, `estilos.css`, `app.js`).
  - `fuentes/`: trae datos de afuera (`indicadores.py`, `acciones.py`, `noticias.py`, `utilidades.py`).
  - `dominio/`: reglas de negocio (`resumen.py`, `corrector.py`, `caja.py`, `pedido.py`, `progreso.py`, `seleccion.py`, `perfil.py`, `servicio.py`).
  - `almacen/`: lo que se guarda en `datos/` (`preferencias.py`, `gustos.py`, `resumenes.py`, `json_seguro.py`). No se llama `datos` para no confundirlo con la carpeta `datos/` de la raíz.
- **Regla de dependencias (sin ciclos):** `web` -> `dominio` (hoy solo `dominio/servicio.py`, que orquesta); `dominio` -> `fuentes` y `almacen`, nunca `web` (dentro de `dominio`, `perfil.py` usa `seleccion.py`, que lee `almacen/preferencias.py`); `fuentes` -> `almacen` (solo `json_seguro`), nunca `dominio` ni `web`; `almacen` no importa a ninguna otra capa. Todos pueden importar `config`, `errores`, `logs`, `modelos` y `textos` (no dependen de ninguna capa). Hoy se cumple por revisión (no hay un test que lo controle).
- **Página:** tres archivos estáticos propios (`index.html`, `estilos.css`, `app.js`) en `micafe/web/estatico/`, sin librerías externas ni build. El servidor sirve solo una lista cerrada de archivos (`ARCHIVOS_ESTATICOS` en `config.py`). La pantalla de Preferencias es la vista `#preferencias` dentro de la misma página (temas con prioridad, subtemas, medios preferidos y excluidos, palabras a seguir y evitar, indicadores); no suma archivos ni toca `ARCHIVOS_ESTATICOS`.
- **Skills del proyecto** (`.claude/skills/`): las instrucciones para armar el resumen viven ahí (`resumen-diario`, `corrector`, `preguntas-nota`), no en el código Python.
- **`datos/`**: todo lo personal (preferencias, gustos 👍/👎 con `reiniciado_en` opcional, resúmenes). Los votos pesan menos con el tiempo (vida media de 14 días); `GET /api/perfil` muestra lo aprendido y `POST /api/perfil/reiniciar` (con `{"confirmar": true}`) lo ignora sin borrar votos. Está en `.gitignore`.
- **`datos/preferencias.json` (esquema v2, `version: 2`, `almacen/preferencias.py`):** `temas` (por tema: `activo` y `prioridad` alta, normal o baja), `subtemas`, `medios` (`preferidos` y `excluidos`), `palabras` (`seguir` y `evitar`) e `indicadores` (lista cerrada: `dolar`, `dolar_otros`, `riesgo_pais`, `reservas`, `tasas`, `inflacion`, `acciones`). Un archivo v1 (dos listas, `indicadores` y `temas`) se migra en memoria al leer y no se reescribe hasta el primer guardado; si no tenía `version`, migra con `reservas` tildada y los grupos nuevos destildados. No hay opción de largo del resumen.
- **`tests/`**: tests con `unittest` y `tests/fixtures/`. **`specs/`**: una spec por vez, empezando por `specs/README.md`.

Flujo: (opcional) la persona escribe qué noticias quiere ver hoy (hasta 500 caracteres, se guarda solo dentro del resumen del día) y toca el botón "Preparar el de hoy" -> `POST /api/resumen` (con `pedido` opcional) responde 202 y arma en un hilo (estado en memoria en `GET /api/resumen/estado`, que la página consulta cada 1,5 s) -> servidor comprueba Claude, trae indicadores (APIs) y noticias de ayer (RSS filtrados por fecha) -> el código ordena las candidatas con un puntaje (el pedido, la frescura, las preferencias y el perfil de gustos; `dominio/seleccion.py` y `dominio/perfil.py`), les pasa a Claude las 40 mejores y marca con `[pedido]` las que encajan (si ninguna encaja, el resumen guarda `pedido_sin_notas`) -> `claude -p` redacta siguiendo las skills y las prioridades aprendidas -> corrector -> se guarda en `datos/resumenes/` -> la página lo muestra, con el bloque plegable "Cómo se armó hoy" (plan por sección, ajustes por gustos y botón "Reiniciar lo aprendido"), el aviso "Tu pedido no encontró notas de ayer" y la lista "Noticias de ayer" ordenada por el puntaje del servidor, con etiquetas (`motivos`). `GET /api/preferencias` trae `opciones.secciones` (de `config.TEMAS`): el front no copia la lista de secciones.

Preferencias en la selección: un medio excluido nunca entra (ni a las candidatas ni a "Noticias de ayer"; los resúmenes ya guardados no se tocan); un medio preferido suma; las palabras a seguir suman y las a evitar restan; los subtemas elegidos suman y los no elegidos restan; la prioridad del tema (alta o baja) pesa en el plan de secciones. Su aporte está acotado (`MAXIMO_PUNTAJE_PREFERENCIAS`), el perfil de 👍/👎 suma encima (acotado por `MAXIMO_PUNTAJE_PERFIL`) y el pedido de hoy va siempre primero.

## Convenciones de código

- Toda constante de configuración (rutas, timeouts, URLs, topes) va en `micafe/config.py`; los módulos reciben las rutas por parámetro y usan `config` como valor por defecto.
- Logging con `logger = logging.getLogger(__name__)`, sin `print`. El detalle técnico va al log y a la consola; la página recibe solo mensajes en español sin texto técnico. Nunca se loguea contenido de resúmenes ni de preguntas.
- Errores: los previstos son subclases de `ErrorMiCafe` (`micafe/errores.py`); el servidor las atrapa en un solo lugar. Nada de `except Exception` sin un comentario que lo justifique.
- Tipos (anotaciones) y docstrings en español rioplatense.
- Tests con `unittest` para todo cambio, sin red ni `claude` real.

## Reglas que no hay que romper

- Todo en español rioplatense: respuestas, textos de la página, comentarios y también los mensajes de commit.
- Ningún número sin fuente y fecha; si no hay dato confiable, "sin dato".
- Toda noticia va con link.
- Montos en formato `$ 1.234,50` (punto para miles, coma para decimales).
- Nada de dependencias externas sin preguntar antes.

- **Ningún número lo escribe el modelo.** Indicadores salen de las APIs (DolarApi, ArgentinaDatos, BCRA v4.0; la v3 está dada de baja) con fecha y fuente; si falta, "sin dato".
- **Indicadores que muestra la página** (cada grupo es elegible en preferencias): dólar oficial, blue, MEP y CCL con sus brechas (DolarApi); otros dólares: mayorista, tarjeta y cripto (DolarApi) y A3500 (BCRA); riesgo país (ArgentinaDatos); reservas (BCRA); tasas BADLAR, TAMAR y plazo fijo a 30 días (BCRA); inflación mensual e interanual y UVA (ArgentinaDatos; la mensual y la interanual se muestran como mes, p. ej. "octubre 2026", y se marcan desactualizadas a partir de 2 meses de atraso); acciones (MSCI Merval de Rava; GGAL, YPFD y PAMP de data912). Bitcoin queda afuera (el dólar cripto de DolarApi sí entra). La inflación ya no está fuera: reemplaza la decisión 1 del 11/11/2026.
- Ventana de noticias: solo ayer (los lunes, de viernes a domingo); descartar notas sin fecha.
- Cada noticia lleva enlace; máximo 3 notas por medio en el resumen (la lista de candidatas "Noticias de ayer" se cuenta aparte, por medio y sección, y puede traer más; el corrector cuenta el tope sobre el resumen entero); deduplicar contra los últimos 3 resúmenes.
- Largo objetivo 550–650 palabras: cuenta solo las notas; los indicadores van aparte (el mínimo solo se exige si el plan de secciones quedó completo; el máximo siempre). Si se pasa, recortar desde las secciones de menor prioridad del plan (pedido, pesos y orden de los temas), nunca los indicadores. El código calcula cuántas notas lleva cada sección (`seleccion.plan_de_secciones`, 9 notas objetivo) y la skill y el corrector siguen ese plan.
- Nombres vigentes: el índice es **MSCI Merval** (desde 19/10/2026, no "S&P Merval"); Télam ya no existe como agencia.
- ArgentinaDatos pide máximo una consulta cada 3 horas por serie: guardar copia local en `datos/`.
- Clarín y La Nación (muro de pago) solo para detectar temas, no como único enlace.
