"""Indicadores de Mi Café: dólares, riesgo país, acciones, reservas y tasas.

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
    BCRA_IDS, TIMEOUT_INDICADORES, URL_BCRA_VARIABLE, URL_DOLARAPI, URL_INFLACION,
    URL_INFLACION_INTERANUAL, URL_RIESGO_PAIS, URL_UVA, ZONA,
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
# Otras casas de la misma respuesta de DolarApi (spec 46): van en su propio grupo de preferencias.
COTIZACIONES_OTROS = [
    ("mayorista", "Dólar mayorista"),
    ("tarjeta", "Dólar tarjeta"),
    ("cripto", "Dólar cripto"),
]
# Tasas del BCRA (clave de config.BCRA_IDS -> nombre para mostrar), grupo "tasas" (spec 47).
TASAS = [
    ("badlar", "BADLAR (bancos privados)"),
    ("tamar", "TAMAR (bancos privados)"),
    ("plazo_fijo_30", "Plazo fijo a 30 días"),
]
# Inflación y UVA de ArgentinaDatos (spec 48): (clave y de la copia local, url, nombre, formato).
CLAVES_MENSUALES = ("inflacion", "inflacion_interanual")  # su fecha es un mes, no un día
# Brechas: cada cotización contra el oficial (calculadas acá, no por el modelo).
BRECHAS = [
    ("blue", "Brecha blue vs. oficial"),
    ("bolsa", "Brecha MEP vs. oficial"),
    ("contadoconliqui", "Brecha CCL vs. oficial"),
]


def obtener(ruta_copia: str, elegidos: list[str], ahora: datetime | None = None) -> ResultadoIndicadores:
    """Devuelve {"indicadores": [...], "generado_en": "...", "avisos": [...]}.

    `elegidos` son las preferencias de indicadores ("dolar", "riesgo_pais",
    "reservas", "tasas", "dolar_otros", "inflacion", "acciones"); solo se consulta lo elegido.
    `avisos` son frases en español para la página: una
    por cada fuente que falló y una por cada dato con fecha vieja.
    """
    ahora = ahora or datetime.now(ZONA)
    hoy = ahora.date()
    copia = utilidades.leer_copia(ruta_copia)
    avisos = []

    indicadores = []
    if "dolar" in elegidos or "dolar_otros" in elegidos:
        indicadores += _dolares(copia, ahora, hoy, avisos, "dolar" in elegidos, "dolar_otros" in elegidos)
    if "riesgo_pais" in elegidos:
        indicadores.append(_riesgo_pais(copia, ahora, hoy, avisos))
    avisos_bcra: list[str] = []
    if "reservas" in elegidos:
        indicadores.append(_serie_bcra(copia, ahora, hoy, avisos_bcra, "reservas", "reservas",
                                       "Reservas internacionales (cifra provisoria)", _texto_reservas))
    if "tasas" in elegidos:
        for clave, nombre in TASAS:
            indicadores.append(_serie_bcra(copia, ahora, hoy, avisos_bcra, clave, "tasas", nombre, _texto_tasa))
    if "dolar_otros" in elegidos:
        indicadores.append(_serie_bcra(copia, ahora, hoy, avisos_bcra, "a3500", "dolar_otros",
                                       "Dólar A3500 (referencia BCRA)", utilidades.monto, "dolar_a3500"))
    if avisos_bcra:
        avisos.append(avisos_bcra[0])  # un solo aviso por fuente, aunque fallen varias series
    if "inflacion" in elegidos:
        avisos_inflacion: list[str] = []
        indicadores += _inflacion_y_uva(copia, ahora, hoy, avisos_inflacion)
        if avisos_inflacion:
            avisos.append(avisos_inflacion[0])  # un solo aviso de ArgentinaDatos para las tres series

    for indicador in indicadores:
        if indicador["desactualizado"]:
            articulo = "de" if indicador["clave"] in CLAVES_MENSUALES else "del"  # "de octubre 2026" / "del 17/11/2026"
            avisos.append(
                f"{indicador['nombre']}: el dato es {articulo} {indicador['fecha']} y está desactualizado."
            )

    utilidades.guardar_copia(ruta_copia, copia)
    return {
        "indicadores": indicadores,
        "generado_en": ahora.strftime("%d/%m/%Y %H:%M"),
        "avisos": avisos,
    }


# --- Indicadores -----------------------------------------------------------

def _dolares(copia, ahora, hoy, avisos, con_dolar=True, con_otros=False):
    respuesta = _respuesta(copia, "dolares", URL_DOLARAPI, ahora, False, "DolarApi", avisos)
    cotis = _cotizaciones(respuesta)
    items = []

    grupos = ([("dolar", COTIZACIONES)] if con_dolar else []) + ([("dolar_otros", COTIZACIONES_OTROS)] if con_otros else [])
    for grupo, casas in grupos:
        for casa, nombre in casas:
            cot = cotis.get(casa)
            if cot is None:
                items.append(_indicador(f"dolar_{casa}", grupo, nombre, FUENTE_DOLARAPI, None, None, hoy))
                continue
            texto = (f"venta {utilidades.monto(cot['venta'])} (compra {utilidades.monto(cot['compra'])})")
            items.append(_indicador(f"dolar_{casa}", grupo, nombre, FUENTE_DOLARAPI,
                                    texto, cot["momento"], hoy))
        if grupo == "dolar":
            items += _brechas(cotis, hoy)
    return items


def _brechas(cotis, hoy):
    items = []
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


def _texto_reservas(valor):
    return f"US$ {utilidades.formatear_numero(valor, 2)} millones"


def _texto_tasa(valor):
    return f"{utilidades.formatear_numero(valor, 2)} % TNA"


def _texto_inflacion_mensual(valor):
    return f"{utilidades.formatear_numero(valor, 2)} % mensual"


def _texto_inflacion_interanual(valor):
    return f"{utilidades.formatear_numero(valor, 2)} % interanual"


def _inflacion_y_uva(copia, ahora, hoy, avisos_ad):
    """Inflación mensual, interanual y UVA (ArgentinaDatos, una copia local por serie, una consulta cada 3 horas)."""
    series = [
        ("inflacion", URL_INFLACION, "Inflación mensual", _texto_inflacion_mensual),
        ("inflacion_interanual", URL_INFLACION_INTERANUAL, "Inflación interanual", _texto_inflacion_interanual),
        ("uva", URL_UVA, "UVA", utilidades.monto),
    ]
    items = []
    for clave, url, nombre, formatear in series:
        respuesta = _respuesta(copia, clave, url, ahora, True, "ArgentinaDatos", avisos_ad)
        valor, fecha = _ultima_de_lista(respuesta, hoy)
        texto = formatear(valor) if valor is not None else None
        items.append(_indicador(clave, "inflacion", nombre, FUENTE_ARGENTINADATOS, texto, fecha, hoy,
                                mensual=clave in CLAVES_MENSUALES))
    return items


def _serie_bcra(copia, ahora, hoy, avisos_bcra, serie, grupo, nombre, formatear, clave=None):
    """Consulta una serie del BCRA (por su id de config.BCRA_IDS) y arma el indicador."""
    url = URL_BCRA_VARIABLE.format(id=BCRA_IDS[serie])
    respuesta = _respuesta(copia, f"bcra_{serie}", url, ahora, False, "BCRA", avisos_bcra)
    valor, fecha = _ultimo_de_serie(respuesta, hoy)
    texto = formatear(valor) if valor is not None else None
    return _indicador(clave or serie, grupo, nombre, FUENTE_BCRA, texto, fecha, hoy)


def _indicador(clave, grupo, nombre, fuente, texto, momento, hoy, mensual=False):
    """Arma un indicador. Sin texto o sin fecha, es "sin dato".

    Un indicador `mensual` muestra su fecha como mes ("octubre 2026") y está desactualizado
    si su mes quedó 2 meses o más atrás del de hoy (spec 48).
    """
    if texto is None or momento is None:
        return {
            "clave": clave, "grupo": grupo, "nombre": nombre,
            "valor": None, "fecha": None, "fuente": fuente, "desactualizado": False,
        }
    if mensual:
        return {
            "clave": clave, "grupo": grupo, "nombre": nombre,
            "valor": texto,
            "fecha": utilidades.mostrar_mes(momento),
            "fuente": fuente,
            "desactualizado": utilidades.meses_entre(utilidades.dia_de(momento), hoy) >= 2,
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


def _ultima_de_lista(respuesta, hoy):
    """Devuelve (valor, fecha) de la fila con la fecha más reciente de una serie de ArgentinaDatos.

    La respuesta es una lista de filas `fecha` y `valor`. No se confía en el orden: se ignoran las
    filas con fecha o valor inválido y las de fecha futura (la UVA, por ejemplo, trae días por adelantado).
    """
    if not isinstance(respuesta, list):
        return None, None
    filas = []
    for fila in respuesta:
        if not isinstance(fila, dict):
            continue
        fecha = utilidades.dia(fila.get("fecha"))
        valor = utilidades.numero(fila.get("valor"))
        if fecha is not None and valor is not None and fecha <= hoy:
            filas.append((fecha, valor))
    if not filas:
        return None, None
    fecha, valor = max(filas)
    return valor, fecha


def _ultimo_de_serie(respuesta, hoy):
    """Devuelve (valor, fecha) de la fila con la fecha más reciente de una serie del BCRA v4.0.

    La respuesta trae `results[0].detalle` con filas `fecha` y `valor`. No se confía en el orden:
    se ignoran las filas con fecha o valor inválido y las de fecha futura (respecto de `hoy`).
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
        if fecha is not None and valor is not None and fecha <= hoy:
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


