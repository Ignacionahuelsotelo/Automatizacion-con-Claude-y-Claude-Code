"""Formas de los datos que circulan por Mi Café (spec 23).

Son `TypedDict`: describen los diccionarios que ya existían, con las mismas claves.
No cambian nada en tiempo de ejecución ni el JSON que se guarda en datos/ o que
recibe y manda la página; sirven para documentar y para que un editor o una
herramienta de tipos los entienda.

Reglas de CLAUDE.md que se ven en estas formas:
- Ningún número lo escribe el modelo: `Indicador.valor` sale de las APIs, con
  `fecha` y `fuente`; si no hay dato confiable es None ("sin dato").
- Toda noticia lleva link: `Nota.link` nunca falta.
"""

from __future__ import annotations

from typing import Any, TypedDict


class Indicador(TypedDict):
    """Un indicador con su valor ya formateado ("$ 1.234,50"), fecha y fuente.

    Sin dato confiable, `valor` y `fecha` son None. `desactualizado` marca los datos con
    más de 1 día hábil de antigüedad.
    """

    clave: str
    grupo: str
    nombre: str
    valor: str | None
    fecha: str | None
    fuente: str
    desactualizado: bool


class Nota(TypedDict):
    """Una noticia de ayer (como la devuelve /api/noticias): `fecha` es "dd/mm/aaaa hh:mm"."""

    titulo: str
    medio: str
    seccion: str
    fecha: str
    link: str


class NotaDeFeed(TypedDict):
    """Una nota recién leída de un RSS, antes de filtrar: `fecha` es un datetime de Buenos Aires."""

    titulo: str
    link: str
    fecha: Any  # datetime
    medio: str
    seccion: str


class FuenteRSS(TypedDict):
    """Un feed RSS de micafe/config.py."""

    medio: str
    seccion: str
    url: str


class FallaDeFuente(TypedDict):
    """Un feed que no respondió: el motivo va en español y sin texto técnico."""

    medio: str
    seccion: str
    motivo: str


class ConteoDeFuente(TypedDict):
    """Diagnóstico de un feed leído: notas que tenía, que caen en la ventana y que quedaron elegidas."""

    medio: str
    seccion: str
    leidas: int
    en_ventana: int
    elegidas: int


class VentanaNoticias(TypedDict):
    """Días que cubren las notas, "dd/mm/aaaa"."""

    desde: str
    hasta: str


class ResultadoNoticias(TypedDict):
    """Respuesta de noticias.obtener y de /api/noticias."""

    notas: list[Nota]
    fallas: list[FallaDeFuente]
    por_fuente: list[ConteoDeFuente]
    ventana: VentanaNoticias
    tope_por_medio: int
    generado_en: str


class ResultadoIndicadores(TypedDict):
    """Respuesta de indicadores.obtener y de /api/indicadores."""

    indicadores: list[Indicador]
    generado_en: str
    avisos: list[str]


class ResultadoAcciones(TypedDict):
    """Respuesta de acciones.obtener y obtener_todo: sin `generado_en`."""

    indicadores: list[Indicador]
    avisos: list[str]


class ResultadoMerval(TypedDict):
    """Respuesta de acciones.obtener_merval."""

    indicador: Indicador
    avisos: list[str]


class Preferencias(TypedDict):
    """Lo guardado en datos/preferencias.json: claves de indicadores y nombres de temas elegidos."""

    indicadores: list[str]
    temas: list[str]


class _VotoBase(TypedDict):
    tipo: str  # "nota" o "tema"
    clave: str  # link de la nota o nombre del tema
    voto: str | None  # "me_gusta", "no_me_gusta" o None (quitar el voto, solo en el pedido)


class Voto(_VotoBase, total=False):
    """Un voto guardado en datos/gustos.json.

    `votado_en` está en los guardados; `titulo`, `medio` y `seccion` solo en las notas.
    """

    votado_en: str
    titulo: str
    medio: str
    seccion: str


class Chequeo(TypedDict):
    """Resultado de la revisión que se guarda junto al resumen (spec 07)."""

    aprobado: bool
    intentos: int
    verificado: list[str]
    no_cumple: list[str]
    omitido: list[str]


class Revision(TypedDict):
    """Lo que devuelve corrector.revisar: el último texto y su chequeo."""

    texto: str
    chequeo: Chequeo


class NotaDelResumen(TypedDict):
    """Una nota leída del texto del resumen, para votarla (spec 31)."""

    titulo: str
    medio: str
    seccion: str
    link: str


class ResumenGuardado(TypedDict):
    """Lo guardado en datos/resumenes/AAAA-MM-DD.json."""

    fecha: str
    generado_en: str
    indicadores: list[Indicador]
    texto: str
    chequeo: Chequeo
    pedido: NotRequired[str]  # solo si la persona pidió algo ese día (spec 35)
    notas: NotRequired[list[NotaDelResumen]]  # se calculan al responder, no se guardan en el archivo


class AvisosDelResumen(TypedDict):
    """Avisos de fuentes caídas o datos viejos que la página muestra junto al resumen (spec 12)."""

    indicadores: list[str]
    noticias: list[FallaDeFuente]


class RespuestaDeError(TypedDict, total=False):
    """Cuerpo JSON de un error: `ok` False y los mensajes en español; a veces `avisos`."""

    ok: bool
    errores: list[str]
    avisos: AvisosDelResumen


class PedidoDePregunta(TypedDict):
    """Pedido ya validado de /api/preguntas."""

    fecha: str
    link: str
    pregunta: str


class RespuestaDePregunta(TypedDict):
    """Respuesta de /api/preguntas (sin el `ok` que agrega la capa web)."""

    respuesta: str
    link: str
