# 27 - README del proyecto y CLAUDE.md al día

**Estado:** hecha

## Depende de
18 a 25 (se cierra al final, cuando la estructura ya es la definitiva). Si la 26 no se hizo, se documenta que las pruebas del front son manuales.

## Para qué
Que cualquiera (o Claude Code) pueda entender, correr y probar el proyecto leyendo dos archivos, y que `CLAUDE.md` describa la estructura real y no la "prevista".

## Qué tiene que hacer
1. Crear `README.md` en la raíz, en español rioplatense, con: qué es Mi Café, requisitos (Python 3 estándar y `claude` en el PATH), cómo correrlo (`python3 servidor.py` y http://localhost:8000), cómo correr los tests (`python3 -m unittest discover -s tests -t .`), mapa de carpetas (`micafe/web`, `fuentes`, `dominio`, almacén, `estatico`, `tests`, `docs`, `specs`, `.claude/skills`), qué es `datos/` y por qué no se versiona, variables de entorno opcionales (`MICAFE_DATOS`, `MICAFE_LOG`), fuentes de datos con enlace a `docs/investigacion.md`, y cómo contribuir (leer `specs/README.md`, una spec por vez).
2. Un diagrama de texto corto del flujo (botón, servidor, fuentes, `claude -p`, corrector, guardado, página), tomado de `docs/plan.md`.
3. Actualizar `CLAUDE.md`:
   - "Estado del proyecto": refactor hecho (specs 17 a 27, según corresponda).
   - "Cómo correrlo": comando de tests y variables de entorno.
   - "Arquitectura prevista" pasa a "Arquitectura": estructura real de carpetas, capas y regla de dependencias entre ellas (web, dominio, fuentes y almacén, sin ciclos).
   - Agregar convenciones de código: configuración en `micafe/config.py`, logging y errores como en la spec 20, tipos y docstrings en español, tests con `unittest` para todo cambio.
   - Mantener textualmente todas las reglas de "Reglas que no hay que romper".
4. Revisar `docs/plan.md` solo en lo que quedó desactualizado por la estructura (por ejemplo, la columna "Dónde vive" de las piezas). No tocar la sección "Riesgos": es de la spec 16.
5. Sin enlaces rotos: todos los enlaces relativos de ambos archivos apuntan a archivos que existen.

## Fuera de alcance
Cambios de código, documentación en otros idiomas, sitio de documentación, la spec 16 (docs de fuentes de acciones y skills).

## Skills a usar
- `verification-before-completion`: probar uno por uno los comandos que figuran en el README antes de darlo por bueno.
- `find-skills` solo si falta alguna skill para documentar.

## Archivos que toca
- `README.md` (nuevo)
- `CLAUDE.md`
- `docs/plan.md` (solo "Dónde vive")

## Criterios de aceptación
- [x] Los comandos del README funcionan: tests (191 OK) y arranque con `MICAFE_DATOS`/`MICAFE_LOG` sirviendo los tres estáticos con 200 (probado en el puerto 8011; ver notas). No se probó en una máquina limpia ni el flujo con `claude`.
- [x] El mapa de carpetas coincide con lo que hay en el disco.
- [x] Las reglas de `CLAUDE.md` están intactas: la sección "Reglas que no hay que romper" no se tocó (el archivo no está versionado, se verificó por construcción: solo se reemplazó lo anterior a ella).
- [x] No quedan menciones a `index.html` único ni a módulos sueltos en la raíz como estructura vigente.
- [x] Todo en español rioplatense.

## Cómo probarlo
1. Seguir el README desde cero: clonar, correr, abrir la página, correr los tests.
2. Comparar el mapa de carpetas con `ls` de cada carpeta.
3. `git diff CLAUDE.md`: solo cambian las secciones de estado, cómo correrlo y arquitectura; la de reglas queda igual.

## Notas de implementación
- Se creó `README.md` y se reescribieron en `CLAUDE.md` las secciones de estado, cómo correrlo, arquitectura (antes "prevista") y se sumó "Convenciones de código". En `docs/plan.md` solo cambió la columna "Dónde vive".
- La spec 26 figura como pendiente (espera Playwright); se documenta que la página se prueba a mano.
- La regla de dependencias entre capas se documentó como es hoy (`web` -> `dominio.servicio`; `dominio` -> `fuentes`/`almacen`; `fuentes` -> `almacen.json_seguro`); no hay un test que la controle y así se aclara. `micafe/README.md` quedó más simple que eso y no se tocó (fuera de los archivos de la spec).
- En el puerto 8000 había un servidor viejo ya corriendo (PID 36123, arrancado antes) que responde 500 en `/`; por eso el arranque se probó en el puerto 8011. Conviene reiniciarlo.
