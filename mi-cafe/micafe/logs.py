"""Configuración del log de Mi Café (librería estándar). Se llama una sola vez en el arranque.

Sale a la consola del servidor con hora, nivel y módulo. Nivel INFO por defecto;
la variable opcional MICAFE_LOG=DEBUG lo sube para diagnóstico.
"""

from __future__ import annotations

import logging
import os

FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"
FORMATO_HORA = "%H:%M:%S"


def configurar() -> None:
    """Deja el log de `micafe` andando en la consola; se puede llamar más de una vez sin duplicar salida."""
    nivel = os.environ.get("MICAFE_LOG", "INFO").strip().upper()
    if nivel not in ("DEBUG", "INFO"):
        nivel = "INFO"
    raiz = logging.getLogger("micafe")
    if not any(getattr(h, "_micafe", False) for h in raiz.handlers):
        manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter(FORMATO, FORMATO_HORA))
        manejador._micafe = True
        raiz.addHandler(manejador)
        raiz.propagate = False
    raiz.setLevel(nivel)
