"""Indicadores de Mi Café: dólares, riesgo país y reservas.

Los números salen de las APIs; el modelo nunca los escribe (regla de CLAUDE.md:
"ningún número sin fuente y fecha"; si no hay dato confiable, "sin dato"). Cada valor lleva
fecha y fuente. Si una fuente falla o no trae un dato válido, ese indicador
queda en "sin dato" (valor None) y los demás se muestran igual. Cada falla de
una fuente, y cada dato con fecha vieja, deja un aviso en español en "avisos"
para que la página lo muestre de forma visible (spec 12).

Copia local: datos/indicadores.json guarda la última respuesta de cada fuente
con la hora de la consulta. ArgentinaDatos admite una consulta cada 3 horas por
serie, así que mientras no pasen 3 horas se usa la copia en lugar de consultar.

Solo usa la librería estándar de Python (sin pip install).
"""

from __future__ import annotations

import logging
import http.client
import json
import urllib.request
from datetime import datetime, timedelta

from micafe.config import (
    AGENTE, FUENTE_ARGENTINADATOS, FUENTE_BCRA, FUENTE_DOLARAPI, HORAS_ENTRE_CONSULTAS,
    TIMEOUT_INDICADORES, URL_DOLARAPI, URL_RESERVAS, URL_RIESGO_PAIS, ZONA,
)
from micafe.fuentes import utilidades
from micafe.modelos import ResultadoIndicadores

logger = logging.getLogger(__name__)

# Cotizaciones de DolarApi: clave de la casa -> nombre para mostrar.
COTIZACIONES = [
    ("oficial", "Dólar oficial"),
    ("blue", "Dólar blue"),
    ("bolsa", "Dólar MEP"),
    ("contadoconliqui", "Dólar CCL"),
]
# Brechas: cada cotización contra el oficial (calculadas acá, no por el modelo).
BRECHAS = [
    ("blue", "Brecha blue vs. oficial"),
    ("bolsa", "Brecha MEP vs. oficial"),
    ("contadoconliqui", "Brecha CCL vs. oficial"),
]


def obtener(ruta_copia: str, elegidos: list[str], ahora: datetime | None = None) -> ResultadoIndicadores:
    """Devuelve {"indicadores": [...], "generado_en": "...", "avisos": [...]}.

    `elegidos` son las preferencias de indicadores ("dolar", "riesgo_pais",
    "acciones"). Reservas no tiene preferencia propia en la lista de la spec 02,
    así que se trae siempre. `avisos` son frases en español para la página: una
    por cada fuente que falló y una por cada dato con fecha vieja.
    """
    ahora = ahora or datetime.now(ZONA)
    hoy = ahora.date()
    copia = utilidades.leer_copia(ruta_copia)
    avisos = []

    indicadores = []
    if "dolar" in elegidos:
        indicadores += _dolares(copia, ahora, hoy, avisos)
    if "riesgo_pais" in elegidos:
        indicadores.append(_riesgo_pais(copia, ahora, hoy, avisos))
    indicadores.append(_reservas(copia, ahora, hoy, avisos))

    for indicador in indicadores:
        if indicador["desactualizado"]:
            avisos.append(
                f"{indicador['nombre']}: el dato es del {indicador['fecha']} y está desactualizado."
            )

    utilidades.guardar_copia(ruta_copia, copia)
    return {
        "indicadores": indicadores,
        "generado_en": ahora.strftime("%d/%m/%Y %H:%M"),
        "avisos": avisos,
    }


# --- Indicadores -----------------------------------------------------------

def _dolares(copia, ahora, hoy, avisos):
    respuesta = _respuesta(copia, "dolares", URL_DOLARAPI, ahora, False, "DolarApi", avisos)
    cotis = _cotizaciones(respuesta)
    items = []

    for casa, nombre in COTIZACIONES:
        cot = cotis.get(casa)
        if cot is None:
            items.append(_indicador(f"dolar_{casa}", "dolar", nombre, FUENTE_DOLARAPI, None, None, hoy))
            continue
        texto = (f"venta {utilidades.monto(cot['venta'])} (compra {utilidades.monto(cot['compra'])})")
        items.append(_indicador(f"dolar_{casa}", "dolar", nombre, FUENTE_DOLARAPI,
                                texto, cot["momento"], hoy))

    oficial = cotis.get("oficial")
    for casa, nombre in BRECHAS:
        cot = cotis.get(casa)
        if cot is None or oficial is None or oficial["venta"] <= 0:
            items.append(_indicador(f"brecha_{casa}", "dolar", nombre, FUENTE_DOLARAPI, None, None, hoy))
            continue
        brecha = (cot["venta"] / oficial["venta"] - 1) * 100
        # La fecha de una brecha es la más vieja de las dos cotizaciones usadas.
        momento = min(cot["momento"], oficial["momento"])
        items.append(_indicador(f"brecha_{casa}", "dolar", nombre, FUENTE_DOLARAPI,
                                f"{utilidades.formatear_numero(brecha, 2)} %", momento, hoy))
    return items


def _riesgo_pais(copia, ahora, hoy, avisos):
    respuesta = _respuesta(copia, "riesgo_pais", URL_RIESGO_PAIS, ahora, True, "ArgentinaDatos", avisos)
    valor = fecha = None
    if isinstance(respuesta, dict):
        valor = utilidades.numero(respuesta.get("valor"))
        fecha = utilidades.dia(respuesta.get("fecha"))
    texto = f"{utilidades.formatear_numero(valor, 0)} puntos básicos" if valor is not None else None
    return _indicador("riesgo_pais", "riesgo_pais", "Riesgo país", FUENTE_ARGENTINADATOS,
                      texto, fecha, hoy)


def _reservas(copia, ahora, hoy, avisos):
    respuesta = _respuesta(copia, "reservas", URL_RESERVAS, ahora, False, "BCRA", avisos)
    valor, fecha = _reservas_ultimo(respuesta)
    texto = f"US$ {utilidades.formatear_numero(valor, 2)} millones" if valor is not None else None
    return _indicador("reservas", "reservas", "Reservas internacionales (cifra provisoria)",
                      FUENTE_BCRA, texto, fecha, hoy)


def _indicador(clave, grupo, nombre, fuente, texto, momento, hoy):
    """Arma un indicador. Sin texto o sin fecha, es "sin dato"."""
    if texto is None or momento is None:
        return {
            "clave": clave, "grupo": grupo, "nombre": nombre,
            "valor": None, "fecha": None, "fuente": fuente, "desactualizado": False,
        }
    return {
        "clave": clave, "grupo": grupo, "nombre": nombre,
        "valor": texto,
        "fecha": utilidades.mostrar_fecha(momento),
        "fuente": fuente,
        # Indicadores diarios: más de 1 día hábil de antigüedad se marca.
        "desactualizado": utilidades.dias_habiles_entre(utilidades.dia_de(momento), hoy) > 1,
    }


# --- Lectura de respuestas -------------------------------------------------

def _cotizaciones(respuesta):
    """Devuelve {casa: {compra, venta, momento}} de la respuesta de DolarApi."""
    salida = {}
    if not isinstance(respuesta, list):
        return salida
    for fila in respuesta:
        if not isinstance(fila, dict):
            continue
        casa = fila.get("casa")
        compra = utilidades.numero(fila.get("compra"))
        venta = utilidades.numero(fila.get("venta"))
        momento = utilidades.momento(fila.get("fechaActualizacion"))
        if isinstance(casa, str) and None not in (compra, venta) and momento is not None:
            salida[casa] = {"compra": compra, "venta": venta, "momento": momento}
    return salida


def _reservas_ultimo(respuesta):
    """Devuelve (valor, fecha) del dato más reciente de la serie del BCRA.

    El endpoint /monetarias/1 trae `results[0].detalle` con las filas más
    recientes primero. La fecha y el valor de esa fila coinciden con
    `ultFechaInformada` y `ultValorInformado` del catálogo del BCRA.
    """
    try:
        detalle = respuesta["results"][0]["detalle"]
    except (TypeError, KeyError, IndexError):
        return None, None
    if not isinstance(detalle, list):
        return None, None

    filas = []
    for fila in detalle:
        if not isinstance(fila, dict):
            continue
        fecha = utilidades.dia(fila.get("fecha"))
        valor = utilidades.numero(fila.get("valor"))
        if fecha is not None and valor is not None:
            filas.append((fecha, valor))
    if not filas:
        return None, None
    fecha, valor = max(filas)
    return valor, fecha


# --- Consultas y copia local -----------------------------------------------

def _respuesta(copia, clave, url, ahora, reutilizar, nombre, avisos):
    """Devuelve la respuesta de la fuente, o None si falla (sin dato).

    Con `reutilizar` (ArgentinaDatos), si la última consulta fue hace menos de
    3 horas se usa la copia y no se vuelve a consultar. Toda consulta, aunque
    falle, queda registrada con su hora y su motivo. Si la fuente no dio datos
    (ahora o en la copia), agrega un aviso a `avisos` con el nombre de la fuente.
    """
    entrada = copia.get(clave)
    if reutilizar and isinstance(entrada, dict) and entrada.get("url") == url:
        consultado = utilidades.momento(entrada.get("consultado_en"))
        if consultado is not None:
            transcurrido = ahora - consultado
            if timedelta(0) <= transcurrido < timedelta(hours=HORAS_ENTRE_CONSULTAS):
                logger.warning(f"Aviso: {clave} sale de la copia local consultada el "
                      f"{utilidades.mostrar_fecha(consultado)} (ArgentinaDatos pide una consulta cada 3 horas).")
                if entrada.get("respuesta") is None:
                    avisos.append(_aviso_de_falla(nombre, entrada.get("motivo")))
                return entrada.get("respuesta")

    respuesta, motivo = _pedir_json(url)
    copia[clave] = {
        "url": url,
        "consultado_en": ahora.isoformat(timespec="seconds"),
        "respuesta": respuesta,
        "motivo": motivo,
    }
    if motivo is not None:
        avisos.append(_aviso_de_falla(nombre, motivo))
    return respuesta


def _aviso_de_falla(nombre, motivo):
    return f"No se pudo consultar {nombre}: {motivo or 'no respondió'}. Se muestra sin dato."


def _pedir_json(url):
    """Pide una URL. Devuelve (JSON, None) si anda, o (None, motivo) si falla.

    El motivo va en español para la página; el detalle técnico queda en la consola.
    """
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_INDICADORES) as respuesta:
            return json.loads(respuesta.read().decode("utf-8")), None
    except (OSError, ValueError, http.client.HTTPException) as error:
        motivo = utilidades.motivo(error)
        logger.warning(f"Aviso: no se pudo consultar {url} ({motivo}). Se muestra sin dato. Detalle: {error}")
        return None, motivo


