"""Errores de Mi Café: una base con mensaje en español para mostrar y código HTTP.

El detalle técnico no va en el mensaje: va al log (micafe/logs.py).
"""

from __future__ import annotations

from typing import Any


class ErrorMiCafe(Exception):
    """Base de los errores previstos. `mensaje` se muestra en la página; `codigo` es el HTTP."""

    codigo_por_defecto = 500

    def __init__(self, mensaje: str, codigo: int | None = None, extras: dict[str, Any] | None = None) -> None:
        """`mensaje` en español para la página; `codigo` HTTP (el por defecto de la clase si es None)."""
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.extras = extras or {}  # campos extra de la respuesta JSON (por ejemplo los avisos)
        self.codigo = self.codigo_por_defecto if codigo is None else codigo


class ErrorResumen(ErrorMiCafe):
    """Error al preparar el resumen o responder una pregunta (por defecto 502)."""

    codigo_por_defecto = 502


class ErrorFuente(ErrorMiCafe):
    """Una fuente externa (API, RSS) no respondió o respondió algo inválido."""

    codigo_por_defecto = 502


class ErrorAlmacenamiento(ErrorMiCafe):
    """No se pudo leer o escribir un archivo de datos/."""

    codigo_por_defecto = 500
