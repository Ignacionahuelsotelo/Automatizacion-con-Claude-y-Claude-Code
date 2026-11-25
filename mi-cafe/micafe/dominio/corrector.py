"""Corrector de Mi Café: revisa el resumen antes de mostrarlo (spec 07).

Los chequeos con código (largo del texto, enlaces, tope por medio,
repetidas dentro del resumen y contra los últimos 3 resúmenes guardados,
"S&P Merval" y Télam) los hace este módulo. Después, si pasaron, se hace el
chequeo con modelo: `claude -p` con la skill .claude/skills/corrector/SKILL.md.

El corrector NO reescribe el resumen. Si algo no cumple, le pide a la redacción
que lo rehaga diciendo qué falló, como mucho 2 reintentos (decisión 8). Si
después de eso sigue sin pasar, devuelve el último texto junto con la lista de
lo que no cumple, para que la página lo muestre con aviso.

Solo usa la librería estándar de Python (sin pip install).
"""

from __future__ import annotations

import difflib
import os
import re
import unicodedata
from collections import Counter
from typing import Any, Callable

from micafe.config import (
    ARCHIVO_SKILL_CORRECTOR, CANTIDAD_PREVIOS, CARPETA_PROYECTO, MAXIMO_PALABRAS, MINIMO_PALABRAS,
    REINTENTOS_CORRECTOR, SECCIONES,
)
from micafe.dominio import resumen
from micafe.dominio.seleccion import orden_de_recorte
from micafe.modelos import CupoSeccion, Nota, Revision

ARCHIVO_SKILL = ARCHIVO_SKILL_CORRECTOR

REINTENTOS = REINTENTOS_CORRECTOR  # decisión 8 de specs/README.md (ver config.py)
SIMILITUD_TITULO = 0.85  # "título casi igual"

INICIO_APERTURA = "Lo más importante de hoy:"
INICIO_CIERRE = "Lo que viene hoy:"

RE_LINK = re.compile(r"https?://\S+")
# Regla de CLAUDE.md ("Nombres vigentes"): el índice es MSCI Merval, no "S&P Merval", y Télam ya no existe.
RE_SP_MERVAL = re.compile(r"S&P\s+Merval", re.IGNORECASE)
# Télam como agencia vigente; "ex Télam" está bien.
RE_TELAM = re.compile(r"(?<!ex )(?<!ex-)\bTélam\b", re.IGNORECASE)


# --- Lectura del texto -------------------------------------------------------

def _bloques(texto: str | None) -> list[str]:
    return [bloque.strip() for bloque in re.split(r"\n\s*\n", texto or "") if bloque.strip()]


def _lineas_utiles(bloque: str) -> list[str]:
    """Las líneas del bloque sin los encabezados de sección."""
    return [linea.strip() for linea in bloque.splitlines() if linea.strip() and linea.strip() not in SECCIONES]


def _links(texto: str | None) -> list[str]:
    return [url.rstrip(".,;:)]»\"'") for url in RE_LINK.findall(texto or "")]


def notas_del_texto(texto: str | None) -> list[list[str]]:
    """Devuelve los bloques que son notas: sin encabezados de sección, apertura ni cierre.

    Cada bloque es una lista de líneas: título primero, link al final.
    """
    notas = []
    for bloque in _bloques(texto):
        lineas = _lineas_utiles(bloque)
        if not lineas:
            continue
        primera = lineas[0]
        if primera.startswith(INICIO_APERTURA) or primera.startswith(INICIO_CIERRE):
            continue
        notas.append(lineas)
    return notas


def _es_solo_link(linea: str) -> bool:
    return re.fullmatch(r"https?://\S+", linea) is not None


def notas_votables(texto: str | None) -> list[dict[str, str]]:
    """Las notas del resumen como `{titulo, medio, seccion, link}`, para poder votarlas (spec 31).

    El título es la primera línea del bloque, el link la primera línea que es solo un link
    (si hay dos fuentes, se toma la primera) y el medio sale de la línea anterior al link
    ("Medio, fecha"), cortando en la última coma. Si no se puede leer, el medio queda en ""
    y, sin título o sin link, la nota no se incluye. No inventa nada.
    """
    notas: list[dict[str, str]] = []
    seccion = ""
    for bloque in _bloques(texto):
        lineas: list[str] = []
        for linea in (l.strip() for l in bloque.splitlines()):
            if linea in SECCIONES:
                seccion = linea
            elif linea:
                lineas.append(linea)
        if not lineas or lineas[0].startswith((INICIO_APERTURA, INICIO_CIERRE)):
            continue
        indice = next((i for i, linea in enumerate(lineas) if _es_solo_link(linea)), None)
        if indice is None or indice == 0 or not seccion:
            continue
        medio = ""
        if indice >= 2 and not lineas[indice - 1].startswith("Por qué importa:"):
            medio = lineas[indice - 1].rsplit(",", 1)[0].strip() if "," in lineas[indice - 1] else lineas[indice - 1]
        notas.append({"titulo": lineas[0], "medio": medio, "seccion": seccion, "link": lineas[indice]})
    return notas


def _titulo(lineas: list[str]) -> str:
    return lineas[0]


def _texto_de(lineas: list[str]) -> str:
    return "\n".join(lineas)


def _medio_de(lineas: list[str], por_link: dict[str, Nota]) -> str | None:
    for url in _links(_texto_de(lineas)):
        if url in por_link:
            return por_link[url]["medio"]
    return None


# --- Comparaciones -----------------------------------------------------------

def _normalizar(texto: str | None) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = re.sub(r"[^\w\s]", " ", texto.lower())
    return " ".join(texto.split())


def titulos_parecidos(uno: str, otro: str) -> bool:
    """True si los títulos son casi iguales (ignora mayúsculas, tildes y puntuación)."""
    normal_uno, normal_otro = _normalizar(uno), _normalizar(otro)
    if not normal_uno or not normal_otro:
        return False
    return difflib.SequenceMatcher(None, normal_uno, normal_otro).ratio() >= SIMILITUD_TITULO


def _unicos(errores: list[str]) -> list[str]:
    vistos = []
    for error in errores:
        if error not in vistos:
            vistos.append(error)
    return vistos


def _chequeo(nombre: str, errores: list[str], detalle: str) -> dict[str, Any]:
    return {"nombre": nombre, "errores": _unicos(errores), "detalle": detalle}


# --- Chequeos con código -----------------------------------------------------

def _notas_por_seccion(texto: str | None) -> tuple[Counter, list[str]]:
    """Cuenta las notas de cada sección del texto y devuelve también los encabezados en orden."""
    cuenta: Counter = Counter()
    encabezados: list[str] = []
    seccion = ""
    for bloque in _bloques(texto):
        lineas = []
        for linea in (l.strip() for l in bloque.splitlines()):
            if linea in SECCIONES:
                seccion = linea
                encabezados.append(linea)
            elif linea:
                lineas.append(linea)
        if lineas and not lineas[0].startswith((INICIO_APERTURA, INICIO_CIERRE)):
            cuenta[seccion] += 1
    return cuenta, encabezados


def _texto_recorte(plan: list[CupoSeccion] | None) -> str:
    """Misma redacción que la skill resumen-diario y el prompt (spec 40)."""
    base = "Recortá desde las secciones de menor prioridad del plan (pedido, pesos y orden de los temas), nunca los indicadores."
    if plan:
        base += f" Orden para recortar: {', '.join(orden_de_recorte(plan))}."
    return base


def _chequear_codigo(texto: str, notas: list[Nota], tope: int,
                     previos: list[str] | None, minimo: int, maximo: int,
                     plan: list[CupoSeccion] | None = None, plan_completo: bool = True,
                     pedidas: list[str] | None = None) -> list[dict[str, Any]]:
    """Devuelve la lista de chequeos (cada uno con sus errores). No llama a ningún modelo."""
    por_link = {nota["link"]: nota for nota in notas}
    bloques = notas_del_texto(texto)
    chequeos = []

    # 1. Largo: solo el texto del resumen; los indicadores van aparte y no cuentan (spec 46).
    # Regla de CLAUDE.md: largo objetivo 550-650 palabras; si se pasa, se recorta desde las secciones de menor
    # prioridad del plan, nunca los indicadores. El mínimo solo se exige si el plan quedó completo (spec 40).
    palabras_texto = len((texto or "").split())
    total = palabras_texto
    errores = []
    if total < minimo and plan_completo:
        errores.append(
            f"Largo: el resumen tiene {palabras_texto} palabras y tiene que tener al menos {minimo} "
            f"(entre {minimo} y {maximo})."
        )
    elif total > maximo:
        errores.append(
            f"Largo: el resumen tiene {palabras_texto} palabras y tiene que tener como máximo {maximo} "
            f"(entre {minimo} y {maximo}). "
            + _texto_recorte(plan)
        )
    if plan_completo:
        chequeos.append(_chequeo("Largo", errores, f"{total} palabras (entre {minimo} y {maximo})."))
    elif errores:
        chequeos.append(_chequeo("Largo", errores, ""))
    else:
        chequeos.append({
            "nombre": "Largo", "errores": [], "omitido": True,
            "detalle": f"Largo mínimo no exigido: el plan quedó incompleto (hay pocas notas). "
                       f"El resumen tiene {total} palabras; el máximo es {maximo}.",
        })

    # 2. Enlaces (regla de CLAUDE.md: toda noticia va con link): cada nota con link, y todos los links tienen que ser de las notas de ayer.
    errores = []
    for lineas in bloques:
        if not _links(_texto_de(lineas)):
            errores.append(f"Falta el enlace en la nota «{_titulo(lineas)}».")
    for url in _links(texto):
        if url not in por_link:
            errores.append(f"El enlace no es de las notas de ayer: {url}")
    chequeos.append(_chequeo(
        "Enlaces de las notas de ayer", errores,
        f"{len(bloques)} notas con enlace de las notas de ayer.",
    ))

    # 3. Tope por medio (3, o 5 los lunes).
    conteo = Counter()
    for lineas in bloques:
        medio = _medio_de(lineas, por_link)
        if medio:
            conteo[medio] += 1
    errores = [
        f"Hay {cantidad} notas de {medio}; el máximo por medio para hoy es {tope}."
        for medio, cantidad in conteo.items() if cantidad > tope
    ]
    chequeos.append(_chequeo(
        "Tope por medio", errores,
        f"Máximo {tope} notas por medio.",
    ))

    # 4. Repetidas dentro del mismo resumen (mismo link o título casi igual, aunque sea en otra sección).
    errores = []
    vistos = {}
    for lineas in bloques:
        for url in set(_links(_texto_de(lineas))):
            if url in vistos:
                errores.append(f"La misma noticia aparece dos veces (mismo enlace): {url}")
            vistos[url] = lineas
    for i, uno in enumerate(bloques):
        for otro in bloques[i + 1:]:
            if set(_links(_texto_de(uno))) & set(_links(_texto_de(otro))):
                continue  # ya reportada por mismo enlace
            if titulos_parecidos(_titulo(uno), _titulo(otro)):
                errores.append(
                    f"La misma noticia aparece dos veces: «{_titulo(uno)}» y «{_titulo(otro)}»."
                )
    chequeos.append(_chequeo(
        "Sin repetidas en el resumen", errores,
        "Ninguna nota repetida dentro del resumen.",
    ))

    # 5. Repetidas contra los últimos 3 resúmenes guardados.
    if previos:
        errores = []
        notas_previas = []
        for texto_previo in previos:
            notas_previas.extend(notas_del_texto(texto_previo))
        for lineas in bloques:
            links_nota = set(_links(_texto_de(lineas)))
            for previa in notas_previas:
                if links_nota & set(_links(_texto_de(previa))):
                    errores.append(f"Nota repetida de un resumen anterior (mismo enlace): «{_titulo(lineas)}».")
                    break
                if titulos_parecidos(_titulo(lineas), _titulo(previa)):
                    errores.append(
                        f"Nota repetida de un resumen anterior (título casi igual): «{_titulo(lineas)}»."
                    )
                    break
        chequeos.append(_chequeo(
            "Sin repetidas de los últimos resúmenes", errores,
            f"Comparado con {len(previos)} resúmenes anteriores.",
        ))
    else:
        chequeos.append({
            "nombre": "Sin repetidas de los últimos resúmenes",
            "errores": [],
            "detalle": "No se chequea: todavía no hay resúmenes guardados.",
            "omitido": True,
        })

    # 6. Nombres vigentes.
    errores = []
    if RE_SP_MERVAL.search(texto or ""):
        errores.append("Dice «S&P Merval»: el índice se llama MSCI Merval desde el 19/10/2026.")
    if RE_TELAM.search(texto or ""):
        errores.append(
            "Menciona a Télam como agencia: ya no existe como agencia (pasó a APE S.A.U.). "
            "Si la nota depende solo de Télam, descartala."
        )
    chequeos.append(_chequeo(
        "Nombres vigentes", errores,
        "Sin «S&P Merval» ni Télam como agencia.",
    ))

    # 7. Secciones del plan (spec 40): ninguna sección fuera del plan ni con más notas que su cuota.
    if plan:
        cuotas = {c["seccion"]: c["cupo"] for c in plan}
        cuenta, encabezados = _notas_por_seccion(texto)
        errores = [f"La sección {s} no está en el plan de hoy: sacala." for s in dict.fromkeys(encabezados) if s not in cuotas]
        errores += [
            f"La sección {s} tiene {cuenta[s]} notas y su cuota de hoy es {cuota}."
            for s, cuota in cuotas.items() if cuenta[s] > cuota
        ]
        chequeos.append(_chequeo("Secciones del plan", errores, "Solo secciones del plan y sin pasarse de la cuota."))

    # 8. Pedido (spec 40): con 2 o más notas [pedido] el resumen usa al menos 2; con 1, esa.
    if pedidas:
        usadas = len(set(pedidas) & set(_links(texto)))
        necesarias = 2 if len(pedidas) >= 2 else 1
        errores = []
        if usadas < necesarias:
            errores.append(
                f"Pedido: la persona pidió algo hoy y el resumen incluye {usadas} de las notas marcadas con [pedido]; "
                f"tiene que incluir al menos {necesarias}."
            )
        chequeos.append(_chequeo("Pedido", errores, f"Al menos {necesarias} nota(s) del pedido incluida(s)."))

    return chequeos


# --- Chequeo con modelo ------------------------------------------------------

def interpretar_veredicto(salida: str | None) -> list[str]:
    """Convierte la respuesta del corrector en una lista de problemas (vacía si está OK)."""
    lineas = [linea.strip() for linea in (salida or "").splitlines() if linea.strip()]
    problemas = [linea[2:].strip() for linea in lineas if linea.startswith("- ")]
    if problemas:
        return problemas
    if lineas and lineas[0].upper().rstrip(".") == "OK":
        return []
    return ["El corrector no devolvió un veredicto claro (se esperaba OK o una lista de problemas)."]


def verificar_con_modelo(texto: str, notas: list[Nota], ruta_skill: str = ARCHIVO_SKILL,
                         carpeta: str = CARPETA_PROYECTO) -> list[str]:
    """Chequeo con modelo. Devuelve la lista de problemas. Levanta ErrorResumen si `claude` falla."""
    instrucciones = resumen.leer_instrucciones(ruta_skill)
    lineas = []
    for nota in notas:
        linea = f"- {' '.join(nota['titulo'].split())} ({nota['medio']}). Link: {nota['link']}"
        bajada = " ".join((nota.get("bajada") or "").split())
        if bajada:
            linea += f"\n  Bajada: {bajada}"
        lineas.append(linea)
    lista = "\n".join(lineas)
    pedido = (
        instrucciones
        + "\n\n## Resumen a revisar\n\n" + texto
        + "\n\n## Notas de ayer\n\n" + lista + "\n"
    )
    return interpretar_veredicto(resumen.ejecutar_claude(pedido, carpeta))


# --- Ciclo de revisión -------------------------------------------------------

def revisar(redactar: Callable[[list[str] | None, str | None], str], notas: list[Nota], tope: int,
            previos: list[str] | None = None,
            verificar_modelo: Callable[[str], list[str]] | None = None,
            minimo: int = MINIMO_PALABRAS, maximo: int = MAXIMO_PALABRAS,
            reintentos: int = REINTENTOS, plan: list[CupoSeccion] | None = None,
            plan_completo: bool = True, pedidas: list[str] | None = None) -> Revision:
    """Redacta, revisa y reintenta. Devuelve {"texto": ..., "chequeo": {...}}.

    `redactar(correcciones, borrador)` devuelve un texto; en el primer intento
    las dos son None. Si devuelve error (ErrorResumen), se propaga.
    `previos` son los textos de los últimos resúmenes guardados.
    `verificar_modelo(texto)` devuelve la lista de problemas del modelo; si es
    None no se hace el chequeo con modelo. Si levanta ErrorResumen, no se
    reintenta la redacción: queda como "no se pudo revisar" en el aviso.

    `plan`, `plan_completo` y `pedidas` (spec 40) son el plan de secciones del día y los links de las
    notas [pedido]; sin ellos no se hacen los chequeos "Secciones del plan" y "Pedido".

    `chequeo` tiene: aprobado, intentos, verificado (lo que pasó en el último
    intento), no_cumple (lo que falló) y omitido (lo que no se pudo chequear).
    """
    intentos = 0
    correcciones = None
    borrador = None
    while True:
        intentos += 1
        texto = redactar(correcciones, borrador)
        chequeos = _chequear_codigo(texto, notas, tope, previos, minimo, maximo,
                                    plan, plan_completo, pedidas)
        errores = [error for chequeo in chequeos for error in chequeo["errores"]]
        omitidos = [chequeo["detalle"] for chequeo in chequeos if chequeo.get("omitido")]
        verificados = [chequeo["detalle"] for chequeo in chequeos if not chequeo["errores"] and not chequeo.get("omitido")]
        tecnico = False

        if not errores and verificar_modelo is not None:
            try:
                problemas = verificar_modelo(texto)
            except resumen.ErrorResumen as error:
                tecnico = True
                errores.append(f"No se pudo revisar el contenido con el modelo: {error.mensaje}")
                omitidos.append("Revisión de contenido con el modelo: no se pudo hacer.")
            else:
                if problemas:
                    errores.extend(problemas)
                else:
                    verificados.append("Contenido: cada nota respaldada por su título, bajada y medio.")

        if not errores:
            return _resultado(texto, True, intentos, verificados, [], omitidos)
        if tecnico or intentos > reintentos:
            return _resultado(texto, False, intentos, verificados, errores, omitidos)
        correcciones = errores
        borrador = texto


def _resultado(texto: str, aprobado: bool, intentos: int, verificados: list[str], no_cumple: list[str],
               omitidos: list[str]) -> Revision:
    return {
        "texto": texto,
        "chequeo": {
            "aprobado": aprobado,
            "intentos": intentos,
            "verificado": verificados,
            "no_cumple": no_cumple,
            "omitido": omitidos,
        },
    }
