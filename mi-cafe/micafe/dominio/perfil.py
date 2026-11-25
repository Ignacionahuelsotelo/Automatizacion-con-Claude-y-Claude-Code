"""Perfil de gustos (spec 41): resume los votos 👍/👎 en puntajes por sección, medio y término.

Módulo puro: recibe la lista de votos y la fecha de hoy por parámetro; no lee disco ni la hora.
Nunca loguea votos, títulos ni términos.

Cada voto pesa `0,5 ** (días / VIDA_MEDIA_GUSTOS_DIAS)` (👍 suma, 👎 resta). Un voto a un tema vale
`MULTIPLICADOR_VOTO_TEMA` veces; uno a una nota suma a su sección y a su medio con peso 1 y a los
términos de su título con `PESO_TERMINO_TITULO`. Todo puntaje se acota a +-TOPE_PERFIL.
"""

from __future__ import annotations

from datetime import datetime

from micafe.config import (
    MAXIMO_PRIORIDADES, MULTIPLICADOR_VOTO_TEMA, PESO_TERMINO_TITULO, TOPE_PERFIL, UMBRAL_PRIORIDAD,
    VIDA_MEDIA_GUSTOS_DIAS,
)
from micafe.dominio.seleccion import terminos_de_titulo
from micafe.modelos import Perfil, Voto

SEGUNDOS_POR_DIA = 86400


def perfil_vacio() -> Perfil:
    """Un perfil sin ningún puntaje."""
    return {"secciones": {}, "medios": {}, "terminos": {}, "votos_contados": 0}


def peso_por_antiguedad(dias: float) -> float:
    """Cuánto pesa un voto de hace `dias` días: 1 hoy, 0,5 a los 14, 0,25 a los 28."""
    return 0.5 ** (dias / VIDA_MEDIA_GUSTOS_DIAS)


def _fecha(texto: object) -> datetime | None:
    """La fecha ISO con zona, o None si es ilegible o no tiene zona (no se puede comparar)."""
    if not isinstance(texto, str):
        return None
    try:
        fecha = datetime.fromisoformat(texto)
    except ValueError:
        return None
    return fecha if fecha.tzinfo is not None else None


def _sumar(puntajes: dict[str, float], clave: str, valor: float) -> None:
    if clave:
        puntajes[clave] = puntajes.get(clave, 0.0) + valor


def calcular(votos: list[Voto], hoy: datetime, reiniciado_en: str | None = None) -> Perfil:
    """El perfil de los votos al día de `hoy` (con zona). Ignora los votos anteriores a `reiniciado_en`,
    los de fecha futura o ilegible y los mal formados."""
    desde = _fecha(reiniciado_en)
    perfil = perfil_vacio()
    for voto in votos:
        if not isinstance(voto, dict):
            continue
        fecha = _fecha(voto.get("votado_en"))
        if fecha is None or fecha > hoy or (desde is not None and fecha <= desde):
            continue
        signo = {"me_gusta": 1.0, "no_me_gusta": -1.0}.get(voto.get("voto"))
        if signo is None:
            continue
        peso = signo * peso_por_antiguedad((hoy - fecha).total_seconds() / SEGUNDOS_POR_DIA)
        if voto.get("tipo") == "tema":
            _sumar(perfil["secciones"], str(voto.get("clave", "")), peso * MULTIPLICADOR_VOTO_TEMA)
        elif voto.get("tipo") == "nota":
            _sumar(perfil["secciones"], str(voto.get("seccion", "")), peso)
            _sumar(perfil["medios"], str(voto.get("medio", "")), peso)
            for termino in terminos_de_titulo(str(voto.get("titulo", ""))):
                _sumar(perfil["terminos"], termino, peso * PESO_TERMINO_TITULO)
        else:
            continue
        perfil["votos_contados"] += 1
    for grupo in ("secciones", "medios", "terminos"):
        perfil[grupo] = {k: round(max(-TOPE_PERFIL, min(TOPE_PERFIL, v)), 4) for k, v in perfil[grupo].items()}
    return perfil


def _etiqueta(tipo: str, nombre: str, positivo: bool) -> str:
    if tipo == "seccion":
        return f"Te interesa más {nombre}" if positivo else f"Te interesa menos {nombre}"
    if tipo == "medio":
        return f"Te interesan las notas de {nombre}" if positivo else f"Poco interés en el medio {nombre}"
    return f"Te interesa lo que habla de «{nombre}»" if positivo else f"Poco interés en «{nombre}»"


def prioridades(perfil: Perfil, maximo: int = MAXIMO_PRIORIDADES, con_terminos: bool = True) -> list[dict[str, object]]:
    """Las prioridades principales, de más a menos fuerte: `{"tipo", "nombre", "signo", "etiqueta"}`.

    `signo` es 1 o -1 (sin puntajes). Solo cuentan los puntajes que pasan de UMBRAL_PRIORIDAD en valor absoluto.
    """
    grupos = [("seccion", perfil["secciones"]), ("medio", perfil["medios"])]
    if con_terminos:
        grupos.append(("termino", perfil["terminos"]))
    todas = [(abs(v), tipo, nombre, v > 0) for tipo, puntajes in grupos for nombre, v in puntajes.items()
             if abs(v) >= UMBRAL_PRIORIDAD]
    todas.sort(key=lambda t: (-t[0], t[1], t[2]))
    return [{"tipo": tipo, "nombre": nombre, "signo": 1 if positivo else -1, "etiqueta": _etiqueta(tipo, nombre, positivo)}
            for _, tipo, nombre, positivo in todas[:maximo]]


def lineas_para_pedido(perfil: Perfil, maximo: int = MAXIMO_PRIORIDADES) -> list[str]:
    """Las prioridades como líneas de texto para Claude. Solo secciones y medios: nunca títulos ni términos."""
    return [f"- {p['etiqueta']}." for p in prioridades(perfil, maximo, con_terminos=False)]
