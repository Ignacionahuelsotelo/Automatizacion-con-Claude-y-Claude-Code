"""Servicio de Mi Café: las operaciones de la app, sin saber nada de HTTP (spec 22).

La capa web (micafe/web/) solo llama a estas funciones. Devuelven datos o levantan
los errores de micafe/errores.py. Los guardados que validan devuelven `(datos, errores)`:
si `errores` no está vacía, no se guardó nada y la capa web responde 400 con esa lista.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Callable

from micafe.almacen import gustos, preferencias, resumenes
from micafe.config import (
    ARCHIVO_ACCIONES, ARCHIVO_GUSTOS, ARCHIVO_INDICADORES, ARCHIVO_PREFERENCIAS, CANDIDATAS_POR_MEDIO_Y_SECCION,
    CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES, CARPETA_RESUMENES, MAXIMO_CARACTERES_PALABRA, MAXIMO_PALABRAS_PREFERENCIA,
    PRIORIDADES_TEMA, SUBTEMAS, TEMAS, TOPE_POR_MEDIO_LUNES, ZONA,
)
from micafe.dominio import caja, corrector, perfil, resumen, seleccion
from micafe.dominio.pedido import validar_pedido
from micafe.dominio.progreso import Progreso
from micafe.errores import ErrorAlmacenamiento, ErrorMiCafe, ErrorResumen
from micafe.fuentes import acciones, indicadores, noticias
from micafe.modelos import (
    Perfil, Preferencias, RespuestaDePregunta, ResultadoIndicadores, ResultadoNoticias, ResumenGuardado, Voto,
)

logger = logging.getLogger(__name__)

MENSAJE_YA_EN_CURSO = "Ya se está preparando un resumen. Esperá a que termine."
MENSAJE_ERROR_INESPERADO = "Pasó un error inesperado al preparar el resumen. Mirá la consola del servidor."

# Estado del armado del resumen (en memoria, un solo armado a la vez). Los tests lo reemplazan.
progreso_resumen = Progreso()

# Las rutas vienen de micafe/config.py y quedan como nombres de este módulo para que
# los tests puedan reemplazarlas por carpetas temporales.


def indicadores_con_acciones(datos: ResultadoIndicadores, prefs: Preferencias) -> ResultadoIndicadores:
    """Suma las acciones y sus avisos a los indicadores, solo si el usuario eligió "acciones".

    `datos` es lo que devuelve indicadores.obtener(); se devuelve el mismo diccionario
    con la lista y los avisos unidos (spec 15).
    """
    if "acciones" not in prefs["indicadores"]:
        return datos
    extra = acciones.obtener_todo(ARCHIVO_ACCIONES)
    return {**datos, "indicadores": datos["indicadores"] + extra["indicadores"],
            "avisos": datos["avisos"] + extra["avisos"]}


def leer_preferencias() -> tuple[Preferencias, str | None]:
    """Devuelve `(preferencias, aviso)`."""
    return preferencias.leer(ARCHIVO_PREFERENCIAS)


def opciones_de_preferencias() -> dict[str, Any]:
    """Las opciones cerradas que la página ofrece (spec 49): el front no copia listas ni topes."""
    return {
        "indicadores": preferencias.INDICADORES,
        "secciones": list(TEMAS),
        "subtemas": list(SUBTEMAS),
        "medios": preferencias.medios_disponibles(),
        "prioridades": list(PRIORIDADES_TEMA),
        "maximo_palabras": MAXIMO_PALABRAS_PREFERENCIA,
        "maximo_caracteres": MAXIMO_CARACTERES_PALABRA,
    }


def guardar_preferencias(datos: Any) -> tuple[Preferencias | None, list[str]]:
    """Devuelve `(preferencias, errores)`; levanta ErrorAlmacenamiento si no puede escribir."""
    try:
        return preferencias.guardar(ARCHIVO_PREFERENCIAS, datos)
    except OSError as error:
        logger.error(f"Aviso: no se pudo guardar las preferencias. Detalle: {error}")
        raise ErrorAlmacenamiento(
            "No se pudo guardar las preferencias. Revisá los permisos de la carpeta datos/.") from error


def obtener_indicadores() -> ResultadoIndicadores:
    """Los indicadores que eligió la persona (con acciones si corresponde), con fecha y fuente."""
    prefs, _ = preferencias.leer(ARCHIVO_PREFERENCIAS)
    datos = indicadores.obtener(ARCHIVO_INDICADORES, prefs["indicadores"])
    return indicadores_con_acciones(datos, prefs)


def obtener_noticias(ahora: datetime | None = None) -> ResultadoNoticias:
    """Las notas de ayer de los temas elegidos, con link, y las fuentes que fallaron.

    Spec 42: vienen ordenadas por el puntaje del servidor (el pedido de hoy, si hay, y los gustos)
    y cada nota trae `motivos`.
    """
    ahora = ahora or datetime.now(ZONA)
    prefs, _ = preferencias.leer(ARCHIVO_PREFERENCIAS)
    datos = noticias.obtener(preferencias.temas_activos(prefs))
    guardado = resumenes.leer_ultimo(CARPETA_RESUMENES)
    pedido = guardado.get("pedido") if guardado and guardado.get("fecha") == ahora.date().isoformat() else None
    terminos = seleccion.terminos_del_pedido(pedido if isinstance(pedido, str) else None)
    return {**datos, "notas": seleccion.ordenar_por_puntaje(datos["notas"], terminos, _perfil(ahora), prefs)}


def ultimo_resumen() -> ResumenGuardado | None:
    """El último resumen guardado, o None si no hay (no llama a Claude)."""
    guardado = resumenes.leer_ultimo(CARPETA_RESUMENES)
    return _con_notas(guardado) if guardado else None


def _con_notas(guardado: ResumenGuardado) -> ResumenGuardado:
    """Suma `notas` (calculadas, no guardadas en el archivo) para poder votarlas (spec 31).

    Spec 42: si el pedido no encontró notas, suma `temas_destildados_pedido` (los temas que el
    pedido nombra y que hoy están destildados) para que la página explique por qué.
    """
    extra: dict[str, Any] = {"notas": corrector.notas_votables(guardado.get("texto"))}
    if guardado.get("pedido_sin_notas") is True and isinstance(guardado.get("pedido"), str):
        prefs, _ = preferencias.leer(ARCHIVO_PREFERENCIAS)
        extra["temas_destildados_pedido"] = seleccion.temas_destildados_nombrados(guardado["pedido"], preferencias.temas_activos(prefs))
    return {**guardado, **extra}


def leer_votos() -> tuple[list[Voto], str | None]:
    """Devuelve `(votos, aviso)`."""
    return gustos.leer(ARCHIVO_GUSTOS)


def guardar_voto(datos: Any) -> tuple[list[Voto] | None, list[str]]:
    """Devuelve `(votos, errores)`; levanta ErrorAlmacenamiento si no puede escribir."""
    try:
        return gustos.guardar(ARCHIVO_GUSTOS, datos)
    except OSError as error:
        logger.error(f"Aviso: no se pudo guardar el voto. Detalle: {error}")
        raise ErrorAlmacenamiento("No se pudo guardar el voto. Revisá los permisos de la carpeta datos/.") from error


def _perfil(ahora: datetime | None = None) -> Perfil:
    """El perfil de gustos de hoy. Si gustos.json falta o está roto, es un perfil vacío y todo sigue."""
    votos, _ = gustos.leer(ARCHIVO_GUSTOS)
    return perfil.calcular(votos, ahora or datetime.now(ZONA), gustos.leer_reinicio(ARCHIVO_GUSTOS))


def _perfil_para_mostrar(calculado: Perfil) -> dict[str, Any]:
    """El perfil en formato apto para mostrar: prioridades con signo y etiqueta, sin puntajes."""
    return {
        "prioridades": perfil.prioridades(calculado),
        "reiniciado_en": gustos.leer_reinicio(ARCHIVO_GUSTOS),
        "votos_que_cuentan": calculado["votos_contados"],
    }


def obtener_perfil() -> dict[str, Any]:
    """Lo aprendido de los votos, para mostrar (spec 41). Sin votos, las listas vienen vacías."""
    return _perfil_para_mostrar(_perfil())


def reiniciar_perfil(datos: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Ignora lo aprendido hasta ahora (no borra votos). Devuelve `(perfil, errores)`.

    Exige `{"confirmar": true}`. Levanta ErrorAlmacenamiento si no puede escribir.
    """
    if not isinstance(datos, dict) or datos.get("confirmar") is not True:
        return None, ["Confirmá el reinicio para ignorar lo aprendido."]
    try:
        gustos.reiniciar(ARCHIVO_GUSTOS)
    except OSError as error:
        logger.error(f"Aviso: no se pudo reiniciar lo aprendido. Detalle: {error}")
        raise ErrorAlmacenamiento("No se pudo reiniciar lo aprendido. Revisá los permisos de la carpeta datos/.") from error
    logger.info("Lo aprendido se reinició")
    return obtener_perfil(), []


def responder_pregunta(datos: Any) -> RespuestaDePregunta:
    """Responde una pregunta sobre una nota del resumen guardado (ver caja.responder)."""
    return caja.responder(datos)


def estado_de_claude() -> dict[str, Any]:
    """Si `claude` está disponible: `{"disponible", "estado", "mensaje"}` (ver resumen.comprobar_claude)."""
    return resumen.comprobar_claude()


def preparar_resumen(ahora: datetime | None = None,
                     avisar: Callable[[str, int | None], None] | None = None,
                     pedido: str | None = None) -> dict[str, Any]:
    """Arma el resumen de hoy de punta a punta, lo guarda y devuelve `{"resumen": ..., "avisos": ...}`.

    `avisar(etapa, intento)` se llama al empezar cada etapa de ETAPAS_RESUMEN (spec 30); es opcional.
    `pedido` es el pedido de noticias ya validado (spec 35): va a la redacción y se guarda, pero no llega al corrector.

    Levanta ErrorResumen (con los avisos en `extras`) si Claude o el corrector fallan, y
    ErrorAlmacenamiento si no puede guardarlo.
    """
    def marcar(etapa: str, intento: int | None = None) -> None:
        if avisar is not None:
            avisar(etapa, intento)

    if pedido:
        logger.info("Pedido de la persona: sí (%d caracteres)", len(pedido))  # nunca el texto
    # Primero se chequea Claude: si no está, no se consulta ninguna fuente (spec 29).
    marcar("claude")
    chequeo = resumen.comprobar_claude()
    if not chequeo["disponible"]:
        raise ErrorResumen(str(chequeo["mensaje"]), codigo=503)
    ahora = ahora or datetime.now(ZONA)
    prefs, _ = preferencias.leer(ARCHIVO_PREFERENCIAS)
    marcar("noticias")
    temas_elegidos = preferencias.temas_activos(prefs)
    datos_noticias = noticias.obtener(temas_elegidos)
    marcar("indicadores")
    datos_indicadores = indicadores.obtener(ARCHIVO_INDICADORES, prefs["indicadores"])
    datos_indicadores = indicadores_con_acciones(datos_indicadores, prefs)
    lista_indicadores = datos_indicadores["indicadores"]
    # Avisos de fuentes caídas o datos viejos: la página los muestra junto al resumen (spec 12).
    avisos = {"indicadores": datos_indicadores["avisos"], "noticias": datos_noticias["fallas"]}
    # Spec 41: lo aprendido de los votos (con peso decreciente en el tiempo) entra a la selección y al plan.
    perfil_de_hoy = _perfil(ahora)
    # Spec 39: el código ordena las candidatas con el pedido y le pasa a Claude las mejores.
    terminos = seleccion.terminos_del_pedido(pedido)
    cupo = (CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES if datos_noticias["tope_por_medio"] == TOPE_POR_MEDIO_LUNES
            else CANDIDATAS_POR_MEDIO_Y_SECCION)
    elegidas = seleccion.elegir_candidatas(datos_noticias["notas"], prefs, terminos, perfil_de_hoy,
                                           tope_por_medio_y_seccion=cupo)
    notas = elegidas["candidatas"]
    pedidas = {link: elegidas["motivos"].get(link, []) for link in elegidas["encajan"]}
    pedido_sin_notas = elegidas["pedido_sin_notas"]
    if terminos:  # solo cantidades: nunca el pedido, los términos ni los sinónimos
        logger.info("Pedido: encajaron %d notas de %d candidatas", len(pedidas), len(notas))
    # Spec 40: el código calcula cuántas notas lleva cada sección; Claude y el corrector siguen ese plan.
    secciones_plan = seleccion.plan_de_secciones(notas, temas_elegidos, seleccion.pesos_de_secciones(perfil_de_hoy), datos_noticias["tope_por_medio"],
                                                 pedidas=set(pedidas), prioridades=preferencias.prioridades_de_temas(prefs))
    completo = seleccion.plan_completo(secciones_plan) if secciones_plan else True  # sin plan, se exige el largo de siempre
    plan_guardado = {"secciones": secciones_plan, "completo": completo} if secciones_plan else None
    lineas_prioridades = perfil.lineas_para_pedido(perfil_de_hoy)
    logger.info("Preferencias: %d medios preferidos, %d excluidos, %d palabras a seguir, %d a evitar, %d subtemas",
                len(prefs["medios"]["preferidos"]), len(prefs["medios"]["excluidos"]),
                len(prefs["palabras"]["seguir"]), len(prefs["palabras"]["evitar"]), len(prefs["subtemas"]))  # solo cantidades
    logger.info("Perfil: %d votos cuentan, %d prioridades al prompt", perfil_de_hoy["votos_contados"], len(lineas_prioridades))

    redacciones = 0

    def redactar(correcciones: list[str] | None, borrador: str | None) -> str:
        """Pide a Claude el texto del resumen; el corrector la llama de nuevo en cada reintento."""
        nonlocal redacciones
        redacciones += 1
        marcar("redactando", redacciones)
        texto = resumen.generar(
            notas,
            tope=datos_noticias["tope_por_medio"],
            correcciones=correcciones,
            borrador=borrador,
            prioridades=lineas_prioridades,
            preferencias=prefs,
            pedido=pedido,
            pedidas=pedidas,
            plan=secciones_plan or None,
            plan_completo=completo,
        )
        marcar("corrigiendo")
        return texto

    try:
        revision = corrector.revisar(
            redactar,
            notas,
            tope=datos_noticias["tope_por_medio"],
            previos=resumenes.leer_previos(CARPETA_RESUMENES, anteriores_a=ahora.astimezone(ZONA).date().isoformat()),
            plan=secciones_plan or None,
            plan_completo=completo,
            pedidas=list(pedidas),
            verificar_modelo=lambda texto: corrector.verificar_con_modelo(texto, notas),
        )
    except resumen.ErrorResumen as error:
        error.extras = {"avisos": avisos}
        raise
    marcar("guardando")
    try:
        registro = resumenes.guardar(
            revision["texto"], lista_indicadores, revision["chequeo"], ahora, CARPETA_RESUMENES,
            pedido=pedido, pedido_sin_notas=pedido_sin_notas, plan=plan_guardado,
        )
    except OSError as error:
        logger.error(f"Aviso: no se pudo guardar el resumen. Detalle: {error}")
        raise ErrorAlmacenamiento(
            "No se pudo guardar el resumen. Revisá los permisos de la carpeta datos/.",
            extras={"avisos": avisos},
        ) from error
    return {"resumen": _con_notas(registro), "avisos": avisos}


def _armar_en_hilo(progreso: Progreso, pedido: str | None = None) -> None:
    """Cuerpo del hilo: arma el resumen y deja el resultado o el fallo en `progreso`. Nunca levanta."""
    try:
        progreso.terminar(preparar_resumen(avisar=progreso.avanzar, pedido=pedido))
    except ErrorMiCafe as error:
        logger.warning("Aviso: no se pudo preparar el resumen: %s", error.mensaje)
        progreso.fallar([error.mensaje], error.extras)
    except Exception:  # último recurso del hilo: si se escapara, el estado quedaría "en_curso" para siempre
        logger.exception("Aviso: error inesperado al preparar el resumen.")
        progreso.fallar([MENSAJE_ERROR_INESPERADO])


def iniciar_resumen(datos: Any = None) -> tuple[dict[str, Any] | None, list[str]]:
    """Empieza a armar el resumen en un hilo y devuelve `(estado_inicial, errores)`.

    `datos` es el cuerpo del POST: None o un objeto con `pedido` opcional (spec 35). Si el
    cuerpo o el pedido no sirven, devuelve `(None, errores)` y no inicia nada.
    Levanta ErrorResumen (409) si ya hay un armado en curso.
    """
    if datos is not None and not isinstance(datos, dict):
        return None, ["El cuerpo tiene que ser un objeto con el campo \"pedido\"."]
    pedido, errores = validar_pedido((datos or {}).get("pedido"))
    if errores:
        return None, errores
    progreso = progreso_resumen
    if not progreso.iniciar():
        raise ErrorResumen(MENSAJE_YA_EN_CURSO, codigo=409)
    threading.Thread(target=_armar_en_hilo, args=(progreso, pedido), daemon=True, name="armado-resumen").start()
    return progreso.instantanea(), []


def estado_del_resumen() -> dict[str, Any]:
    """El estado del armado: libre, en_curso, listo o fallo (ver Progreso.instantanea)."""
    return progreso_resumen.instantanea()
