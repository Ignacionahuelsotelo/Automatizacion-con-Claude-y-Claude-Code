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
URL_RESERVAS = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/1"  # BCRA v4.0 (la v3 está dada de baja)
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
SECCIONES = ["Política", "Economía", "Internacional", "Deportes", "Tecnología"]

# RSS: todas las URLs en un solo lugar. Probados el 11/11/2026 y, los de la spec 34 (Perfil,
# iProfesional, El Cronista y más de Ámbito), el 18/11/2026. Ámbito "últimas noticias", la
# portada de Página/12 y el feed general de Infobae no se usan porque no tienen sección asignada.
# TN no se usa: su feed trae la fecha en ISO 8601 (no RFC 822) y no tiene feeds por sección.
# Infobae internacional y tecnología responden bien pero hoy no traen ítems.
FUENTES_RSS = [
    {"medio": "Infobae", "seccion": "Política",
     "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/politica/"},
    {"medio": "elDiarioAR", "seccion": "Política",
     "url": "https://www.eldiarioar.com/rss/"},
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
    {"medio": "Olé", "seccion": "Deportes",
     "url": "https://www.ole.com.ar/rss/ultimas-noticias/"},
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
]

# --- Topes --------------------------------------------------------------------
# Reglas de CLAUDE.md: máximo 3 notas por medio, largo objetivo 550-650 palabras y
# deduplicar contra los últimos 3 resúmenes.
TOPE_POR_MEDIO = 3
TOPE_POR_MEDIO_LUNES = 5  # decisión 14: la ventana de los lunes (viernes a domingo) es más larga
# Candidatas de la lista "Noticias de ayer" (spec 33): el cupo se cuenta por (medio, seccion)
# para que un medio presente en varias secciones no deje vacias a las otras. No es la regla
# del resumen: ahi sigue valiendo TOPE_POR_MEDIO sobre el resumen completo (lo hace cumplir el corrector).
CANDIDATAS_POR_MEDIO_Y_SECCION = 3
CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES = 5
MINIMO_PALABRAS = 550
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
CANTIDAD_GUSTOS_PARA_CLAUDE = 30  # decisión 10: últimos 30 votos
