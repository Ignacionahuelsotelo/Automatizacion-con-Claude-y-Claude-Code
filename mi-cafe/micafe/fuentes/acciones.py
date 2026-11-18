"""Acciones GGAL, YPFD y PAMP desde data912 (spec 13) y MSCI Merval desde Rava (spec 14).

Solo librería estándar. Para cada ticker se pide
https://data912.com/historical/stocks/{TICKER} y se toma el último cierre con
fecha menor o igual a ayer (America/Argentina/Buenos_Aires). El valor se formatea
acá: el modelo nunca ve ni escribe estos números.
"""

from __future__ import annotations

import logging
import http.client
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta

from micafe.config import (
    AGENTE, AGENTE_RAVA, FUENTE_DATA912 as FUENTE, FUENTE_RAVA, FUENTE_RESPALDO_DATA912 as FUENTE_RESPALDO,
    HORAS_ENTRE_CONSULTAS, MAX_CONSULTAS_RAVA, NOMBRE_MERVAL, TIMEOUT_ACCIONES, URL_DATA912 as URL_BASE,
    URL_RAVA, URL_RAVA_ROBOTS as URL_ROBOTS, ZONA,
)
from micafe.fuentes import utilidades  # helpers de fechas, formato y copia local
from micafe.modelos import ResultadoAcciones, ResultadoMerval

logger = logging.getLogger(__name__)

TICKERS = [
    ("GGAL", "Grupo Galicia (GGAL)"),
    ("YPFD", "YPF (YPFD)"),
    ("PAMP", "Pampa Energía (PAMP)"),
]


# --- MSCI Merval (spec 14) ---------------------------------------------------
# Respaldo en data912: el 18/11/2026 se probaron /historical/stocks/MERV, /MMSCI y
# /live/arg_stocks y ninguno trae el índice. Queda desactivado (spec 14, punto 8).
TICKER_RESPALDO = None
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11,
         "diciembre": 12}


def obtener_merval(ruta_copia: str, ahora: datetime | None = None) -> ResultadoMerval:
    """Devuelve {"indicador": {...}, "avisos": [...]} con el cierre del MSCI Merval.

    Los avisos incluyen el de dato desactualizado (spec 15).
    """
    ahora = ahora or datetime.now(ZONA)
    resultado = _obtener_merval(ruta_copia, ahora)
    _avisar_desactualizado(resultado["indicador"], resultado["avisos"])
    return resultado


def obtener_todo(ruta_copia: str, ahora: datetime | None = None) -> ResultadoAcciones:
    """Devuelve {"indicadores": [MSCI Merval, GGAL, YPFD, PAMP], "avisos": [...]} (spec 15)."""
    ahora = ahora or datetime.now(ZONA)
    merval = obtener_merval(ruta_copia, ahora)
    resto = obtener(ruta_copia, ahora)
    return {"indicadores": [merval["indicador"]] + resto["indicadores"],
            "avisos": merval["avisos"] + resto["avisos"]}


def _avisar_desactualizado(indicador, avisos):
    if indicador.get("desactualizado"):
        avisos.append(f"{indicador['nombre']}: el dato es del {indicador['fecha']} y está desactualizado.")


def _obtener_merval(ruta_copia, ahora):
    """Cuerpo de obtener_merval, sin el aviso de desactualizado.

    Rava primero; si falla, respaldo en data912 (hoy desactivado); si no, sin dato.
    Copia local en la clave "merval" de ruta_copia (vigente 3 horas).
    """
    ayer = ahora.date() - timedelta(days=1)
    copia = utilidades.leer_copia(ruta_copia)
    avisos = []

    entrada = copia.get("merval")
    if isinstance(entrada, dict):
        consultado = utilidades.momento(entrada.get("consultado_en"))
        dato = entrada.get("dato")
        if (consultado is not None and timedelta(0) <= ahora - consultado
                < timedelta(hours=HORAS_ENTRE_CONSULTAS) and isinstance(dato, dict)):
            dia = utilidades.dia(dato.get("fecha"))
            cierre = utilidades.numero(dato.get("cierre"))
            if dia is not None and dia <= ayer and cierre is not None and cierre > 0:
                return {"indicador": _indicador_merval(cierre, dia, entrada.get("fuente"), ahora),
                        "avisos": avisos}

    resultado, url = _merval_de_rava(ayer, avisos)
    fuente = FUENTE_RAVA
    if resultado is None:
        resultado, url = _merval_de_respaldo(ayer, avisos)
        fuente = FUENTE_RESPALDO
        if resultado is not None:
            avisos.append("Se usó data912 para el MSCI Merval.")
    if resultado is None:
        avisos.append("El MSCI Merval se muestra sin dato.")
        copia.pop("merval", None)  # una consulta fallida no queda como vigente
        utilidades.guardar_copia(ruta_copia, copia)
        return {"indicador": _indicador_merval(None, None, None, ahora), "avisos": avisos}

    cierre, dia = resultado
    copia["merval"] = {"fuente": fuente, "url": url, "consultado_en": ahora.isoformat(timespec="seconds"),
                       "dato": {"cierre": cierre, "fecha": dia.isoformat()}}
    utilidades.guardar_copia(ruta_copia, copia)
    return {"indicador": _indicador_merval(cierre, dia, fuente, ahora), "avisos": avisos}


def _indicador_merval(cierre, dia, fuente, ahora):
    base = {"clave": "accion_mmsci", "grupo": "acciones", "nombre": NOMBRE_MERVAL}
    if cierre is None:
        return {**base, "valor": None, "fecha": None, "fuente": FUENTE_RAVA, "desactualizado": False}
    return {**base, "valor": f"{_formatear_puntos(cierre)} puntos",
            "fecha": utilidades.mostrar_fecha(dia), "fuente": fuente or FUENTE_RAVA,
            "desactualizado": utilidades.dias_habiles_entre(dia, ahora.date()) > 1}


def _formatear_puntos(numero):
    """81794 -> '81.794'; 81794.5 -> '81.794,50' (sin símbolo $, es un índice)."""
    decimales = 0 if float(numero).is_integer() else 2
    return utilidades.formatear_numero(numero, decimales)


def _merval_de_rava(ayer, avisos):
    """Devuelve ((cierre, fecha), url) o (None, None). Máximo 8 consultas a Rava."""
    if not _robots_permite():
        logger.warning("Aviso: robots.txt de Rava bloquea la ruta histórica. No se consulta.")
        avisos.append("Rava no permite consultar el MSCI Merval (robots.txt).")
        return None, None
    dia = ayer
    for _ in range(MAX_CONSULTAS_RAVA):
        url = f"{URL_RAVA}{dia.year}/{dia.month:02d}/{dia.day:02d}/"
        html, motivo = _pedir_html(url)
        if motivo == "404":
            dia -= timedelta(days=1)  # sin rueda: probar el día anterior
            continue
        if html is None:
            avisos.append(f"No se pudo consultar Rava para el MSCI Merval: {motivo}.")
            return None, None
        leido = _leer_json_ld(html)
        if leido is None or leido[1] != dia:
            logger.warning(f"Aviso: la página de Rava {url} no trajo un cierre válido para ese día.")
            avisos.append("Rava respondió algo que no se pudo validar para el MSCI Merval.")
            return None, None
        return leido, url
    avisos.append("Rava no tuvo página del MSCI Merval en los últimos días consultados.")
    return None, None


def _merval_de_respaldo(ayer, avisos):
    """Respaldo en data912. Desactivado mientras TICKER_RESPALDO sea None."""
    if TICKER_RESPALDO is None:
        return None, None
    url = URL_BASE + TICKER_RESPALDO
    respuesta, motivo = _pedir_json(url)
    cierre, dia = _ultimo_cierre(respuesta, ayer)
    if cierre is None:
        avisos.append(f"No se pudo consultar data912 para el MSCI Merval: "
                      f"{motivo or 'no trajo un cierre válido'}.")
        return None, None
    return (cierre, dia), url


def _robots_permite():
    """False solo si robots.txt (grupo *) bloquea la ruta; si no se puede leer, se sigue."""
    texto, _ = _pedir_html(URL_ROBOTS)
    if texto is None:
        return True
    aplica = False
    for linea in texto.splitlines():
        linea = linea.split("#")[0].strip()
        clave, _, valor = linea.partition(":")
        clave, valor = clave.strip().lower(), valor.strip()
        if clave == "user-agent":
            aplica = valor == "*"
        elif aplica and clave == "disallow" and valor and "/cotizaciones/historico/merval/".startswith(valor):
            return False
    return True


def _pedir_html(url):
    """Devuelve (texto, None) o (None, motivo). El motivo "404" marca un día sin página."""
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE_RAVA})
    try:
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_ACCIONES) as r:
            return r.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None, "404"
        motivo = utilidades.motivo(error)  # el 410 se explica como dirección dada de baja
        logger.warning(f"Aviso: no se pudo consultar {url} (HTTP {error.code}).")
        return None, motivo
    except (OSError, http.client.HTTPException) as error:
        motivo = utilidades.motivo(error)
        logger.warning(f"Aviso: no se pudo consultar {url} ({motivo}). Detalle: {error}")
        return None, motivo


def _leer_json_ld(html):
    """Devuelve (cierre, fecha) del FAQPage de Rava, o None si no se puede leer."""
    bloques = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I)
    for bloque in bloques:
        try:
            datos = json.loads(bloque)
        except ValueError:
            continue
        if not isinstance(datos, dict) or datos.get("@type") != "FAQPage":
            continue
        for pregunta in datos.get("mainEntity") or []:
            try:
                texto = pregunta["acceptedAnswer"]["text"]
            except (KeyError, TypeError):
                continue
            m = re.search(r"cerr[oó] a ([\d.,]+) el (\d{1,2}) de (\w+) de (\d{4})", texto, re.I)
            if not m:
                continue
            numero = m.group(1).replace(".", "").replace(",", ".")
            mes = MESES.get(m.group(3).lower())
            try:
                cierre = float(numero)
                dia = datetime(int(m.group(4)), mes, int(m.group(2))).date() if mes else None
            except ValueError:
                continue
            if dia is not None and cierre > 0:
                return cierre, dia
    return None


def obtener(ruta_copia: str, ahora: datetime | None = None) -> ResultadoAcciones:
    """Devuelve {"indicadores": [...], "avisos": [...]} con un indicador por ticker.

    La copia local guarda, por ticker, la URL, la hora de la consulta y la
    respuesta. Una consulta fallida no se guarda como vigente.
    """
    ahora = ahora or datetime.now(ZONA)
    ayer = ahora.date() - timedelta(days=1)
    copia = utilidades.leer_copia(ruta_copia)
    salida, avisos = [], []

    for ticker, nombre in TICKERS:
        url = URL_BASE + ticker
        respuesta = _respuesta(copia, ticker, url, ahora, avisos, nombre)
        cierre, dia = _ultimo_cierre(respuesta, ayer)
        if cierre is None:
            if respuesta is not None:
                logger.warning(f"Aviso: data912 no trajo ninguna fila válida para {ticker}.")
                avisos.append(f"{nombre}: data912 no trajo un cierre válido. Se muestra sin dato.")
                copia.pop(ticker, None)
            salida.append(_indicador(ticker, nombre, None, None, ahora))
        else:
            salida.append(_indicador(ticker, nombre, cierre, dia, ahora))

    utilidades.guardar_copia(ruta_copia, copia)
    for indicador in salida:
        _avisar_desactualizado(indicador, avisos)
    return {"indicadores": salida, "avisos": avisos}


def _indicador(ticker, nombre, cierre, dia, ahora):
    base = {"clave": f"accion_{ticker.lower()}", "grupo": "acciones", "nombre": nombre,
            "fuente": FUENTE}
    if cierre is None:
        return {**base, "valor": None, "fecha": None, "desactualizado": False}
    return {
        **base,
        "valor": utilidades.monto(cierre),
        "fecha": utilidades.mostrar_fecha(dia),  # la de la fila, no la de la consulta
        "desactualizado": utilidades.dias_habiles_entre(dia, ahora.date()) > 1,
    }


def _ultimo_cierre(respuesta, ayer):
    """Devuelve (cierre, fecha) de la fila válida más reciente con fecha <= ayer."""
    if not isinstance(respuesta, list):
        return None, None
    mejor = None
    for fila in respuesta:
        if not isinstance(fila, dict):
            continue
        dia = utilidades.dia(fila.get("date"))
        cierre = utilidades.numero(fila.get("c"))
        if dia is None or dia > ayer or cierre is None or cierre <= 0:
            continue
        if mejor is None or dia > mejor[1]:
            mejor = (cierre, dia)
    return mejor if mejor else (None, None)


def _respuesta(copia, ticker, url, ahora, avisos, nombre):
    """Respuesta de data912 (de la copia si tiene menos de 3 horas), o None si falla."""
    entrada = copia.get(ticker)
    if isinstance(entrada, dict) and entrada.get("url") == url and entrada.get("respuesta") is not None:
        consultado = utilidades.momento(entrada.get("consultado_en"))
        if consultado is not None and timedelta(0) <= ahora - consultado < timedelta(hours=HORAS_ENTRE_CONSULTAS):
            return entrada["respuesta"]

    respuesta, motivo = _pedir_json(url)
    if not isinstance(respuesta, list) or not respuesta:
        # No se guarda como vigente: se reintenta en el pedido siguiente.
        copia.pop(ticker, None)
        avisos.append(f"No se pudo consultar data912 para {nombre}: "
                      f"{motivo or 'respondió algo que no es una lista de cotizaciones'}. Se muestra sin dato.")
        return None
    copia[ticker] = {"url": url, "consultado_en": ahora.isoformat(timespec="seconds"),
                     "respuesta": respuesta}
    return respuesta


def _pedir_json(url):
    pedido = urllib.request.Request(
        url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_ACCIONES) as r:
            return json.loads(r.read().decode("utf-8")), None
    except (OSError, ValueError, http.client.HTTPException) as error:
        motivo = utilidades.motivo(error)
        logger.warning(f"Aviso: no se pudo consultar {url} ({motivo}). Se muestra sin dato. Detalle: {error}")
        return None, motivo
