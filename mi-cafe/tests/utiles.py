"""Ayudas compartidas por los tests de Mi Café (solo librería estándar)."""

import contextlib
import io
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

CARPETA_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

# Miércoles 18/11/2026 al mediodía: "ayer" es el martes 17/11/2026.
MIERCOLES = datetime(2026, 11, 18, 12, 0, tzinfo=ZONA)
# Lunes 16/11/2026: la ventana de noticias va de viernes 13 a domingo 15.
LUNES = datetime(2026, 11, 16, 12, 0, tzinfo=ZONA)


def fixture(nombre):
    """Lee un archivo de tests/fixtures/ como texto."""
    with open(os.path.join(CARPETA_FIXTURES, nombre), encoding="utf-8") as archivo:
        return archivo.read()


def fixture_json(nombre):
    return json.loads(fixture(nombre))


def silenciar(caso):
    """Tapa lo que la app imprime en consola (avisos y trazas) mientras corre el test."""
    salida, errores = io.StringIO(), io.StringIO()
    pila = contextlib.ExitStack()
    pila.enter_context(contextlib.redirect_stdout(salida))
    pila.enter_context(contextlib.redirect_stderr(errores))
    caso.addCleanup(pila.close)
    return salida, errores


def rss(items):
    """Arma un RSS (bytes) con items [(titulo, link, pubDate)]; link o fecha en None se omiten."""
    partes = ['<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>x</title>']
    for titulo, link, fecha in items:
        partes.append("<item>")
        partes.append(f"<title>{titulo}</title>")
        if link:
            partes.append(f"<link>{link}</link>")
        if fecha:
            partes.append(f"<pubDate>{fecha}</pubDate>")
        partes.append("</item>")
    partes.append("</channel></rss>")
    return "".join(partes).encode("utf-8")
