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

from typing import Any, NotRequired, TypedDict


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
    bajada: NotRequired[str]  # spec 38: description del RSS, limpia; ausente en datos viejos
    categorias: NotRequired[list[str]]  # spec 38: category del RSS; ausente en datos viejos
    subtema: NotRequired[str]  # spec 45: solo en notas de Deportes


class NotaDeFeed(TypedDict):
    """Una nota recién leída de un RSS, antes de filtrar: `fecha` es un datetime de Buenos Aires."""

    titulo: str
    link: str
    fecha: Any  # datetime
    medio: str
    seccion: str
    bajada: NotRequired[str]
    categorias: NotRequired[list[str]]
    subtema: NotRequired[str]  # spec 45: solo en notas de Deportes


class _FuenteRSSBase(TypedDict):
    medio: str
    seccion: str
    url: str


class FuenteRSS(_FuenteRSSBase, total=False):
    """Un feed RSS de micafe/config.py. `reclasificar_por_categoria` es opcional (spec 44)."""

    reclasificar_por_categoria: bool
    subtema: str  # spec 45: subtema de Deportes que declara el feed


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


class PreferenciasV1(TypedDict):
    """El formato viejo de datos/preferencias.json: claves de indicadores y nombres de temas elegidos."""

    indicadores: list[str]
    temas: list[str]


class PreferenciaDeTema(TypedDict):
    """Un tema en las preferencias v2: si está activo y qué prioridad tiene ("alta", "normal" o "baja")."""

    activo: bool
    prioridad: str


class MediosPreferidos(TypedDict):
    preferidos: list[str]
    excluidos: list[str]


class PalabrasPreferidas(TypedDict):
    seguir: list[str]
    evitar: list[str]


class Preferencias(TypedDict):
    """Lo guardado en datos/preferencias.json (esquema v2, spec 49). `temas` trae todos los de config.TEMAS."""

    version: int
    temas: dict[str, PreferenciaDeTema]
    subtemas: list[str]
    medios: MediosPreferidos
    palabras: PalabrasPreferidas
    indicadores: list[str]


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


class Perfil(TypedDict):
    """Lo que el código aprendió de los votos (spec 41): puntajes entre -TOPE_PERFIL y +TOPE_PERFIL."""

    secciones: dict[str, float]
    medios: dict[str, float]
    terminos: dict[str, float]
    votos_contados: int  # votos que cuentan (sin los anteriores al reinicio ni los de fecha ilegible o futura)


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


class NotaPuntuada(TypedDict):
    """Una candidata con su puntaje y los motivos cortos de ese puntaje (spec 39)."""

    nota: Nota
    puntaje: float
    motivos: list[str]
    encaja: bool  # True si algún término del pedido aparece en la nota


class Seleccion(TypedDict):
    """Resultado de seleccion.elegir_candidatas (spec 39).

    `motivos` va por link y solo trae las notas que sumaron puntaje; `encajan` son los links
    de las notas que encajan con el pedido.
    """

    candidatas: list[Nota]
    motivos: dict[str, list[str]]
    encajan: list[str]
    pedido_sin_notas: bool


class CupoSeccion(TypedDict):
    """Cuántas notas lleva una sección en el plan del día (spec 40)."""

    seccion: str
    cupo: int
    pedidas: int  # notas [pedido] que la sección tiene entre las candidatas
    motivos: list[str]  # por qué el cupo quedó así (pedido, falta de notas, tope por medio)
    prioridad: NotRequired[str]  # spec 49: "alta" o "baja"; ausente si es "normal"


class PlanDelDia(TypedDict):
    """El plan que se guarda en el resumen: secciones con su cupo y si llegó a NOTAS_OBJETIVO."""

    secciones: list[CupoSeccion]
    completo: bool


class ResumenGuardado(TypedDict):
    """Lo guardado en datos/resumenes/AAAA-MM-DD.json."""

    fecha: str
    generado_en: str
    indicadores: list[Indicador]
    texto: str
    chequeo: Chequeo
    pedido: NotRequired[str]  # solo si la persona pidió algo ese día (spec 35)
    pedido_sin_notas: NotRequired[bool]  # spec 39: True si había pedido y ninguna nota encajó
    plan: NotRequired[PlanDelDia]  # spec 40; los resúmenes viejos no lo tienen
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
