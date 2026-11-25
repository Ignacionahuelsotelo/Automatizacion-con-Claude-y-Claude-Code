"""Configuración de Mi Café: única fuente de verdad de rutas, zona, timeouts, URLs y topes (spec 19).

Los valores son los de siempre; acá solo están juntos. Los módulos reciben las rutas
por parámetro (los tests pasan carpetas temporales) y usan estas constantes como valor por defecto.

Variables de entorno opcionales (solo para pruebas y para correr en otra carpeta):
- MICAFE_DATOS: carpeta donde se guardan preferencias, gustos, copias y resúmenes.
  Sin ella se usa `datos/` en la raíz del proyecto.
El puerto y el host NO se sobrescriben: puerto fijo 8000 y solo 127.0.0.1.
"""

from __future__ import annotations

import os
from zoneinfo import ZoneInfo

# --- Servidor (decisión 4 de specs/README.md) ---------------------------------
HOST = "127.0.0.1"
PUERTO = 8000
# Cola de escucha del servidor: el 5 por defecto de http.server se desborda con varios POST a la vez.
COLA_DE_ESCUCHA = 128

# --- Zona horaria (decisión 5 de specs/README.md) -----------------------------
ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

# --- Rutas --------------------------------------------------------------------
CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_DATOS = os.environ.get("MICAFE_DATOS") or os.path.join(CARPETA_PROYECTO, "datos")
ARCHIVO_PREFERENCIAS = os.path.join(CARPETA_DATOS, "preferencias.json")
ARCHIVO_GUSTOS = os.path.join(CARPETA_DATOS, "gustos.json")
ARCHIVO_INDICADORES = os.path.join(CARPETA_DATOS, "indicadores.json")
ARCHIVO_ACCIONES = os.path.join(CARPETA_DATOS, "acciones.json")
CARPETA_RESUMENES = os.path.join(CARPETA_DATOS, "resumenes")  # AAAA-MM-DD.json

CARPETA_ESTATICA = os.path.join(CARPETA_PROYECTO, "micafe", "web", "estatico")
ARCHIVO_INDEX = os.path.join(CARPETA_ESTATICA, "index.html")
# Lista cerrada de lo que se sirve como estático: ruta del pedido -> (nombre de archivo, Content-Type).
ARCHIVOS_ESTATICOS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/estilos.css": ("estilos.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
CARPETA_SKILLS = os.path.join(CARPETA_PROYECTO, ".claude", "skills")
ARCHIVO_SKILL_RESUMEN = os.path.join(CARPETA_SKILLS, "resumen-diario", "SKILL.md")
ARCHIVO_SKILL_CORRECTOR = os.path.join(CARPETA_SKILLS, "corrector", "SKILL.md")
ARCHIVO_SKILL_PREGUNTAS = os.path.join(CARPETA_SKILLS, "preguntas-nota", "SKILL.md")

# --- Timeouts (segundos) ------------------------------------------------------
# Valores distintos para "consultar una fuente HTTP", conservados como estaban (spec 19, pregunta 4):
TIMEOUT_CLAUDE = 5 * 60  # `claude -p`: decisión 13 de specs/README.md
TIMEOUT_CHEQUEO_CLAUDE = 10  # `claude --version`: solo comprueba que el comando existe y arranca (spec 29)
TIMEOUT_INDICADORES = 10  # DolarApi, ArgentinaDatos, BCRA
TIMEOUT_NOTICIAS = 10  # RSS de los medios
HILOS_FEEDS = 6  # feeds que se leen a la vez (spec 43)
TIMEOUT_ACCIONES = 15  # data912 y Rava

# User-Agent: dos variantes, como estaban.
AGENTE = "MiCafe/1.0"
AGENTE_RAVA = "MiCafe/1.0 uso personal"

# Horas entre consultas: ArgentinaDatos admite una cada 3 horas por serie; data912 usa lo mismo.
# Regla de CLAUDE.md ("ArgentinaDatos pide máximo una consulta cada 3 horas"): por eso hay copia local en datos/.
HORAS_ENTRE_CONSULTAS = 3

# --- URLs y nombres de las fuentes --------------------------------------------
URL_DOLARAPI = "https://dolarapi.com/v1/dolares"
URL_RIESGO_PAIS = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo"
# BCRA v4.0 (la v3 está dada de baja). Ids verificados contra el catálogo real el 24/11/2026 (docs/investigacion.md).
# ArgentinaDatos (rutas verificadas el 24/11/2026, docs/investigacion.md): series con filas {fecha, valor}.
URL_INFLACION = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
URL_INFLACION_INTERANUAL = "https://api.argentinadatos.com/v1/finanzas/indices/inflacionInteranual"
URL_UVA = "https://api.argentinadatos.com/v1/finanzas/indices/uva"
URL_BCRA_VARIABLE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}?limit=10"  # solo el último tramo
BCRA_IDS = {
    "reservas": 1,        # Reservas internacionales (millones de USD)
    "badlar": 7,          # Tasa de interés BADLAR de bancos privados (% nominal anual)
    "tamar": 44,          # Tasa de interés TAMAR de bancos privados (% nominal anual)
    "plazo_fijo_30": 1207,  # Tasa de interés de depósitos a plazo fijo de 30 días (% nominal anual)
    "a3500": 5,           # Tipo de cambio Mayorista de Referencia (Com. A 3500, pesos por dólar)
}
URL_DATA912 = "https://data912.com/historical/stocks/"
URL_RAVA = "https://www.rava.com/cotizaciones/historico/merval/"
URL_RAVA_ROBOTS = "https://www.rava.com/robots.txt"

FUENTE_DOLARAPI = "DolarApi https://dolarapi.com"
FUENTE_ARGENTINADATOS = "ArgentinaDatos https://argentinadatos.com"
FUENTE_BCRA = "BCRA, Estadísticas Monetarias v4.0 https://www.bcra.gob.ar"
FUENTE_DATA912 = "data912 https://data912.com, cierre en pesos"
FUENTE_RAVA = "Rava https://www.rava.com (cierre del índice)"
FUENTE_RESPALDO_DATA912 = "data912 https://data912.com"

# Nombre vigente del índice: MSCI Merval desde 19/10/2026 (no "S&P Merval").
# Regla de CLAUDE.md ("Nombres vigentes"); la hace cumplir corrector.RE_SP_MERVAL.
NOMBRE_MERVAL = "MSCI Merval"
MAX_CONSULTAS_RAVA = 8  # ayer + hasta 7 días de retroceso (decisión 5 de las preguntas resueltas)

# Orden fijo de las secciones del resumen.
# Temas elegibles = secciones de noticias, en el orden en que se muestran (única definición).
# Spec 44: "Policiales" quedó afuera porque solo Infobae tiene un feed válido (hace falta 2 medios por tema).
TEMAS = ["Política", "Economía", "Internacional", "Sociedad", "Deportes", "Salud y Ciencia",
         "Espectáculos y Cultura", "Tecnología"]
SECCIONES = TEMAS

# Spec 45: subtemas de Deportes (solo de Deportes), en orden fijo. Palabras clave: conjunto inicial
# a validar con datos reales; se comparan sin tildes ni mayúsculas, como palabra o frase completa.
# "Otros" es lo que no encaja en ninguno y no lleva palabras clave.
SUBTEMAS = {
    "Fútbol argentino": ["Boca", "River", "Racing", "Independiente", "San Lorenzo", "Vélez", "Estudiantes",
                         "Huracán", "Talleres", "Newell's", "Rosario Central", "Lanús", "Banfield",
                         "Argentinos Juniors", "Gimnasia", "Liga Profesional", "Copa Argentina", "AFA",
                         "Primera Nacional", "Torneo Clausura", "Torneo Apertura", "Scaloni"],
    "Fútbol internacional": ["Champions League", "Premier League", "LaLiga", "Real Madrid", "Barcelona",
                             "Manchester", "Liverpool", "Bayern", "Juventus", "Inter Miami", "Mundial",
                             "Eliminatorias", "Copa Libertadores", "Copa Sudamericana", "Mbappé", "Haaland",
                             "Messi", "Serie A", "Bundesliga"],
    "Tenis": ["tenis", "Wimbledon", "Roland Garros", "US Open", "Abierto de Australia", "ATP", "WTA",
              "Copa Davis", "Djokovic", "Alcaraz", "Sinner", "Nadal", "Federer", "Báez", "Cerúndolo",
              "Etcheverry", "Masters 1000"],
    "Básquet": ["básquet", "NBA", "Liga Nacional", "Euroliga", "Campazzo", "Deck", "FIBA", "Ginóbili"],
    "Automovilismo": ["Fórmula 1", "F1", "MotoGP", "Colapinto", "Verstappen", "Hamilton", "Ferrari", "McLaren",
                      "Rally", "Dakar", "TC2000", "Turismo Carretera", "Fórmula 2", "Gran Premio"],
    "Otros": [],
}
# Sin archivo de preferencias solo vienen tildados los cinco temas originales (spec 44).
TEMAS_POR_DEFECTO = ["Política", "Economía", "Internacional", "Deportes", "Tecnología"]
# Spec 44: reclasificación de feeds marcados con `reclasificar_por_categoria`: categoría
# normalizada (minúsculas, sin tildes) -> tema. Hoy ningún feed la usa (el RSS general de
# elDiarioAR no trae <category>); queda lista para cuando haya uno.
CATEGORIAS_A_TEMA = {
    "politica": "Política", "economia": "Economía", "internacional": "Internacional", "mundo": "Internacional",
    "sociedad": "Sociedad", "deportes": "Deportes", "salud": "Salud y Ciencia", "ciencia": "Salud y Ciencia",
    "cultura": "Espectáculos y Cultura", "espectaculos": "Espectáculos y Cultura", "tecnologia": "Tecnología",
}

# RSS: todas las URLs en un solo lugar. Probados el 11/11/2026 y, los de la spec 34 (Perfil,
# iProfesional, El Cronista y más de Ámbito), el 18/11/2026; los de la spec 44 (Sociedad, Salud y
# Ciencia, Espectáculos y Cultura y el de Política de elDiarioAR), el 24/11/2026. Ámbito "últimas noticias", la
# portada de Página/12 y el feed general de Infobae no se usan porque no tienen sección asignada.
# TN no se usa: su feed trae la fecha en ISO 8601 (no RFC 822) y no tiene feeds por sección.
# Infobae internacional y tecnología responden bien pero hoy no traen ítems.
FUENTES_RSS = [
    {"medio": "Infobae", "seccion": "Política",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/politica/"},
    {"medio": "elDiarioAR", "seccion": "Política",
     "url": "https://www.eldiarioar.com/rss/politica/"},
    {"medio": "Página/12", "seccion": "Política",
     "url": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/el-pais/notas/"},
    {"medio": "Infobae", "seccion": "Economía",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/"},
    {"medio": "Ámbito", "seccion": "Economía",
     "url": "https://www.ambito.com/rss/economia.xml"},
    {"medio": "Ámbito", "seccion": "Economía",
     "url": "https://www.ambito.com/rss/pages/finanzas.xml"},
    {"medio": "Página/12", "seccion": "Economía",
     "url": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/economia/notas/"},
    {"medio": "Página/12", "seccion": "Internacional",
     "url": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/el-mundo/notas/"},
    {"medio": "Infobae", "seccion": "Internacional",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/internacional/"},
    # Spec 45: el feed "ultimas-noticias" de Olé trae solo 10 ítems de las últimas horas (nunca
    # de ayer); se reemplazó por los feeds por deporte. automovilismo da 404 y se descartó.
    {"medio": "Olé", "seccion": "Deportes", "subtema": "Fútbol argentino",
     "url": "https://www.ole.com.ar/rss/futbol-primera/"},
    {"medio": "Olé", "seccion": "Deportes", "subtema": "Fútbol internacional",
     "url": "https://www.ole.com.ar/rss/futbol-internacional/"},
    {"medio": "Olé", "seccion": "Deportes", "subtema": "Tenis",
     "url": "https://www.ole.com.ar/rss/tenis/"},
    {"medio": "Olé", "seccion": "Deportes", "subtema": "Básquet",
     "url": "https://www.ole.com.ar/rss/basquet/"},
    {"medio": "Infobae", "seccion": "Deportes",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/deportes/"},
    {"medio": "Infobae", "seccion": "Tecnología",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/tecnologia/"},
    {"medio": "iProfesional", "seccion": "Política",
     "url": "https://www.iprofesional.com/rss/politica"},
    {"medio": "El Cronista", "seccion": "Economía",
     "url": "https://www.cronista.com/arc/outboundfeeds/rss/category/economia-politica/?outputType=xml"},
    {"medio": "Ámbito", "seccion": "Política",
     "url": "https://www.ambito.com/rss/politica.xml"},
    {"medio": "Ámbito", "seccion": "Internacional",
     "url": "https://www.ambito.com/rss/mundo.xml"},
    {"medio": "Perfil", "seccion": "Internacional",
     "url": "https://www.perfil.com/feed/internacional"},
    {"medio": "Ámbito", "seccion": "Deportes",
     "url": "https://www.ambito.com/rss/pages/deportes.xml"},
    {"medio": "Perfil", "seccion": "Deportes",
     "url": "https://www.perfil.com/feed/deportes"},
    {"medio": "Ámbito", "seccion": "Tecnología",
     "url": "https://www.ambito.com/rss/tecnologia.xml"},
    {"medio": "Perfil", "seccion": "Tecnología",
     "url": "https://www.perfil.com/feed/tecnologia"},
    {"medio": "iProfesional", "seccion": "Tecnología",
     "url": "https://www.iprofesional.com/rss/tecnologia"},
    # Spec 44 (probados el 24/11/2026).
    {"medio": "Infobae", "seccion": "Sociedad",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/sociedad/"},
    {"medio": "elDiarioAR", "seccion": "Sociedad",
     "url": "https://www.eldiarioar.com/rss/sociedad/"},
    {"medio": "Página/12", "seccion": "Sociedad",
     "url": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/sociedad/notas/"},
    {"medio": "Infobae", "seccion": "Salud y Ciencia",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/salud/"},
    {"medio": "iProfesional", "seccion": "Salud y Ciencia",
     "url": "https://www.iprofesional.com/rss/salud"},
    {"medio": "Infobae", "seccion": "Espectáculos y Cultura",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/teleshow/"},
    {"medio": "Infobae", "seccion": "Espectáculos y Cultura",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/cultura/"},
    {"medio": "Página/12", "seccion": "Espectáculos y Cultura",
     "url": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/cultura-y-espectaculos/notas/"},
    {"medio": "Ámbito", "seccion": "Espectáculos y Cultura",
     "url": "https://www.ambito.com/rss/pages/espectaculos.xml"},
]

# --- Topes --------------------------------------------------------------------
# Reglas de CLAUDE.md: máximo 3 notas por medio, largo objetivo 550-650 palabras y
# deduplicar contra los últimos 3 resúmenes.
TOPE_POR_MEDIO = 3
TOPE_POR_MEDIO_LUNES = 5  # decisión 14: la ventana de los lunes (viernes a domingo) es más larga
# Candidatas de la lista "Noticias de ayer" (spec 33): el cupo se cuenta por (medio, seccion)
# para que un medio presente en varias secciones no deje vacias a las otras. No es la regla
# del resumen: ahi sigue valiendo TOPE_POR_MEDIO sobre el resumen completo (lo hace cumplir el corrector).
# Spec 39: se sube a 8 (13 los lunes, en proporción a 3 y 5) para que la selección por puntaje
# tenga de dónde elegir; después seleccion.elegir_candidatas recorta a MAXIMO_CANDIDATAS_PARA_CLAUDE.
CANDIDATAS_POR_MEDIO_Y_SECCION = 8
CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES = 13
MAXIMO_CANDIDATAS_PARA_CLAUDE = 40  # spec 39: notas que le llegan a Claude
MINIMO_PALABRAS = 550  # solo se exige si el plan de secciones quedó completo (spec 40)
MAXIMO_BAJADA = 300  # caracteres de la bajada (description del RSS) de cada candidata (spec 38)
MAXIMO_CATEGORIAS = 5  # categorías (category del RSS) por candidata (spec 38)
MAXIMO_PEDIDO_USUARIO = 500  # caracteres del pedido de noticias (spec 35); mismo valor que la pregunta de la caja
MAXIMO_PALABRAS = 650
REINTENTOS_CORRECTOR = 2  # decisión 8

# Etapas de armar el resumen, en el orden real del código (spec 30). Los textos son fijos:
# nunca llevan contenido de notas ni de resúmenes.
ETAPAS_RESUMEN = [
    ("claude", "Comprobando Claude"),
    ("noticias", "Trayendo noticias"),
    ("indicadores", "Trayendo indicadores"),
    ("redactando", "Redactando con Claude"),
    ("corrigiendo", "Corrigiendo"),
    ("guardando", "Guardando"),
]
CANTIDAD_PREVIOS = 3  # decisión 9: dedupe contra los últimos 3 resúmenes

# --- Perfil de gustos (spec 41) -----------------------------------------------
VIDA_MEDIA_GUSTOS_DIAS = 14  # un voto pesa la mitad cada 14 días
MULTIPLICADOR_VOTO_TEMA = 3  # un voto a un tema vale el triple que uno a una nota
PESO_TERMINO_TITULO = 0.5  # peso de cada término del título de una nota votada
TOPE_PERFIL = 5  # todo puntaje del perfil queda entre -TOPE_PERFIL y +TOPE_PERFIL
# Cómo el perfil entra en la selección. El aporte total a una nota se acota a +-MAXIMO_PUNTAJE_PERFIL,
# que sumado a la frescura (2) queda por debajo del peso mínimo de un término del pedido (3):
# el pedido siempre le gana al perfil.
PESO_PERFIL_MEDIO = 0.18  # puntos por cada punto del perfil del medio de la nota
PESO_PERFIL_TERMINO = 0.09  # puntos por cada punto del perfil de cada término del título
MAXIMO_PUNTAJE_PERFIL = 0.9
PESO_PERFIL_SECCION = 0.2  # el peso de una sección del plan es 1 + esto * su puntaje de perfil (mínimo PESO_MINIMO_SECCION)
PESO_MINIMO_SECCION = 0.1
UMBRAL_PRIORIDAD = 0.5  # puntaje (en valor absoluto) desde el cual algo cuenta como prioridad aprendida
MAXIMO_PRIORIDADES = 8  # prioridades que se muestran y que van al prompt


# --- Selección por puntaje (spec 39) ------------------------------------------
# Pesos del puntaje de cada candidata. Un término del pedido que aparece en el título suma
# más que en la bajada, y en la bajada más que en las categorías. Todo el pedido pesa más que
# la frescura (que suma entre 0 y `frescura`), así una nota que encaja con el pedido queda
# primera aunque sea más vieja. Se pueden ajustar midiendo con datos reales.
PESOS_PUNTAJE = {"titulo": 10.0, "bajada": 5.0, "subtema": 5.0, "categoria": 3.0, "frescura": 2.0}

# Palabras que no cuentan como término del pedido (ya normalizadas: minúsculas y sin tildes).
PALABRAS_VACIAS_PEDIDO = frozenset({
    "a", "al", "algo", "con", "de", "del", "el", "en", "es", "esta", "este", "hoy", "la", "las", "lo", "los",
    "mas", "me", "mi", "muy", "noticia", "noticias", "nota", "notas", "para", "por", "que", "quiero",
    "quisiera", "sobre", "solo", "su", "sus", "un", "una", "uno", "unas", "unos", "y", "o", "ver", "dame",
    "necesito", "tema", "temas", "info", "informacion", "novedades", "todo", "todas", "todos",
})

# Término del pedido -> términos equivalentes. Las claves se normalizan al comparar
# (minúsculas, sin tildes). Conjunto inicial: se amplía a mano.
SINONIMOS_TEMAS = {
    "fútbol argentino": ["liga profesional", "AFA", "Boca", "River", "Racing", "Independiente",
                         "San Lorenzo", "Copa Argentina", "Primera División", "Selección"],
    "fútbol internacional": ["Champions League", "Premier League", "LaLiga", "Real Madrid", "Barcelona",
                             "Copa Libertadores", "Mundial"],
    "tenis": ["ATP", "WTA", "Copa Davis", "Wimbledon", "Roland Garros", "US Open"],
    "básquet": ["NBA", "Liga Nacional", "Euroliga", "FIBA"],
    "automovilismo": ["Fórmula 1", "MotoGP", "Colapinto", "TC2000", "Turismo Carretera"],
    "fútbol": ["liga profesional", "AFA", "Boca", "River", "Racing", "Independiente", "San Lorenzo",
               "Copa Libertadores", "Champions League", "Mundial"],
    "política": ["Gobierno", "Congreso", "Senado", "Diputados", "Milei", "gabinete", "elecciones", "Casa Rosada"],
    "economía": ["dólar", "inflación", "BCRA", "Banco Central", "tasas", "salarios", "FMI", "déficit", "exportaciones"],
    "tecnología": ["inteligencia artificial", "IA", "celulares", "software", "internet", "ciberseguridad", "startups"],
    "internacional": ["Estados Unidos", "Trump", "Brasil", "China", "Europa", "ONU", "guerra", "Rusia"],
    "deportes": ["fútbol", "tenis", "básquet", "rugby", "Fórmula 1", "Selección", "Juegos Olímpicos"],
    "sociedad": ["educación", "universidades", "transporte", "clima", "género", "jubilados", "vivienda", "salud pública"],
    "policiales": ["policía", "detenido", "robo", "homicidio", "juicio", "fiscalía", "Justicia", "narcotráfico"],
    "salud": ["hospital", "vacunas", "enfermedad", "medicamentos", "obras sociales", "dengue", "nutrición"],
    "ciencia": ["investigación", "CONICET", "astronomía", "espacio", "NASA", "descubrimiento", "clima"],
    "espectáculos": ["cine", "series", "televisión", "famosos", "música", "streaming", "teatro", "Netflix"],
    "cultura": ["libros", "literatura", "museo", "arte", "teatro", "exposición", "festival", "cine"],
}

# Spec 42: claves de SINONIMOS_TEMAS que no se llaman como un tema pero lo nombran (para avisar si está destildado).
TEMA_DE_CLAVE_SINONIMO = {
    "fútbol": "Deportes", "fútbol argentino": "Deportes", "fútbol internacional": "Deportes",
    "tenis": "Deportes", "básquet": "Deportes", "automovilismo": "Deportes",
    "salud": "Salud y Ciencia", "ciencia": "Salud y Ciencia",
    "espectáculos": "Espectáculos y Cultura", "cultura": "Espectáculos y Cultura",
}


# --- Preferencias v2 (spec 49) ------------------------------------------------
PRIORIDADES_TEMA = ["alta", "normal", "baja"]  # orden fijo; "normal" es la de los temas sin elegir
MAXIMO_PALABRAS_PREFERENCIA = 20  # palabras por lista (seguir y evitar por separado)
MAXIMO_CARACTERES_PALABRA = 40
# Cómo entran las preferencias en el puntaje de cada nota. La suma de sus aportes se acota a
# +-MAXIMO_PUNTAJE_PREFERENCIAS: más que el tope del perfil (0,9) y menos que el peso mínimo de un
# término del pedido (3). Además las notas que encajan con el pedido van siempre antes (ver seleccion).
PESO_MEDIO_PREFERIDO = 0.6
PESO_PALABRA_SEGUIR = 0.5
PESO_PALABRA_EVITAR = 0.8  # se resta
PESO_SUBTEMA_ELEGIDO = 0.5
PESO_SUBTEMA_NO_ELEGIDO = 0.5  # se resta
MAXIMO_PUNTAJE_PREFERENCIAS = 1.5
# Multiplicador del peso de una sección en el plan según la prioridad del tema.
PESO_PRIORIDAD_ALTA = 1.5
PESO_PRIORIDAD_BAJA = 0.5

# --- Plan de secciones (spec 40) ----------------------------------------------
NOTAS_OBJETIVO = 9  # notas del resumen que el plan trata de repartir entre las secciones activas
MAXIMO_POR_SECCION = 9  # tope de notas de una sola sección; igual a NOTAS_OBJETIVO para que, con un solo tema tildado, ese tema lleve todas
MINIMO_POR_SECCION_ACTIVA = 1  # toda sección tildada y con candidatas lleva al menos esta cantidad
PESO_POR_NOTA_PEDIDA = 0.5  # cuánto suma al peso de una sección cada nota [pedido] que tiene entre las candidatas
