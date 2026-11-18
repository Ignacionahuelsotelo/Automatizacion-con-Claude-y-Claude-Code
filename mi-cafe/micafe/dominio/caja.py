"""Caja de preguntas de Mi Café: preguntas sobre una nota del resumen (spec 10).

La página manda la fecha del resumen, el link de la nota (la que la persona tocó)
y la pregunta. El servidor busca esa nota en el resumen guardado
(datos/resumenes/AAAA-MM-DD.json), no en lo que mande la página, y le pasa a
Claude solo ese bloque (texto, medio, fecha y link) junto con la pregunta.

Las reglas de respuesta viven en .claude/skills/preguntas-nota/SKILL.md, no acá.
La llamada a Claude usa resumen.ejecutar_claude: mismo mecanismo y mismo timeout
de 5 minutos que el resumen (decisión 13 de specs/README.md).

Ningún número lo escribe el modelo: si la respuesta trae una cifra que no está en
la nota, no se muestra y se avisa.

Solo usa la librería estándar de Python (sin pip install).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from micafe.almacen import json_seguro
from micafe.config import ARCHIVO_SKILL_PREGUNTAS, CARPETA_PROYECTO, CARPETA_RESUMENES
from micafe.dominio import corrector
from micafe.dominio import resumen
from micafe.modelos import PedidoDePregunta, RespuestaDePregunta

logger = logging.getLogger(__name__)

ARCHIVO_SKILL = ARCHIVO_SKILL_PREGUNTAS
MAXIMO_PREGUNTA = 500  # caracteres; la página usa el mismo límite
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_CIFRA = re.compile(r"\d+(?:[.,]\d+)*")


def validar_pedido(datos: Any) -> tuple[PedidoDePregunta | None, list[str]]:
    """Revisa el pedido de la página. Devuelve (pedido, errores); pedido es None si hay errores."""
    if not isinstance(datos, dict):
        return None, ["Se esperaba un objeto JSON con 'fecha', 'link' y 'pregunta'."]

    errores = []
    fecha = datos.get("fecha")
    if not isinstance(fecha, str) or not RE_FECHA.match(fecha):
        errores.append("La fecha del resumen no es válida.")
    link = datos.get("link")
    if not isinstance(link, str) or not link.startswith(("http://", "https://")):
        errores.append("El link de la nota no es válido.")
    pregunta = datos.get("pregunta")
    if not isinstance(pregunta, str) or not pregunta.strip():
        errores.append("Escribí una pregunta.")
    elif len(pregunta.strip()) > MAXIMO_PREGUNTA:
        errores.append(f"La pregunta es muy larga (máximo {MAXIMO_PREGUNTA} caracteres).")
    if errores:
        return None, errores
    return {"fecha": fecha, "link": link, "pregunta": " ".join(pregunta.split())}, []


def nota_del_resumen(fecha: str, link: str, carpeta: str = CARPETA_RESUMENES) -> list[str] | None:
    """Devuelve las líneas del bloque de la nota (título primero, link al final) o None si no está."""
    ruta = os.path.join(carpeta, f"{fecha}.json")
    datos, _ = json_seguro.leer(ruta, None)
    texto = datos.get("texto") if isinstance(datos, dict) else None
    if not isinstance(texto, str):
        return None
    for lineas in corrector.notas_del_texto(texto):
        if link in lineas:
            return lineas
    return None


def cifras(texto: str | None) -> set[str]:
    """Las cifras del texto sin separadores: "1.234,50" queda como "123450"."""
    return {re.sub(r"[.,]", "", cifra) for cifra in RE_CIFRA.findall(texto or "")}


def armar_pedido(instrucciones: str, texto_nota: str, pregunta: str) -> str:
    """Junta las reglas de la skill con la nota (tal como está en el resumen) y la pregunta."""
    return (
        instrucciones
        + "\n\n## Nota\n\n" + texto_nota + "\n"
        + "\n## Pregunta\n\n" + pregunta + "\n"
    )


def responder(datos: Any, ruta_skill: str = ARCHIVO_SKILL, carpeta: str = CARPETA_PROYECTO) -> RespuestaDePregunta:
    """Devuelve {"respuesta": texto, "link": link} para la pregunta sobre la nota.

    Levanta resumen.ErrorResumen si el pedido no sirve (400), si no está la nota
    (404), si `claude` falla o tarda más de 5 minutos, o si la respuesta trae
    cifras que no están en la nota.
    """
    pedido, errores = validar_pedido(datos)
    if errores:
        raise resumen.ErrorResumen(" ".join(errores), codigo=400)

    lineas_nota = nota_del_resumen(pedido["fecha"], pedido["link"])
    if lineas_nota is None:
        raise resumen.ErrorResumen("No encuentro esa nota en el resumen guardado.", codigo=404)
    texto_nota = "\n".join(lineas_nota)

    try:
        instrucciones = resumen.leer_instrucciones(ruta_skill)
    except OSError as error:
        logger.warning(f"Aviso: no se pudo leer la skill de preguntas. Detalle: {error}")
        raise resumen.ErrorResumen("No se pudo leer la skill de preguntas (.claude/skills/preguntas-nota/SKILL.md).")

    respuesta = resumen.ejecutar_claude(armar_pedido(instrucciones, texto_nota, pedido["pregunta"]), carpeta)
    if cifras(respuesta) - cifras(texto_nota):
        raise resumen.ErrorResumen(
            "La respuesta traía cifras que no están en la nota, así que no se muestra. "
            "Probá preguntar de otra forma."
        )
    return {"respuesta": respuesta, "link": pedido["link"]}
