"""Ayudas compartidas por las fuentes (indicadores y acciones): fechas, formato de montos y copia local.

Salieron de indicadores.py en la spec 19 sin cambiar su comportamiento. Solo librería estándar.
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError

from micafe.almacen import json_seguro
from micafe.config import ZONA

logger = logging.getLogger(__name__)


def numero(valor: Any) -> float | None:
    """Devuelve el número como float, o None si no es un número finito."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    if not math.isfinite(valor):
        return None
    return float(valor)


def dia(texto: Any) -> date | None:
    """Convierte 'AAAA-MM-DD' en date, o None si no es una fecha válida."""
    if not isinstance(texto, str):
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def momento(texto: Any) -> datetime | None:
    """Convierte una fecha con hora (ISO, con zona) en datetime de Buenos Aires."""
    if not isinstance(texto, str):
        return None
    try:
        momento = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None
    if momento.tzinfo is None:
        return None  # sin zona horaria no sabemos a qué día corresponde
    return momento.astimezone(ZONA)


def dia_de(momento: datetime | date) -> date:
    """El día de un datetime (o la misma fecha si ya es un date)."""
    return momento.date() if isinstance(momento, datetime) else momento


def mostrar_fecha(momento: datetime | date) -> str:
    """'dd/mm/aaaa hh:mm' si trae hora, 'dd/mm/aaaa' si es solo el día."""
    if isinstance(momento, datetime):
        return momento.strftime("%d/%m/%Y %H:%M")
    return momento.strftime("%d/%m/%Y")


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def mostrar_mes(fecha: datetime | date) -> str | None:
    """'octubre 2026' (mes en español, sin día y sin `locale`). Devuelve None si no es una fecha."""
    if not isinstance(fecha, date):  # datetime es subclase de date
        return None
    return f"{MESES[fecha.month - 1]} {fecha.year}"


def meses_entre(fecha: date, hoy: date) -> int:
    """Meses calendario de diferencia entre el mes de `fecha` y el de `hoy` (septiembre a noviembre = 2)."""
    return (hoy.year * 12 + hoy.month) - (fecha.year * 12 + fecha.month)


def dias_habiles_entre(dia: date, hoy: date) -> int:
    """Cuenta los días hábiles (lunes a viernes) posteriores a `dia`, hasta `hoy`.

    No descuenta feriados: es una aproximación de la regla "más de 1 día hábil".
    """
    cuenta = 0
    while dia < hoy:
        dia += timedelta(days=1)
        if dia.weekday() < 5:
            cuenta += 1
    return cuenta


# --- Formato ---------------------------------------------------------------

def formatear_numero(numero: float, decimales: int) -> str:
    """1234.5 -> '1.234,50' (punto para miles, coma para decimales)."""
    texto = f"{numero:,.{decimales}f}"
    return texto.translate(str.maketrans({",": ".", ".": ","}))


def monto(numero: float) -> str:
    """Formato de montos de CLAUDE.md: `$ 1.234,50` (punto para miles, coma para decimales)."""
    return f"$ {formatear_numero(numero, 2)}"


def motivo(error: BaseException) -> str:
    """Explica en español por qué falló una consulta (sin texto técnico)."""
    if isinstance(error, HTTPError):
        if error.code == 410:
            return "la versión de la API fue dada de baja (HTTP 410), hay que actualizar la dirección"
        return f"respondió con error HTTP {error.code}"
    if isinstance(error, TimeoutError) or (isinstance(error, URLError) and isinstance(error.reason, TimeoutError)):
        return "tardó demasiado en responder"
    if isinstance(error, OSError):
        return "no se pudo conectar"
    if isinstance(error, ValueError):
        return "respondió algo que no es JSON válido"
    return "respondió algo que no se entiende"


def leer_copia(ruta: str) -> dict[str, Any]:
    """Lee la copia local de una fuente; si falta o está rota, devuelve {} (se vuelve a consultar)."""
    datos, estado = json_seguro.leer(ruta, {})
    if estado == json_seguro.ROTO:
        logger.warning("Aviso: la copia local de indicadores está rota. Se vuelve a consultar.")
        return {}
    return datos if isinstance(datos, dict) else {}


def guardar_copia(ruta: str, copia: dict[str, Any]) -> None:
    """Guarda la copia local. Si no se puede escribir, avisa y sigue."""
    try:
        json_seguro.escribir(ruta, copia)
    except OSError as error:
        logger.warning(f"Aviso: no se pudo guardar la copia local de indicadores. Detalle: {error}")
