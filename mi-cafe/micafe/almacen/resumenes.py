"""Resúmenes guardados en datos/resumenes/AAAA-MM-DD.json (specs 08 y 21)."""

from __future__ import annotations

import os
import re
from datetime import datetime

from micafe.almacen import json_seguro
from micafe.config import CANTIDAD_PREVIOS, CARPETA_RESUMENES, ZONA
from micafe.modelos import Chequeo, Indicador, PlanDelDia, ResumenGuardado

RE_ARCHIVO_RESUMEN = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def guardar(texto: str, indicadores_mostrados: list[Indicador], chequeo: Chequeo, ahora: datetime,
            carpeta: str = CARPETA_RESUMENES, pedido: str | None = None,
            pedido_sin_notas: bool | None = None, plan: PlanDelDia | None = None) -> ResumenGuardado:
    """Guarda el resumen de hoy en AAAA-MM-DD.json y devuelve el registro.

    `pedido` (spec 35) se guarda como campo "pedido" solo si hay; sin pedido no se escribe.

    Solo escribe el archivo de la fecha de hoy (no pisa otros días). Un fallo de
    escritura sale como OSError.
    """
    ahora = ahora.astimezone(ZONA)
    registro = {
        "fecha": ahora.date().isoformat(),
        "generado_en": ahora.strftime("%d/%m/%Y %H:%M"),
        "indicadores": indicadores_mostrados,
        "texto": texto,
        "chequeo": chequeo,
    }
    if pedido:
        registro["pedido"] = pedido
    if pedido_sin_notas is not None:
        registro["pedido_sin_notas"] = pedido_sin_notas  # spec 39
    if plan is not None:
        registro["plan"] = plan  # spec 40
    json_seguro.escribir(os.path.join(carpeta, f"{registro['fecha']}.json"), registro)
    return registro


def _nombres(carpeta: str) -> list[str]:
    """Nombres de archivos de resumen, del más nuevo al más viejo."""
    if not os.path.isdir(carpeta):
        return []
    return sorted((n for n in os.listdir(carpeta) if RE_ARCHIVO_RESUMEN.match(n)), reverse=True)


def leer_ultimo(carpeta: str = CARPETA_RESUMENES) -> ResumenGuardado | None:
    """Devuelve el resumen más reciente, o None si no hay ninguno válido.

    Un archivo roto, borrado o con otra forma se saltea.
    """
    for nombre in _nombres(carpeta):
        datos, estado = json_seguro.leer(os.path.join(carpeta, nombre), None)
        if (estado is None and isinstance(datos, dict) and isinstance(datos.get("fecha"), str)
                and isinstance(datos.get("texto"), str) and datos["texto"].strip()):
            return datos
    return None


def leer_previos(carpeta: str = CARPETA_RESUMENES, cantidad: int = CANTIDAD_PREVIOS,
                 anteriores_a: str | None = None) -> list[str]:
    """Devuelve el texto de los últimos resúmenes guardados (uno por día).

    Si `anteriores_a` trae una fecha AAAA-MM-DD, solo mira los días anteriores
    (al preparar de nuevo el de hoy no se compara contra el de hoy).
    """
    nombres = [n for n in _nombres(carpeta) if anteriores_a is None or n < f"{anteriores_a}.json"][:cantidad]
    textos = []
    for nombre in nombres:
        datos, _ = json_seguro.leer(os.path.join(carpeta, nombre), None)
        texto = datos.get("texto") if isinstance(datos, dict) else None
        if isinstance(texto, str) and texto.strip():
            textos.append(texto)
    return textos
