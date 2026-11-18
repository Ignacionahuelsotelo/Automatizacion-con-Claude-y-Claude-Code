"""Pedido de noticias en texto libre (spec 35).

El texto lo escribe la persona y va a un prompt: se trata como dato, nunca como
instrucción. Acá se valida y se normaliza; el armado del prompt está en
resumen.armar_pedido. El texto del pedido nunca se loguea.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from micafe.config import MAXIMO_PEDIDO_USUARIO


def normalizar(texto: str) -> str:
    """Una sola línea: sin caracteres de control y con los espacios y saltos de línea colapsados en un espacio."""
    una_linea = " ".join(texto.split())
    return "".join(c for c in una_linea if unicodedata.category(c) != "Cc").strip()


def validar_pedido(valor: Any) -> tuple[str | None, list[str]]:
    """Devuelve `(texto_limpio | None, errores)`. Ausente, None o solo espacios es "sin pedido" (None, [])."""
    if valor is None:
        return None, []
    if not isinstance(valor, str):
        return None, ["El pedido tiene que ser un texto."]
    texto = normalizar(valor)
    if not texto:
        return None, []
    if len(texto) > MAXIMO_PEDIDO_USUARIO:
        return None, [f"El pedido es muy largo (máximo {MAXIMO_PEDIDO_USUARIO} caracteres)."]
    return texto, []
