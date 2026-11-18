"""Preferencias de Mi Café: qué indicadores y qué temas quiere ver el usuario.

Se guardan en datos/preferencias.json. Solo usa la librería estándar de Python.
"""

from __future__ import annotations

import logging
from typing import Any

from micafe.almacen import json_seguro
from micafe.modelos import Preferencias

logger = logging.getLogger(__name__)

# Lista cerrada de indicadores y temas. Lo que no esté acá no se guarda.
INDICADORES = {
    "dolar": "Dólar",
    "riesgo_pais": "Riesgo país",
    "acciones": "Acciones",
}
TEMAS = ["Política", "Economía", "Deportes", "Tecnología"]

OPCIONES = {"indicadores": INDICADORES, "temas": TEMAS}


def por_defecto() -> Preferencias:
    """Preferencias iniciales: todo elegido."""
    return {"indicadores": list(INDICADORES), "temas": list(TEMAS)}


def validar(datos: Any) -> tuple[Preferencias | None, list[str]]:
    """Revisa un diccionario de preferencias.

    Devuelve (preferencias, errores). Si hay errores, preferencias es None y
    errores es una lista de mensajes para mostrar. Un valor desconocido hace
    que se rechace todo: no se guarda nada a medias.
    """
    if not isinstance(datos, dict):
        return None, ["Se esperaba un objeto JSON con 'indicadores' y 'temas'."]

    errores = []
    limpias = {}
    for clave, conocidos in (("indicadores", INDICADORES), ("temas", TEMAS)):
        valor = datos.get(clave)
        if not isinstance(valor, list):
            errores.append(f"'{clave}' tiene que ser una lista.")
            continue
        for elegido in valor:
            if not (isinstance(elegido, str) and elegido in conocidos):
                errores.append(f"Valor desconocido en '{clave}': {elegido!r}.")
        # Se guarda en el orden de la lista de conocidos, sin repetidos.
        limpias[clave] = [c for c in conocidos if c in valor]

    if errores:
        return None, errores
    return limpias, []


def leer(ruta: str) -> tuple[Preferencias, str | None]:
    """Devuelve (preferencias, aviso).

    Si el archivo no existe, usa los valores por defecto sin aviso. Si está
    roto o no sirve, usa los valores por defecto y devuelve un aviso (que
    también se imprime en la consola del servidor).
    """
    datos, estado = json_seguro.leer(ruta, None)
    if estado == json_seguro.FALTA:
        return por_defecto(), None

    if estado == json_seguro.ROTO:
        aviso = "El archivo de preferencias está roto. Se usan los valores por defecto."
    else:
        limpias, errores = validar(datos)
        if not errores:
            return limpias, None
        aviso = "El archivo de preferencias no es válido (" + " ".join(errores) + "). Se usan los valores por defecto."

    logger.warning(f"Aviso: {aviso}")
    return por_defecto(), aviso


def guardar(ruta: str, datos: Any) -> tuple[Preferencias | None, list[str]]:
    """Valida y guarda las preferencias. Devuelve (preferencias, errores)."""
    limpias, errores = validar(datos)
    if errores:
        return None, errores

    json_seguro.escribir(ruta, limpias)
    return limpias, []
