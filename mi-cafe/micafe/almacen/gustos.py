"""Gustos de Mi Café: los 👍 y 👎 que el usuario da a notas y temas (spec 09).

Se guardan en datos/gustos.json. Cada voto tiene:
- "tipo": "nota" o "tema".
- "clave": en una nota, su link (es único por nota, como en la deduplicación);
  en un tema, su nombre (lista cerrada de config.TEMAS).
- "voto": "me_gusta" o "no_me_gusta".
- "votado_en": fecha y hora del voto, en America/Argentina/Buenos_Aires.
- En las notas, también "titulo", "medio" y "seccion" (el pedido a Claude los usa).

Quitar un voto es mandarlo con voto None: se borra la entrada.

El archivo puede traer también "reiniciado_en" (fecha ISO con zona; spec 41): los votos anteriores
se ignoran al armar el perfil, pero no se borran. Un archivo viejo sin ese campo se lee igual.

Si el archivo no existe, no se puede leer o está roto, se sigue sin gustos y se
devuelve un aviso (no se rompe nada). Al guardar un voto nuevo, un archivo roto
se reemplaza por uno nuevo.

Solo usa la librería estándar de Python (sin pip install).
"""

from __future__ import annotations

import logging

import threading
from datetime import datetime
from typing import Any

from micafe.almacen import json_seguro
from micafe.config import TEMAS, ZONA
from micafe.modelos import Voto

logger = logging.getLogger(__name__)

TIPOS = ("nota", "tema")
VOTOS = ("me_gusta", "no_me_gusta")
_candado = threading.Lock()  # el servidor atiende en hilos: leer y escribir de a uno


def _error_de_clave(tipo: Any, clave: Any) -> str | None:
    """Devuelve un mensaje si la clave no sirve para ese tipo, o None si está bien."""
    if tipo == "nota":
        if isinstance(clave, str) and clave.startswith(("http://", "https://")):
            return None
        return "La clave de una nota tiene que ser su link (http o https)."
    if tipo == "tema":
        if isinstance(clave, str) and clave in TEMAS:
            return None
        return f"Tema desconocido: {clave!r}."
    return f"Tipo desconocido: {tipo!r}."


def _texto_limpio(valor: Any) -> str:
    return " ".join(valor.split()) if isinstance(valor, str) else ""


def _votado_en_valido(valor: Any) -> bool:
    if not isinstance(valor, str):
        return False
    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError:
        return False
    return fecha.tzinfo is not None  # sin zona horaria no se puede ordenar con las demás


def _entrada_guardada_valida(entrada: Any) -> bool:
    """True si una entrada del archivo tiene la forma que espera el resto del código."""
    if not isinstance(entrada, dict):
        return False
    if _error_de_clave(entrada.get("tipo"), entrada.get("clave")):
        return False
    if entrada.get("voto") not in VOTOS or not _votado_en_valido(entrada.get("votado_en")):
        return False
    if entrada["tipo"] == "nota":
        return all(isinstance(entrada.get(campo), str) for campo in ("titulo", "medio", "seccion"))
    return True


def validar_voto(datos: Any) -> tuple[Voto | None, list[str]]:
    """Revisa el pedido de voto de la página.

    Devuelve (entrada, errores). `entrada` es None si hay errores. Si voto es None
    (quitar el voto), solo hace falta tipo y clave.
    """
    if not isinstance(datos, dict):
        return None, ["Se esperaba un objeto JSON con 'tipo', 'clave' y 'voto'."]

    tipo = datos.get("tipo")
    clave = datos.get("clave")
    voto = datos.get("voto")
    errores = []
    error_clave = _error_de_clave(tipo, clave)
    if error_clave:
        errores.append(error_clave)
    if voto is not None and voto not in VOTOS:
        errores.append(f"Voto desconocido: {voto!r}.")
    if errores:
        return None, errores

    entrada = {"tipo": tipo, "clave": clave, "voto": voto}
    if voto is None:
        return entrada, []
    if tipo == "nota":
        for campo in ("titulo", "medio", "seccion"):
            if not isinstance(datos.get(campo), str):
                errores.append(f"Falta '{campo}' de la nota.")
        if not _texto_limpio(datos.get("titulo")):
            errores.append("Falta el título de la nota.")
        if errores:
            return None, errores
        entrada["titulo"] = _texto_limpio(datos["titulo"])
        entrada["medio"] = _texto_limpio(datos["medio"])
        entrada["seccion"] = _texto_limpio(datos["seccion"])
    return entrada, []


def leer(ruta: str) -> tuple[list[Voto], str | None]:
    """Devuelve (votos, aviso). Sin archivo, o si está roto, devuelve [] y un aviso (o None)."""
    datos, estado = json_seguro.leer(ruta, None)
    if estado == json_seguro.FALTA:
        return [], None
    if estado == json_seguro.ROTO:
        aviso = "El archivo de gustos está roto. Se sigue sin gustos."
        logger.warning(f"Aviso: {aviso}")
        return [], aviso

    if not isinstance(datos, dict) or not isinstance(datos.get("votos"), list):
        aviso = "El archivo de gustos no tiene el formato esperado. Se sigue sin gustos."
        logger.warning(f"Aviso: {aviso}")
        return [], aviso

    votos = [entrada for entrada in datos["votos"] if _entrada_guardada_valida(entrada)]
    if len(votos) != len(datos["votos"]):
        aviso = "Algunos votos del archivo de gustos no se entienden y se ignoraron."
        logger.warning(f"Aviso: {aviso}")
        return votos, aviso
    return votos, None


def leer_reinicio(ruta: str) -> str | None:
    """La fecha de `reiniciado_en` del archivo, o None si no hay, no se entiende o el archivo falta o está roto."""
    datos, _ = json_seguro.leer(ruta, None)
    if isinstance(datos, dict) and _votado_en_valido(datos.get("reiniciado_en")):
        return datos["reiniciado_en"]
    return None


def _escribir(ruta: str, votos: list[Voto], reiniciado_en: str | None) -> None:
    datos: dict[str, Any] = {"votos": votos}
    if reiniciado_en:
        datos["reiniciado_en"] = reiniciado_en
    json_seguro.escribir(ruta, datos)


def reiniciar(ruta: str, ahora: datetime | None = None) -> str:
    """Marca que lo aprendido se ignora desde ahora. No borra ningún voto. Devuelve la fecha guardada.

    Un fallo de escritura sale como OSError.
    """
    momento = (ahora or datetime.now(ZONA)).isoformat(timespec="seconds")
    with _candado:
        votos, _ = leer(ruta)
        _escribir(ruta, votos, momento)
    return momento


def guardar(ruta: str, datos: Any) -> tuple[list[Voto] | None, list[str]]:
    """Registra, cambia o quita un voto. Devuelve (votos, errores).

    Hay como mucho un voto por nota o tema: votar de nuevo lo cambia, y voto None
    lo quita. El voto nuevo pasa a ser el más reciente. Un fallo de escritura sale como OSError.
    """
    entrada, errores = validar_voto(datos)
    if errores:
        return None, errores

    with _candado:
        votos, _ = leer(ruta)
        reiniciado_en = leer_reinicio(ruta)
        votos = [v for v in votos if (v["tipo"], v["clave"]) != (entrada["tipo"], entrada["clave"])]
        if entrada["voto"] is not None:
            entrada["votado_en"] = datetime.now(ZONA).isoformat(timespec="seconds")
            votos.append(entrada)
        _escribir(ruta, votos, reiniciado_en)
    return votos, []
