"""Selección de candidatas por puntaje (spec 39).

Funciones puras: sin red, sin disco, sin `claude` y sin leer la hora del sistema. El código
ordena las notas de ayer con un puntaje que se puede explicar (el pedido de la persona y la
frescura) y le pasa a Claude las mejores. El pedido nunca se loguea: acá no se escribe ningún log.

Un término del pedido encaja con una nota si aparece, como palabra o frase y sin importar
mayúsculas ni tildes, en el título, la bajada o las categorías.
"""

from __future__ import annotations

from datetime import datetime, timezone

from micafe.almacen.preferencias import temas_activos
from micafe.config import (
    MAXIMO_CANDIDATAS_PARA_CLAUDE, MAXIMO_POR_SECCION, MAXIMO_PUNTAJE_PERFIL, MAXIMO_PUNTAJE_PREFERENCIAS,
    MINIMO_POR_SECCION_ACTIVA, NOTAS_OBJETIVO, PALABRAS_VACIAS_PEDIDO, PESO_MEDIO_PREFERIDO, PESO_MINIMO_SECCION,
    PESO_PALABRA_EVITAR, PESO_PALABRA_SEGUIR, PESO_PERFIL_MEDIO, PESO_PERFIL_SECCION, PESO_PERFIL_TERMINO,
    PESO_POR_NOTA_PEDIDA, PESO_PRIORIDAD_ALTA, PESO_PRIORIDAD_BAJA, PESO_SUBTEMA_ELEGIDO, PESO_SUBTEMA_NO_ELEGIDO,
    PESOS_PUNTAJE, SINONIMOS_TEMAS, TEMA_DE_CLAVE_SINONIMO, TEMAS,
)
from micafe.modelos import CupoSeccion, Nota, NotaPuntuada, Perfil, Preferencias, Seleccion
from micafe.textos import normalizar_texto

FORMATO_FECHA = "%d/%m/%Y %H:%M"  # como viene `Nota["fecha"]`


def _contiene(texto_normalizado: str, termino: str) -> bool:
    """True si `termino` (ya normalizado) aparece como palabra o frase completa en el texto."""
    return bool(termino) and f" {termino} " in f" {texto_normalizado} "


def terminos_del_pedido(texto: str | None) -> list[str]:
    """Los términos del pedido, normalizados, sin palabras vacías, con sinónimos y sin repetidos.

    Si el pedido nombra una clave de `SINONIMOS_TEMAS` (por ejemplo "fútbol argentino"), se suma
    la frase y sus equivalentes. Un pedido vacío da `[]`.
    """
    restante = normalizar_texto(texto or "")
    if not restante:
        return []
    claves = sorted(((normalizar_texto(c), c) for c in SINONIMOS_TEMAS), key=lambda par: (-len(par[0]), par[0]))
    terminos: list[str] = []
    for clave_normalizada, clave in claves:
        if _contiene(restante, clave_normalizada):
            terminos.append(clave_normalizada)
            terminos.extend(normalizar_texto(s) for s in SINONIMOS_TEMAS[clave])
            restante = f" {restante} ".replace(f" {clave_normalizada} ", " ").strip()
    terminos.extend(p for p in restante.split() if p not in PALABRAS_VACIAS_PEDIDO)
    vistos: set[str] = set()
    unicos = []
    for termino in terminos:
        if termino and termino not in vistos:
            vistos.add(termino)
            unicos.append(termino)
    return unicos


def terminos_de_titulo(titulo: str) -> list[str]:
    """Los términos de un título: normalizados, sin palabras vacías, de 3 letras o más y sin repetidos."""
    vistos: dict[str, None] = {}
    for palabra in normalizar_texto(titulo).split():
        if len(palabra) >= 3 and palabra not in PALABRAS_VACIAS_PEDIDO:
            vistos[palabra] = None
    return list(vistos)


def _aporte_del_perfil(nota: Nota, perfil: Perfil) -> tuple[float, list[str]]:
    """Puntaje y motivos que suma el perfil a una nota (acotado a +-MAXIMO_PUNTAJE_PERFIL)."""
    del_medio = PESO_PERFIL_MEDIO * perfil["medios"].get(nota.get("medio", ""), 0.0)
    de_terminos = PESO_PERFIL_TERMINO * sum(perfil["terminos"].get(t, 0.0) for t in terminos_de_titulo(nota.get("titulo", "")))
    motivos = []
    if del_medio > 0:
        motivos.append("medio que te gusta")
    if de_terminos > 0:
        motivos.append("te gustó algo parecido")
    total = max(-MAXIMO_PUNTAJE_PERFIL, min(MAXIMO_PUNTAJE_PERFIL, del_medio + de_terminos))
    return total, motivos


def pesos_de_secciones(perfil: Perfil | None) -> dict[str, float]:  # la prioridad de cada tema se aplica en el plan
    """Peso de cada sección en el plan según el perfil: 1 sin datos, más si te gusta, menos si no."""
    if not perfil:
        return {}
    return {s: max(PESO_MINIMO_SECCION, 1.0 + PESO_PERFIL_SECCION * v) for s, v in perfil["secciones"].items() if s in TEMAS}


FACTOR_DE_PRIORIDAD = {"alta": PESO_PRIORIDAD_ALTA, "normal": 1.0, "baja": PESO_PRIORIDAD_BAJA}
RANGO_DE_PRIORIDAD = {"alta": 0, "normal": 1, "baja": 2}  # para ordenar: la alta se recorta última


def _aporte_de_preferencias(nota: Nota, prefs: Preferencias | None) -> tuple[float, list[str]]:
    """Puntaje y motivos que suman las preferencias v2 (spec 49), acotado a +-MAXIMO_PUNTAJE_PREFERENCIAS.

    Medio preferido y palabras a seguir suman; palabras a evitar y subtemas no elegidos restan; un
    subtema elegido suma. Las palabras se buscan como palabra o frase, sin mayúsculas ni tildes, en
    el título, la bajada y las categorías. Con preferencias del formato viejo no suma nada.
    """
    if not prefs:
        return 0.0, []
    total = 0.0
    motivos: list[str] = []
    if nota.get("medio") in (prefs.get("medios") or {}).get("preferidos", []):
        total += PESO_MEDIO_PREFERIDO
        motivos.append("medio preferido")
    texto = normalizar_texto(" ".join([nota.get("titulo", ""), nota.get("bajada", ""),
                                       " ".join(nota.get("categorias") or [])]))
    palabras = prefs.get("palabras") or {}
    if any(_contiene(texto, normalizar_texto(p)) for p in palabras.get("seguir", [])):
        total += PESO_PALABRA_SEGUIR
        motivos.append("palabra a seguir")
    if any(_contiene(texto, normalizar_texto(p)) for p in palabras.get("evitar", [])):
        total -= PESO_PALABRA_EVITAR
        motivos.append("palabra a evitar")
    elegidos = prefs.get("subtemas") or []
    if elegidos and nota.get("seccion") == "Deportes":
        if (nota.get("subtema") or "Otros") in elegidos:
            total += PESO_SUBTEMA_ELEGIDO
            motivos.append("subtema elegido")
        else:
            total -= PESO_SUBTEMA_NO_ELEGIDO
            motivos.append("subtema no elegido")
    return max(-MAXIMO_PUNTAJE_PREFERENCIAS, min(MAXIMO_PUNTAJE_PREFERENCIAS, total)), motivos


def habilitadas(notas: list[Nota], prefs: Preferencias | None) -> list[Nota]:
    """Las notas que pueden entrar: sin las de temas destildados ni las de medios excluidos (nunca entran)."""
    if not prefs:
        return list(notas)
    temas = set(temas_activos(prefs))
    excluidos = set((prefs.get("medios") or {}).get("excluidos", []))
    return [n for n in notas
            if (not n.get("seccion") or n["seccion"] in temas) and n.get("medio") not in excluidos]


def _segundos(nota: Nota) -> float:
    """Instante de la nota en segundos; 0 si la fecha no se puede leer. Sin zona: solo sirve para comparar."""
    try:
        return datetime.strptime(nota.get("fecha", ""), FORMATO_FECHA).replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return 0.0


def _motivos_de_pedido(nota: Nota, terminos: list[str]) -> tuple[float, list[str]]:
    """Puntaje y motivos por los términos del pedido (cada término suma por su mejor lugar)."""
    titulo = normalizar_texto(nota.get("titulo", ""))
    bajada = normalizar_texto(nota.get("bajada", ""))
    categorias = normalizar_texto(" ".join(nota.get("categorias") or []))
    subtema = normalizar_texto(nota.get("subtema") or "")
    puntaje = 0.0
    motivos: list[str] = []
    for termino in terminos:
        if _contiene(subtema, termino):  # spec 45: suma aparte de título/bajada
            puntaje += PESOS_PUNTAJE["subtema"]
            motivos.append(f"pedido: {termino} (subtema)")
        for lugar, texto in (("titulo", titulo), ("bajada", bajada), ("categoria", categorias)):
            if _contiene(texto, termino):
                puntaje += PESOS_PUNTAJE[lugar]
                motivos.append(f"pedido: {termino} ({lugar})")
                break
    return puntaje, motivos


def puntuar(notas: list[Nota], prefs: Preferencias | None, terminos: list[str],
            perfil: Perfil | None = None) -> list[NotaPuntuada]:
    """Puntaje y motivos de cada nota, en el mismo orden en que vienen.

    Suma: los términos del pedido (título > bajada > categoría) y la frescura, que va de 0 (la más
    vieja de la tanda) a `PESOS_PUNTAJE["frescura"]` (la más nueva), y el perfil de gustos (spec 41: medio y
    términos del título), que nunca llega a pesar lo que un término del pedido, y las preferencias
    (spec 49: medios, palabras y subtemas, ver `_aporte_de_preferencias`). Con `perfil` en None no suma
    el perfil. No descarta nada: eso lo hace `habilitadas`.
    """
    segundos = [_segundos(n) for n in notas]
    minimo, maximo = (min(segundos), max(segundos)) if segundos else (0.0, 0.0)
    puntuadas: list[NotaPuntuada] = []
    for nota, instante in zip(notas, segundos):
        puntaje, motivos = _motivos_de_pedido(nota, terminos)
        encaja = bool(motivos)
        if maximo > minimo:
            frescura = PESOS_PUNTAJE["frescura"] * (instante - minimo) / (maximo - minimo)
            if frescura > 0:
                puntaje += frescura
                motivos.append("frescura")
        aporte_prefs, motivos_prefs = _aporte_de_preferencias(nota, prefs)
        puntaje += aporte_prefs
        motivos.extend(motivos_prefs)
        if perfil:
            aporte, motivos_perfil = _aporte_del_perfil(nota, perfil)
            puntaje += aporte
            motivos.extend(motivos_perfil)
        puntuadas.append({"nota": nota, "puntaje": round(puntaje, 4), "motivos": motivos, "encaja": encaja})
    return puntuadas


def _clave_de_orden(p: NotaPuntuada) -> tuple[bool, float, float, str]:
    """Primero las que encajan con el pedido (el pedido siempre gana), después mayor puntaje, más nueva y link."""
    return (not p["encaja"], -p["puntaje"], -_segundos(p["nota"]), p["nota"]["link"])


def elegir_candidatas(notas: list[Nota], prefs: Preferencias | None, terminos: list[str],
                      perfil: Perfil | None = None, tope_por_medio_y_seccion: int = 8,
                      maximo: int = MAXIMO_CANDIDATAS_PARA_CLAUDE) -> Seleccion:
    """Las mejores candidatas para Claude, de mayor a menor puntaje.

    Primero se descartan las notas de temas destildados y de medios excluidos (nunca entran, ni por
    el pedido ni por sinónimos ni por las preferencias); después se puntúa, se ordena (empate: más nueva primero, luego por link), se
    respeta el tope por (medio, sección) y se corta en `maximo`.
    `pedido_sin_notas` es True si hay términos y ninguna nota habilitada encaja.
    """
    puntuadas = puntuar(habilitadas(notas, prefs), prefs, terminos, perfil)
    puntuadas.sort(key=_clave_de_orden)

    por_clave: dict[tuple[str, str], int] = {}
    elegidas: list[NotaPuntuada] = []
    for p in puntuadas:
        if len(elegidas) >= maximo:
            break
        clave = (p["nota"].get("medio", ""), p["nota"].get("seccion", ""))
        if por_clave.get(clave, 0) >= tope_por_medio_y_seccion:
            continue
        por_clave[clave] = por_clave.get(clave, 0) + 1
        elegidas.append(p)

    return {
        "candidatas": [p["nota"] for p in elegidas],
        "motivos": {p["nota"]["link"]: p["motivos"] for p in elegidas if p["motivos"]},
        "encajan": [p["nota"]["link"] for p in elegidas if p["encaja"]],
        "pedido_sin_notas": bool(terminos) and not any(p["encaja"] for p in puntuadas),
    }


def ordenar_por_puntaje(notas: list[Nota], terminos: list[str], perfil: Perfil | None = None,
                        prefs: Preferencias | None = None) -> list[dict]:
    """La lista "Noticias de ayer" en el orden del servidor (spec 42): de mayor a menor puntaje.

    Devuelve copias de las notas con `motivos` (lista, vacía si no suman nada). No descarta ni corta
    nada (salvo los medios excluidos, spec 49) y no expone el puntaje. Mismo orden que `elegir_candidatas`.
    """
    puntuadas = puntuar(habilitadas(notas, prefs) if prefs else notas, prefs, terminos, perfil)
    puntuadas.sort(key=_clave_de_orden)
    return [{**p["nota"], "motivos": p["motivos"]} for p in puntuadas]


def temas_destildados_nombrados(pedido: str | None, temas_elegidos: list[str]) -> list[str]:
    """Temas de `TEMAS` que el pedido nombra y que están destildados, en el orden de `TEMAS`.

    Un tema se nombra por su nombre o por una clave de `TEMA_DE_CLAVE_SINONIMO` ("fútbol" es Deportes).
    """
    texto = normalizar_texto(pedido or "")
    if not texto:
        return []
    nombrados = {t for t in TEMAS if _contiene(texto, normalizar_texto(t))}
    nombrados |= {t for clave, t in TEMA_DE_CLAVE_SINONIMO.items() if _contiene(texto, normalizar_texto(clave))}
    return [t for t in TEMAS if t in nombrados and t not in temas_elegidos]


# --- Plan de secciones (spec 40) ---------------------------------------------

def plan_de_secciones(candidatas: list[Nota], temas: list[str], pesos: dict[str, float] | None,
                      tope_por_medio: int, total: int = NOTAS_OBJETIVO,
                      pedidas: set[str] | list[str] | None = None,
                      prioridades: dict[str, str] | None = None) -> list[CupoSeccion]:
    """Cuántas notas lleva cada sección hoy, en el orden de `TEMAS`. Pura y determinista.

    Solo entran las secciones tildadas en `temas` con al menos una candidata. Cada una recibe
    `MINIMO_POR_SECCION_ACTIVA` y el resto se reparte (método D'Hondt) según su peso:
    `pesos.get(sección, 1.0)` multiplicado por el factor de su prioridad (spec 49: alta, normal o baja,
    en `prioridades`; sin dato es normal) más `PESO_POR_NOTA_PEDIDA` por cada candidata cuyo link está en `pedidas`.
    Ninguna sección pasa de `MAXIMO_POR_SECCION`. El plan nunca pide más notas de las que dan las
    candidatas con el tope por medio contado sobre el resumen entero, así que puede sumar menos
    que `total` (ver `plan_completo`). Las notas sin sección no entran en el plan.
    """
    pesos = pesos or {}
    prioridades = prioridades or {}
    pedidas = set(pedidas or ())
    disponibles: dict[str, dict[str, int]] = {}
    cantidad_pedidas: dict[str, int] = {}
    for nota in candidatas:
        seccion = nota.get("seccion", "")
        if seccion in TEMAS and seccion in temas:
            por_medio = disponibles.setdefault(seccion, {})
            medio = nota.get("medio", "")
            por_medio[medio] = por_medio.get(medio, 0) + 1
            if nota["link"] in pedidas:
                cantidad_pedidas[seccion] = cantidad_pedidas.get(seccion, 0) + 1
    activas = [s for s in TEMAS if s in disponibles]
    presupuesto: dict[str, int] = {}  # lo que le queda a cada medio del tope sobre el resumen entero
    cupos = {s: 0 for s in activas}

    def conceder(seccion: str) -> bool:
        """Suma una nota a la sección sacándola del medio con más margen. False si no se puede."""
        posibles = [m for m, n in disponibles[seccion].items() if n > 0 and presupuesto.get(m, tope_por_medio) > 0]
        if not posibles or cupos[seccion] >= MAXIMO_POR_SECCION:
            return False
        medio = min(posibles, key=lambda m: (-presupuesto.get(m, tope_por_medio), -disponibles[seccion][m], m))
        presupuesto[medio] = presupuesto.get(medio, tope_por_medio) - 1
        disponibles[seccion][medio] -= 1
        cupos[seccion] += 1
        return True

    def peso(seccion: str) -> float:
        factor = FACTOR_DE_PRIORIDAD.get(prioridades.get(seccion, "normal"), 1.0)
        return pesos.get(seccion, 1.0) * factor + PESO_POR_NOTA_PEDIDA * cantidad_pedidas.get(seccion, 0)

    # Si el mínimo no alcanza para todas (más secciones activas que `total`), quedan las de más peso.
    por_peso = sorted(activas, key=lambda s: (-peso(s), TEMAS.index(s)))
    for _ in range(MINIMO_POR_SECCION_ACTIVA):
        for seccion in por_peso:
            if sum(cupos.values()) < total:
                conceder(seccion)
    while sum(cupos.values()) < total:
        # Una sección sin cupo no se pudo habilitar ni con el mínimo: no entra al reparto.
        con_lugar = [s for s in activas if cupos[s] > 0 and cupos[s] < MAXIMO_POR_SECCION
                     and any(n > 0 and presupuesto.get(m, tope_por_medio) > 0 for m, n in disponibles[s].items())]
        if not con_lugar:
            break
        elegida = min(con_lugar, key=lambda s: (-peso(s) / (cupos[s] + 1), TEMAS.index(s)))
        conceder(elegida)

    plan: list[CupoSeccion] = []
    for seccion in activas:
        if cupos[seccion] == 0:
            continue
        motivos = []
        if cantidad_pedidas.get(seccion):
            motivos.append(f"{cantidad_pedidas[seccion]} nota(s) del pedido entre las candidatas")
        if pesos.get(seccion, 1.0) > 1.0:
            motivos.append("tema que te gusta")
        if prioridades.get(seccion) in ("alta", "baja"):
            motivos.append(f"prioridad {prioridades[seccion]}")
        if cupos[seccion] < MAXIMO_POR_SECCION and not any(
                n > 0 and presupuesto.get(m, tope_por_medio) > 0 for m, n in disponibles[seccion].items()):
            motivos.append("no hay más notas posibles (candidatas o tope por medio)")
        cupo: CupoSeccion = {"seccion": seccion, "cupo": cupos[seccion], "pedidas": cantidad_pedidas.get(seccion, 0),
                             "motivos": motivos}
        if prioridades.get(seccion) in ("alta", "baja"):
            cupo["prioridad"] = prioridades[seccion]
        plan.append(cupo)
    return plan


def plan_completo(plan: list[CupoSeccion], total: int = NOTAS_OBJETIVO) -> bool:
    """True si el plan llega a `total` notas. Un plan vacío no es completo."""
    return sum(c["cupo"] for c in plan) >= total


def orden_de_recorte(plan: list[CupoSeccion]) -> list[str]:
    """Secciones del plan de la que menos prioridad tiene a la que más: de ahí se recorta primero.

    Prioridad: más notas [pedido], después la prioridad del tema (spec 49: la baja se recorta antes),
    después más cupo (que ya refleja los pesos) y por último el orden de `TEMAS`.
    """
    mayor_a_menor = sorted(plan, key=lambda c: (-c["pedidas"], RANGO_DE_PRIORIDAD.get(c.get("prioridad", "normal"), 1),
                                                -c["cupo"], TEMAS.index(c["seccion"])))
    return [c["seccion"] for c in reversed(mayor_a_menor)]
