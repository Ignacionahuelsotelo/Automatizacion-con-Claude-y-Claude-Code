"""Utilidades de texto compartidas por todas las capas (sin dependencias del resto del paquete)."""

from __future__ import annotations

import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sin tildes ni signos, con los espacios colapsados en uno."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9ñ]+", " ", sin_tildes.lower().replace("ñ", "n")).split())
