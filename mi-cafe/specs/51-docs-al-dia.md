# 51 - Docs al día

**Estado:** hecha

## Depende de
Todas las anteriores (43 a 50). Es la última de la tanda: no cambia código.

## Para qué
Las specs 43 a 50 cambian cosas que `CLAUDE.md`, `README.md`, `specs/README.md` y `docs/investigacion.md` describen: temas, feeds, indicadores, la cuenta de palabras, el esquema de preferencias y la pantalla. Dejar los cuatro documentos de acuerdo con el código, para que quien abra el proyecto (o Claude Code) no se guíe por reglas viejas.

## Qué tiene que hacer
1. **`CLAUDE.md`:**
   - "Estado del proyecto": specs 01 a 51 hechas (la lista exacta se cuenta al terminar) y una línea por tanda (specs 43 a 51: feeds en paralelo, más temas, subtemas, más indicadores, preferencias v2 y su pantalla).
   - Arquitectura: `HILOS_FEEDS`, los nueve temas de `config.TEMAS`, `SUBTEMAS`, `CATEGORIAS_A_TEMA`, `BCRA_IDS`, la vista `#preferencias` dentro de la misma página (sin tocar `ARCHIVOS_ESTATICOS`) y el esquema v2 de `datos/preferencias.json` (con migración desde el v1).
   - Flujo: la selección usa las preferencias (medio excluido nunca entra, preferido suma, palabras suman o restan, prioridad pesa en el plan) y el perfil de 👍/👎 suma encima; el pedido va primero.
   - **Regla del largo:** "Largo objetivo 550–650 palabras: el rango cuenta solo las notas; los indicadores van aparte y no cuentan" (decisión de la spec 46). Si se pasa, recortar desde las secciones de menor prioridad, nunca los indicadores. El mínimo solo se exige con el plan completo.
   - Regla de indicadores: la lista (dólar oficial, blue, MEP, CCL, mayorista, tarjeta, cripto, brechas, riesgo país, reservas, tasas, A3500, inflación mensual e interanual, UVA, acciones), con su fuente (DolarApi, ArgentinaDatos, BCRA v4.0) y que Bitcoin queda afuera. "Ningún número lo escribe el modelo" sigue igual. La inflación deja de estar fuera (reemplaza la decisión 1 del 11/11/2026).
   - Variables de entorno y comando de tests sin cambios; conteo de tests actualizado al final.
2. **`README.md` (raíz):** qué muestra la página hoy (indicadores nuevos, temas, pantalla de Preferencias), el mapa de carpetas (nuevos módulos si los hay) y los comandos. Sin prometer lo que no existe.
3. **`specs/README.md`:** las filas de 43 a 51 en la tabla (ya agregadas al escribirlas, con "pendiente") pasan a "hecha" a medida que se terminan; sección de decisiones tomadas de esta tanda (las nueve aprobadas); marcar como **reemplazadas** la decisión 1 del 11/11/2026 (inflación fuera de la v1) y la decisión 7 (indicadores dentro de las 550 a 650 palabras), la pregunta abierta 6 de las specs 28 a 36 (lectura en paralelo, resuelta en la 43) y cerrar las preguntas abiertas de esta tanda que se resolvieron al implementar.
4. **`docs/investigacion.md`:** tabla de feeds con los de las specs 44 y 45 (resultado de cada prueba y fecha, incluido el feed de Olé que dio `en_ventana=0`); tabla de indicadores con las casas nuevas de DolarApi, los ids verificados del BCRA v4.0 (tasas, A3500, reservas, UVA si es del BCRA) y las rutas de inflación de ArgentinaDatos; formato y controles de cada indicador nuevo (formato `32,50 % TNA`, "octubre 2026", desactualizado a más de 2 meses); quitar o corregir lo que ya no valga (por ejemplo, el feed general de elDiarioAR en Política).
5. **Skills** (`.claude/skills/resumen-diario/SKILL.md`, `corrector/SKILL.md`, `preguntas-nota/SKILL.md`): revisar que no queden menciones al largo con indicadores, a las cinco secciones fijas, ni a una lista de cifras prohibidas incompleta. Se arregla lo que falte, sin reescribir lo demás.
6. **`docs/plan.md` y `docs/preferencias.md`:** solo si dicen algo que ahora es falso (por ejemplo, los temas elegibles o el esquema de preferencias); si no, se dejan.
7. **Comprobación cruzada:** al terminar, correr la suite y revisar a mano que cada afirmación nueva de los documentos tenga respaldo en el código (nombres de constantes, rutas y endpoints, cantidades). Si un documento nombra algo que no existe, se corrige el documento (no se inventa el código).
8. Todo en español rioplatense; los mensajes de commit también.

## Fuera de alcance
Cambios de código o de tests (salvo corregir el conteo de tests en un comentario); reescribir `docs/plan.md`; documentación para otros idiomas; capturas de pantalla.

## Archivos que toca
- `CLAUDE.md`, `README.md`
- `specs/README.md`
- `docs/investigacion.md` (y `docs/plan.md` / `docs/preferencias.md` solo si hace falta)
- `.claude/skills/*/SKILL.md` (solo coherencia)

## Criterios de aceptación
- [x] `CLAUDE.md` dice que el rango de 550 a 650 palabras cuenta solo las notas y que los indicadores van aparte.
- [x] `CLAUDE.md` describe el esquema v2, la vista `#preferencias`, los ocho temas, los subtemas y los indicadores nuevos con sus fuentes.
- [x] Ningún documento dice que la inflación está fuera, que los indicadores cuentan en el largo, que Internacional entra siempre ni que son cinco los temas.
- [x] `specs/README.md` tiene las filas de 43 a 51 con su estado real, las decisiones de la tanda y las preguntas abiertas que quedan.
- [x] `docs/investigacion.md` registra cada feed e indicador nuevo con la fecha de su prueba.
- [x] Cada nombre de archivo, constante o endpoint citado en los documentos existe en el código (comprobado con una búsqueda).
- [x] `python3 -m unittest discover -s tests -t .` sigue pasando (no se tocó código).

## Tests
Sin tests nuevos. Se corre la suite completa para confirmar que no se rompió nada y se hace una búsqueda de las frases viejas en la raíz, `docs/`, `specs/` y `.claude/skills/`.

## Cómo probarlo
1. `python3 -m unittest discover -s tests -t .`.
2. Buscar en los documentos las frases viejas: "S&P Merval" (solo como ejemplo de lo prohibido), "dentro de las 550", "cinco temas", "Internacional entra siempre", "inflación: fuera de v1", "palabras_indicadores".
3. Leer `CLAUDE.md` de punta a punta y confirmar que alguien que no vio las specs entiende cómo corre y qué reglas hay.
4. Abrir los enlaces de `specs/README.md` y verificar que cada spec existe y su estado es el real.

## Notas de implementación

- Se actualizaron `CLAUDE.md` (estado 01 a 51, `HILOS_FEEDS`, `TEMAS`, `SUBTEMAS`, `CATEGORIAS_A_TEMA`, `BCRA_IDS`, `textos.py`, esquema v2 con migración, vista `#preferencias`, preferencias en la selección, lista de indicadores y regla del largo), `README.md`, `micafe/README.md`, `specs/README.md` (preguntas abiertas de 43 a 51 resueltas o vigentes, decisiones reemplazadas marcadas) y `docs/investigacion.md` (largo sin indicadores, fuentes vigentes, secciones de BCRA e inflación movidas para no cortar la tabla de indicadores).
- Son **ocho** temas, no nueve: Policiales quedó fuera de `config.TEMAS` (spec 44, un solo medio con feed válido). Los documentos dicen ocho.
- `docs/plan.md` y `docs/preferencias.md` no se tocaron (no dicen nada falso que importe). En las skills solo se completó la lista de cifras de `preguntas-nota`; `resumen-diario` y `corrector` ya estaban al día.
- La suite pasó (477 tests) y la búsqueda de frases viejas ("cinco temas", "dentro de las 550", "Internacional entra siempre", "fuera de v1", "palabras_indicadores") no encontró nada fuera de las specs históricas.
