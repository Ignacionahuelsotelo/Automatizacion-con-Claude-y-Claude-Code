# Paquete `micafe/`

- `web/`: lo que habla HTTP (`servidor.py`, clase `Manejador` y `main`).
- `fuentes/`: trae datos de afuera (`indicadores.py`, `acciones.py`, `noticias.py`).
- `dominio/`: reglas de negocio (`resumen.py`, `corrector.py`, `caja.py`).
- `config.py`: única fuente de verdad de puerto, zona, rutas, timeouts, URLs y topes. `MICAFE_DATOS` (opcional) cambia la carpeta de datos; puerto y host no se sobrescriben.
- `almacen/`: código de acceso a lo que se guarda (`preferencias.py`, `gustos.py`). Se llama `almacen` y no `datos` para no confundirlo con la carpeta `datos/` de la raíz, que no se versiona.

Dependencias permitidas: web -> dominio, fuentes, almacen; dominio -> (nada de web); fuentes -> (nada de dominio ni web). Todos pueden importar `micafe/config.py` (configuración central, ver abajo). `fuentes/acciones.py` e `indicadores.py` comparten helpers de fechas, formato de montos y copia local desde `fuentes/utilidades.py` (ya no se importan entre sí).
