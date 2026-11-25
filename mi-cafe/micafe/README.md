# Paquete `micafe/`

- `web/`: lo que habla HTTP (`servidor.py`, clase `Manejador` y `main`).
- `fuentes/`: trae datos de afuera (`indicadores.py`, `acciones.py`, `noticias.py`).
- `dominio/`: reglas de negocio (`resumen.py`, `corrector.py`, `caja.py`, `pedido.py`, `progreso.py`, `seleccion.py`, `perfil.py`, `servicio.py`).
- `config.py`: única fuente de verdad de puerto, zona, rutas, timeouts, URLs y topes. `MICAFE_DATOS` (opcional) cambia la carpeta de datos; puerto y host no se sobrescriben.
- `almacen/`: código de acceso a lo que se guarda (`preferencias.py`, `gustos.py`, `resumenes.py`, `json_seguro.py`). `textos.py` (normalización de texto) no depende de ninguna capa. Se llama `almacen` y no `datos` para no confundirlo con la carpeta `datos/` de la raíz, que no se versiona.

Dependencias permitidas: web -> dominio, fuentes, almacen; dominio -> (nada de web); fuentes -> (nada de dominio ni web). Todos pueden importar `micafe/config.py` (configuración central, ver abajo). `fuentes/acciones.py` e `indicadores.py` comparten helpers de fechas, formato de montos y copia local desde `fuentes/utilidades.py` (ya no se importan entre sí).
