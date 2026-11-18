"""Noticias de Mi Café: las notas de ayer leídas de los RSS de los medios.

"Ayer" se toma en America/Argentina/Buenos_Aires. Los lunes la ventana es de
viernes a domingo. Se descartan las notas sin fecha (o con una fecha que no se
pueda leer) y las que no tengan link http o https. Cada nota lleva medio,
sección, fecha y link.

Si un feed no responde o no es un RSS válido, se sigue con los demás y la falla
queda en "fallas" para avisarla en la página.

Solo usa la librería estándar de Python (sin pip install).
"""

from __future__ import annotations

import logging
import http.client
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, time, timedelta
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.error import HTTPError, URLError

from micafe.config import (
    AGENTE, CANDIDATAS_POR_MEDIO_Y_SECCION, CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES,
    FUENTES_RSS as FUENTES, SECCIONES, TIMEOUT_NOTICIAS as TIMEOUT_SEGUNDOS, TOPE_POR_MEDIO,
    TOPE_POR_MEDIO_LUNES, ZONA,
)

from micafe.modelos import ConteoDeFuente, FuenteRSS, NotaDeFeed, ResultadoNoticias

logger = logging.getLogger(__name__)

# Secciones que no son tema de preferencias: se muestran siempre.
# (Internacional no está en la lista cerrada de temas de la spec 02.)
SECCIONES_SIEMPRE = ["Internacional"]

# Los feeds (FUENTES) viven en micafe/config.py, con las demás URLs.


def ventana(ahora: datetime) -> tuple[datetime, datetime, int]:
    """Devuelve (desde, hasta, tope) para la fecha de hoy.

    `tope` es el máximo de notas por medio del resumen (no el cupo de candidatas).

    `desde` está incluido y `hasta` no. Normalmente es ayer de 0 a 24 h. Si hoy
    es lunes, va de viernes 00:00 a domingo 24:00.
    Regla de CLAUDE.md ("Ventana de noticias"): solo ayer, y los lunes de viernes a domingo.
    """
    hoy = ahora.astimezone(ZONA).date()
    if hoy.weekday() == 0:
        inicio = hoy - timedelta(days=3)
        tope = TOPE_POR_MEDIO_LUNES
    else:
        inicio = hoy - timedelta(days=1)
        tope = TOPE_POR_MEDIO
    desde = datetime.combine(inicio, time.min, tzinfo=ZONA)
    hasta = datetime.combine(hoy, time.min, tzinfo=ZONA)
    return desde, hasta, tope


def fecha_de(texto: str | None) -> datetime | None:
    """Convierte un pubDate RSS a datetime en Buenos Aires. None si no se puede leer."""
    if not texto:
        return None
    try:
        fecha = parsedate_to_datetime(texto)
    except (TypeError, ValueError, IndexError):
        return None
    if fecha.tzinfo is None:
        return None  # sin zona horaria no se puede ubicar en la ventana
    return fecha.astimezone(ZONA)


def _texto(item: ET.Element, etiqueta: str) -> str:
    elemento = item.find(etiqueta)
    if elemento is None or elemento.text is None:
        return ""
    return elemento.text.strip()


def notas_del_feed(contenido: bytes, fuente: FuenteRSS) -> list[NotaDeFeed]:
    """Lee un RSS (bytes) y devuelve sus notas con fecha, sin filtrar por ventana.

    Lanza ValueError si el documento no es un RSS, o SyntaxError (ET.ParseError)
    si el XML no sirve.
    """
    raiz = ET.fromstring(contenido)
    if raiz.find("./channel") is None:
        raise ValueError("el documento no es un RSS")

    notas = []
    for item in raiz.findall("./channel/item"):
        titulo = _texto(item, "title")
        link = _texto(item, "link")
        fecha = fecha_de(_texto(item, "pubDate"))
        if not titulo or not fecha:
            continue
        if not link.startswith(("http://", "https://")):
            continue
        notas.append({
            "titulo": titulo,
            "link": link,
            "fecha": fecha,
            "medio": fuente["medio"],
            "seccion": fuente["seccion"],
        })
    return notas


def leer_feed(url: str) -> bytes:
    """Descarga un feed y devuelve los bytes. Lanza error si falla."""
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as respuesta:
        return respuesta.read()


def _motivo(error: BaseException) -> str:
    """Explica en español por qué falló un feed (sin texto técnico)."""
    if isinstance(error, HTTPError):
        if error.code == 410:
            return "la versión del feed fue dada de baja (HTTP 410)"
        return f"respondió con error HTTP {error.code}"
    if isinstance(error, TimeoutError) or (isinstance(error, URLError) and isinstance(error.reason, TimeoutError)):
        return "tardó demasiado en responder"
    if isinstance(error, OSError):
        return "no se pudo conectar"
    if isinstance(error, SyntaxError):
        return "el XML no es válido"
    if isinstance(error, ValueError):
        return "el documento no es un RSS válido"
    return "no se pudo leer"


def obtener(temas: list[str], ahora: datetime | None = None, fuentes: list[FuenteRSS] = FUENTES,
            leer: Callable[[str], bytes] = leer_feed) -> ResultadoNoticias:
    """Devuelve {"notas": [...], "fallas": [...], "por_fuente": [...], "ventana": {...}, "tope_por_medio": n, "generado_en": "..."}.

    `temas` son las preferencias de temas. Solo se leen los feeds de las
    secciones elegidas (más las que se muestran siempre). `leer` se puede
    cambiar para probar sin red.
    """
    ahora = ahora or datetime.now(ZONA)
    desde, hasta, tope = ventana(ahora)
    secciones_activas = set(temas) | set(SECCIONES_SIEMPRE)

    candidatas = []
    fallas = []
    por_fuente: list[ConteoDeFuente] = []
    feed_de_link: dict[str, ConteoDeFuente] = {}  # a qué feed se le anota cada link (gana el primero)
    for fuente in fuentes:
        if fuente["seccion"] not in secciones_activas:
            continue
        try:
            notas = notas_del_feed(leer(fuente["url"]), fuente)
        except (OSError, ValueError, SyntaxError, http.client.HTTPException) as error:
            fallas.append({
                "medio": fuente["medio"],
                "seccion": fuente["seccion"],
                "motivo": _motivo(error),
            })
            logger.warning(f"Aviso: no se pudo leer {fuente['url']} ({_motivo(error)}). Detalle: {error}")
            continue
        en_ventana = [n for n in notas if desde <= n["fecha"] < hasta]
        conteo: ConteoDeFuente = {
            "medio": fuente["medio"], "seccion": fuente["seccion"],
            "leidas": len(notas), "en_ventana": len(en_ventana), "elegidas": 0,
        }
        por_fuente.append(conteo)
        for nota in en_ventana:
            feed_de_link.setdefault(nota["link"], conteo)
        candidatas.extend(en_ventana)

    # Sin repetidos por link (gana el primer feed en el orden de FUENTES).
    vistos = set()
    unicas = []
    for nota in candidatas:
        if nota["link"] in vistos:
            continue
        vistos.add(nota["link"])
        unicas.append(nota)

    # Las más nuevas primero; después se aplica el cupo por (medio, sección). El tope por
    # medio del resumen (`tope`) se cumple al elegir y lo controla el corrector.
    cupo = CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES if tope == TOPE_POR_MEDIO_LUNES else CANDIDATAS_POR_MEDIO_Y_SECCION
    unicas.sort(key=lambda n: n["fecha"], reverse=True)
    por_medio_y_seccion = {}
    elegidas = []
    for nota in unicas:
        clave = (nota["medio"], nota["seccion"])
        cantidad = por_medio_y_seccion.get(clave, 0)
        if cantidad >= cupo:
            continue
        por_medio_y_seccion[clave] = cantidad + 1
        elegidas.append(nota)
        feed_de_link[nota["link"]]["elegidas"] += 1

    # Solo conteos en el log: ni títulos ni links.
    for c in por_fuente:
        logger.info(f"Feed {c['medio']} / {c['seccion']}: leidas={c['leidas']}, "
                    f"en_ventana={c['en_ventana']}, elegidas={c['elegidas']}")

    # Orden de la lista: por sección (orden fijo) y dentro de cada una, la más nueva primera.
    elegidas.sort(key=lambda n: (SECCIONES.index(n["seccion"]), -n["fecha"].timestamp()))

    ultimo_dia = hasta - timedelta(days=1)
    return {
        "notas": [
            {
                "titulo": n["titulo"],
                "medio": n["medio"],
                "seccion": n["seccion"],
                "fecha": n["fecha"].strftime("%d/%m/%Y %H:%M"),
                "link": n["link"],
            }
            for n in elegidas
        ],
        "fallas": fallas,
        "por_fuente": por_fuente,
        "ventana": {
            "desde": desde.strftime("%d/%m/%Y"),
            "hasta": ultimo_dia.strftime("%d/%m/%Y"),
        },
        "tope_por_medio": tope,
        "generado_en": ahora.astimezone(ZONA).strftime("%d/%m/%Y %H:%M"),
    }
