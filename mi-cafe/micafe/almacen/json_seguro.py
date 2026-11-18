"""Lectura tolerante y escritura atómica de JSON en datos/ (spec 21).

Es la única implementación: preferencias, gustos, copias de indicadores y
acciones y resúmenes la usan, así un archivo roto nunca tira el servidor.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

FALTA = "falta"
ROTO = "roto"


def leer(ruta: str, por_defecto: Any) -> tuple[Any, str | None]:
    """Devuelve (datos, estado). `estado` es None si se leyó bien, FALTA o ROTO.

    Si el archivo no existe o no es un JSON válido, `datos` es `por_defecto`.
    Cada módulo arma su propio aviso en español según el estado.
    """
    try:
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo), None
    except FileNotFoundError:
        return por_defecto, FALTA
    except (OSError, ValueError) as error:
        logger.debug(f"Detalle del archivo {os.path.basename(ruta)}: {error}")
        return por_defecto, ROTO


def escribir(ruta: str, datos: Any) -> None:
    """Escribe `datos` como JSON de forma atómica: archivo temporal y después os.replace.

    El temporal es único por escritura (mkstemp en la misma carpeta), así dos
    escrituras simultáneas al mismo archivo no se pisan (spec 28).

    Crea la carpeta si no existe. Si falla, deja el archivo anterior intacto, no deja
    el temporal y propaga el OSError (quien llama decide el aviso).
    """
    carpeta = os.path.dirname(ruta)
    os.makedirs(carpeta, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(dir=carpeta, prefix=os.path.basename(ruta) + ".", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
    except BaseException:
        try:
            os.remove(temporal)
        except OSError:
            pass
        raise
