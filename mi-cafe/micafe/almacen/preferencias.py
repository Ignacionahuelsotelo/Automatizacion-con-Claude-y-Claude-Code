"""Preferencias de Mi Café (esquema v2, spec 49): temas con prioridad, subtemas, medios, palabras e indicadores.

Se guardan en datos/preferencias.json. El formato viejo (v1: dos listas, `indicadores` y `temas`)
se migra solo al leer y no se reescribe hasta el primer guardado. Solo usa la librería estándar.
"""

from __future__ import annotations

import logging
from typing import Any

from micafe.almacen import json_seguro
from micafe.config import (
    FUENTES_RSS, MAXIMO_CARACTERES_PALABRA, MAXIMO_PALABRAS_PREFERENCIA, PRIORIDADES_TEMA, SUBTEMAS, TEMAS,
    TEMAS_POR_DEFECTO,
)
from micafe.modelos import Preferencias
from micafe.textos import normalizar_texto

logger = logging.getLogger(__name__)

# Lista cerrada de indicadores (los temas salen de config.TEMAS). Lo que no esté acá no se guarda.
INDICADORES = {
    "dolar": "Dólar",
    "dolar_otros": "Otros dólares (mayorista, tarjeta, cripto y A3500)",
    "riesgo_pais": "Riesgo país",
    "reservas": "Reservas internacionales",
    "tasas": "Tasas (BADLAR, TAMAR y plazo fijo)",
    "inflacion": "Inflación (mensual, interanual y UVA)",
    "acciones": "Acciones",
}

VERSION_ARCHIVO = 2
PRIORIDAD_NORMAL = "normal"


def medios_disponibles() -> list[str]:
    """Los medios que existen en FUENTES_RSS, sin repetidos y en orden alfabético (sin tildes)."""
    return sorted({f["medio"] for f in FUENTES_RSS}, key=normalizar_texto)


def temas_activos(prefs: Preferencias | dict[str, Any] | None) -> list[str]:
    """Los temas con `activo: true`, en el orden de config.TEMAS.

    Por compatibilidad también acepta el formato viejo (`temas` como lista de nombres).
    """
    if not prefs:
        return []
    temas = prefs.get("temas")
    if isinstance(temas, dict):
        return [t for t in TEMAS if isinstance(temas.get(t), dict) and temas[t].get("activo") is True]
    return [t for t in TEMAS if isinstance(temas, list) and t in temas]


def prioridades_de_temas(prefs: Preferencias | dict[str, Any] | None) -> dict[str, str]:
    """Tema -> prioridad, solo de los que no son "normal" (con el formato viejo, siempre vacío)."""
    temas = (prefs or {}).get("temas")
    if not isinstance(temas, dict):
        return {}
    return {t: v["prioridad"] for t, v in temas.items()
            if isinstance(v, dict) and v.get("prioridad") in PRIORIDADES_TEMA and v["prioridad"] != PRIORIDAD_NORMAL}


def _completar_temas(activos: list[str]) -> dict[str, dict[str, Any]]:
    return {t: {"activo": t in activos, "prioridad": PRIORIDAD_NORMAL} for t in TEMAS}


def por_defecto() -> Preferencias:
    """Preferencias iniciales: todos los indicadores y los temas originales (los nuevos se tildan a mano)."""
    return {"version": VERSION_ARCHIVO, "temas": _completar_temas(TEMAS_POR_DEFECTO), "subtemas": [],
            "medios": {"preferidos": [], "excluidos": []}, "palabras": {"seguir": [], "evitar": []},
            "indicadores": list(INDICADORES)}


def _lista_conocida(valor: Any, clave: str, conocidos: Any, errores: list[str]) -> list[str]:
    """Elementos de `valor` que están en `conocidos`, en el orden de `conocidos` y sin repetidos."""
    if not isinstance(valor, list):
        errores.append(f"'{clave}' tiene que ser una lista.")
        return []
    for elegido in valor:
        if not (isinstance(elegido, str) and elegido in conocidos):
            errores.append(f"Valor desconocido en '{clave}': {elegido!r}.")
    return [c for c in conocidos if c in valor]


def _limpiar_palabras(valor: Any, clave: str, errores: list[str]) -> list[str]:
    """Palabras limpias: espacios colapsados, sin vacías ni repetidas (sin mayúsculas ni tildes)."""
    if not isinstance(valor, list) or not all(isinstance(p, str) for p in valor):
        errores.append(f"'{clave}' tiene que ser una lista de textos.")
        return []
    limpias: list[str] = []
    vistas: set[str] = set()
    for palabra in valor:
        texto = " ".join(palabra.split())
        clave_normalizada = normalizar_texto(texto)
        if not clave_normalizada or clave_normalizada in vistas:
            continue
        if len(texto) > MAXIMO_CARACTERES_PALABRA:
            errores.append(f"Cada palabra puede tener hasta {MAXIMO_CARACTERES_PALABRA} caracteres.")
            continue
        vistas.add(clave_normalizada)
        limpias.append(texto)
    if len(limpias) > MAXIMO_PALABRAS_PREFERENCIA:
        errores.append(f"Podés cargar hasta {MAXIMO_PALABRAS_PREFERENCIA} palabras.")
    return limpias


def _sub_objeto(datos: dict[str, Any], clave: str, errores: list[str]) -> dict[str, Any]:
    valor = datos.get(clave)
    if valor is None:
        return {}
    if not isinstance(valor, dict):
        errores.append(f"'{clave}' tiene que ser un objeto.")
        return {}
    return valor


def _temas_v2(valor: Any, errores: list[str]) -> dict[str, dict[str, Any]]:
    """Valida el objeto `temas` y lo completa con todos los de config.TEMAS."""
    if not isinstance(valor, dict):
        errores.append("'temas' tiene que ser un objeto.")
        return {}
    limpios = _completar_temas([])
    for nombre, tema in valor.items():
        if nombre not in TEMAS:
            errores.append(f"Valor desconocido en 'temas': {nombre!r}.")
            continue
        if not isinstance(tema, dict):
            errores.append(f"El tema {nombre!r} tiene que ser un objeto con 'activo' y 'prioridad'.")
            continue
        activo = tema.get("activo", False)
        prioridad = tema.get("prioridad", PRIORIDAD_NORMAL)
        if not isinstance(activo, bool):
            errores.append(f"'activo' del tema {nombre!r} tiene que ser verdadero o falso.")
        if prioridad not in PRIORIDADES_TEMA:
            errores.append(f"Prioridad desconocida en el tema {nombre!r}: {prioridad!r}.")
        if isinstance(activo, bool) and prioridad in PRIORIDADES_TEMA:
            limpios[nombre] = {"activo": activo, "prioridad": prioridad}
    return limpios


def validar(datos: Any, exigir_tema: bool = True) -> tuple[Preferencias | None, list[str]]:
    """Revisa un diccionario de preferencias, en v2 o en el formato viejo (v1, que se migra).

    Devuelve (preferencias, errores). Si hay errores, preferencias es None y
    errores es una lista de mensajes para mostrar. Con `exigir_tema`, tiene que
    haber al menos un tema activo. Un valor desconocido hace que se rechace todo:
    no se guarda nada a medias. No se acepta ningún campo de largo del resumen.
    """
    if not isinstance(datos, dict):
        return None, ["Se esperaba un objeto JSON con las preferencias."]
    version = datos.get("version")
    if isinstance(version, int) and not isinstance(version, bool) and version > VERSION_ARCHIVO:
        return None, ["Las preferencias son de una versión más nueva que la que entiende esta app."]

    errores: list[str] = []
    if isinstance(datos.get("temas"), list):  # v1: se migra
        nombres = _lista_conocida(datos["temas"], "temas", TEMAS, errores)
        temas = _completar_temas(nombres)
        subtemas: list[str] = []
        preferidos: list[str] = []
        excluidos: list[str] = []
        seguir: list[str] = []
        evitar: list[str] = []
    else:
        temas = _temas_v2(datos.get("temas"), errores)
        subtemas = _lista_conocida(datos.get("subtemas", []), "subtemas", list(SUBTEMAS), errores)
        medios = _sub_objeto(datos, "medios", errores)
        existentes = medios_disponibles()
        for clave in ("preferidos", "excluidos"):
            if isinstance(medios.get(clave), list) and len(medios[clave]) > len(existentes):
                errores.append(f"Hay más medios en '{clave}' de los que existen.")
        preferidos = _lista_conocida(medios.get("preferidos", []), "medios.preferidos", existentes, errores)
        excluidos = _lista_conocida(medios.get("excluidos", []), "medios.excluidos", existentes, errores)
        repetidos = [m for m in preferidos if m in excluidos]
        if repetidos:
            errores.append("Un medio no puede estar entre los preferidos y los excluidos a la vez: "
                           + ", ".join(repetidos) + ".")
        palabras = _sub_objeto(datos, "palabras", errores)
        seguir = _limpiar_palabras(palabras.get("seguir", []), "palabras.seguir", errores)
        evitar = _limpiar_palabras(palabras.get("evitar", []), "palabras.evitar", errores)
    indicadores = _lista_conocida(datos.get("indicadores"), "indicadores", list(INDICADORES), errores)

    if exigir_tema and not errores and not any(t["activo"] for t in temas.values()):
        errores.append("Elegí al menos un tema.")
    if errores:
        return None, errores
    return {"version": VERSION_ARCHIVO, "temas": temas, "subtemas": subtemas,
            "medios": {"preferidos": preferidos, "excluidos": excluidos},
            "palabras": {"seguir": seguir, "evitar": evitar}, "indicadores": indicadores}, []


def leer(ruta: str) -> tuple[Preferencias, str | None]:
    """Devuelve (preferencias, aviso).

    Si el archivo no existe, usa los valores por defecto sin aviso. Si está roto, es de una
    versión futura o no sirve, usa los valores por defecto y devuelve un aviso (que también va
    al log del servidor). Un archivo en formato v1 se migra en memoria; no se reescribe.
    """
    datos, estado = json_seguro.leer(ruta, None)
    if estado == json_seguro.FALTA:
        return por_defecto(), None

    if estado == json_seguro.ROTO:
        aviso = "El archivo de preferencias está roto. Se usan los valores por defecto."
    elif (isinstance(datos, dict) and isinstance(datos.get("version"), int) and not isinstance(datos["version"], bool)
          and datos["version"] > VERSION_ARCHIVO):
        aviso = "El archivo de preferencias es de una versión más nueva. Se usan los valores por defecto."
    else:
        # Un archivo viejo con temas vacíos se lee igual; la exigencia es al guardar.
        limpias, errores = validar(datos, exigir_tema=False)
        if not errores and limpias is not None:
            # Un archivo viejo (v1 sin "version") no tenía la opción de reservas: se traían siempre.
            # Para no cambiarle el resumen, se migra con las reservas tildadas (spec 47).
            if isinstance(datos.get("temas"), list) and "version" not in datos and "reservas" not in limpias["indicadores"]:
                limpias["indicadores"] = [c for c in INDICADORES if c in limpias["indicadores"] or c == "reservas"]
            return limpias, None
        aviso = "El archivo de preferencias no es válido (" + " ".join(errores) + "). Se usan los valores por defecto."

    logger.warning(f"Aviso: {aviso}")
    return por_defecto(), aviso


def guardar(ruta: str, datos: Any) -> tuple[Preferencias | None, list[str]]:
    """Valida y guarda las preferencias (v2 o v1, que se migra). Devuelve (preferencias, errores)."""
    limpias, errores = validar(datos)
    if errores or limpias is None:
        return None, errores

    json_seguro.escribir(ruta, limpias)
    return limpias, []
