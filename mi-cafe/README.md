# Mi Café

Resumen diario de noticias argentinas que se lee en unos 3 minutos: indicadores (dólar, riesgo país, reservas, acciones) más las notas de ayer, cada una con su link. Los números salen de APIs con fecha y fuente (nunca los escribe la IA); si falta un dato, dice "sin dato". La redacción la hace Claude con `claude -p`.

## Requisitos

- Python 3, solo librería estándar (no hay `pip install`).
- Claude Code instalado, con `claude` en el PATH (el resumen y las preguntas llaman a `claude -p`).

## Cómo correrlo

```
python3 servidor.py
```

Después abrí http://localhost:8000 (puerto fijo 8000, solo en 127.0.0.1) y tocá "Preparar el de hoy".

Si una fuente falla (API, RSS o `claude`), la página lo avisa en español y sigue andando. Los errores técnicos van a la consola del servidor.

## Tests

```
python3 -m unittest discover -s tests -t .
```

Usan `unittest`, sin red ni `claude` real (datos de `tests/fixtures/`). Para la página hay pruebas opcionales (ver abajo).

## Pruebas de la página (opcional, solo desarrollo)

Son pruebas de punta a punta con Playwright (Python). **No hacen falta para usar la app ni para los tests de arriba**; Playwright es una dependencia de desarrollo aprobada solo para esto y se instala aislada, nunca en el Python del sistema:

```
python3 -m venv .venv-dev
.venv-dev/bin/pip install -r requisitos-dev.txt
.venv-dev/bin/python -m playwright install chromium
tests/e2e/correr_e2e.sh
```

El script levanta un servidor de prueba en el puerto 8765 (cambiable con `MICAFE_E2E_PUERTO`; nunca 8000 ni 8001), con datos temporales y fuentes simuladas: no usa internet, no llama a `claude` y no toca `datos/`. Falla si la consola del navegador muestra errores o si la página pide algo fuera de localhost. `unittest` no las recoge.

## Variables de entorno (opcionales)

- `MICAFE_DATOS`: carpeta donde se guardan preferencias, gustos, copias y resúmenes. Por defecto, `datos/` en la raíz.
- `MICAFE_LOG=DEBUG`: sube el nivel del log de la consola (por defecto INFO).

El puerto y el host no se cambian.

## Cómo funciona

```
Pedido opcional de noticias (texto) + botón "Preparar el de hoy"
  -> servidor (micafe/web)
     -> fuentes: indicadores y acciones (APIs) + noticias de ayer (RSS)
     -> claude -p redacta, siguiendo las skills y tus gustos
     -> corrector (enlaces, repetidas, largo)
     -> se guarda en datos/resumenes/
  -> la página lo muestra
```

Más detalle en [docs/plan.md](docs/plan.md).

## Mapa de carpetas

- `servidor.py`: lanzador (llama a `micafe.web.servidor.main`).
- `micafe/`: el paquete (ver [micafe/README.md](micafe/README.md)).
  - `config.py`, `errores.py`, `logs.py`, `modelos.py`: configuración central, errores, logging y tipos compartidos.
  - `web/`: servidor HTTP.
  - `web/estatico/`: la página, en tres archivos (`index.html`, `estilos.css`, `app.js`), sin librerías ni build.
  - `fuentes/`: trae datos de afuera (indicadores, acciones, noticias).
  - `dominio/`: reglas de negocio (resumen, corrector, caja de preguntas, servicio).
  - `almacen/`: acceso a lo que se guarda (preferencias, gustos, resúmenes).
- `tests/`: tests con `unittest` y `tests/fixtures/`; `tests/e2e/` tiene las pruebas opcionales de la página.
- `docs/`: [plan](docs/plan.md), [investigación de fuentes](docs/investigacion.md) y [preferencias](docs/preferencias.md).
- `specs/`: una spec por tarea; arrancá por [specs/README.md](specs/README.md).
- `.claude/skills/`: las instrucciones para Claude (`resumen-diario`, `corrector`, `preguntas-nota`, más skills de desarrollo).
- `datos/`: todo lo personal (preferencias, gustos 👍/👎, copia de indicadores y acciones, resúmenes). No se versiona (está en `.gitignore`) para que nada personal se suba a GitHub. Se crea sola al usar la app.

## Fuentes de datos

DolarApi, ArgentinaDatos, BCRA (v4.0), Rava y data912 para los números; RSS de Infobae, Página/12, Ámbito, Olé y elDiarioAR para las noticias. Detalle, condiciones y fechas de verificación en [docs/investigacion.md](docs/investigacion.md).

## Cómo contribuir

1. Leé [specs/README.md](specs/README.md) y [CLAUDE.md](CLAUDE.md) (reglas que no hay que romper).
2. Tomá una spec pendiente, una por vez, y hacé solo lo que dice.
3. Todo cambio de código lleva su test con `unittest`; corré la suite antes de cerrar.
4. Todo en español rioplatense, también los mensajes de commit.
