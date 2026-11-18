"""Servidor local de Mi Café.

Solo usa la librería estándar de Python (sin pip install).
Sirve index.html en la raíz, las preferencias en /api/preferencias (GET y POST)
los indicadores en /api/indicadores (GET), las noticias de ayer en /api/noticias (GET),
el último resumen guardado en /api/resumen (GET, sin llamar a Claude). El POST de
/api/resumen empieza a armar el de hoy en un hilo y responde 202 enseguida (409 si ya
hay uno en curso); el avance y el resultado se consultan en /api/resumen/estado (GET)
y el resumen se guarda en datos/resumenes/ (spec 30). Los 👍/👎 se leen
en /api/gustos (GET) y se guardan en /api/gustos (POST). La pregunta sobre una nota
va a /api/preguntas (POST), que responde solo con lo que dice esa nota (spec 10).
El resto de las rutas responde 404.
Atiende cada pedido en su propio hilo: mientras Claude redacta el resumen, la
página sigue pidiendo lo demás. Si un pedido falla de forma no prevista, el
servidor registra el error en la consola, responde un aviso en español y sigue
andando (spec 12).

Uso:
    python3 servidor.py
    y abrir http://localhost:8000
"""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from micafe.config import ARCHIVOS_ESTATICOS, CARPETA_DATOS, CARPETA_ESTATICA, COLA_DE_ESCUCHA, HOST, PUERTO
from micafe.dominio import servicio
from micafe.errores import ErrorMiCafe
from micafe.logs import configurar as configurar_log

logger = logging.getLogger(__name__)

# Tope del cuerpo de un pedido: lo que se manda (preferencias, un voto, una pregunta) es mucho menor.
LIMITE_CUERPO = 1024 * 1024
MENSAJE_JSON_INVALIDO = "El cuerpo no es JSON válido."


class ServidorMiCafe(ThreadingHTTPServer):
    """Servidor con un hilo por pedido y una cola de escucha más grande que la de por defecto (5)."""

    request_queue_size = COLA_DE_ESCUCHA


class CuerpoInvalido(ErrorMiCafe):
    """El cuerpo del pedido no es JSON o es demasiado grande."""

    codigo_por_defecto = 400


# Cada ruta devuelve (código, datos JSON). `peticion` es el Manejador, que aporta `cuerpo_json()`.

RespuestaRuta = tuple[int, dict[str, Any]]

def _ruta_preferencias_get(peticion: Manejador) -> RespuestaRuta:
    prefs, aviso = servicio.leer_preferencias()
    return 200, {"preferencias": prefs, "opciones": servicio.opciones_de_preferencias(), "aviso": aviso}


def _ruta_preferencias_post(peticion: Manejador) -> RespuestaRuta:
    prefs, errores = servicio.guardar_preferencias(peticion.cuerpo_json())
    return (400, {"ok": False, "errores": errores}) if errores else (200, {"ok": True, "preferencias": prefs})


def _ruta_indicadores(peticion: Manejador) -> RespuestaRuta:
    return 200, servicio.obtener_indicadores()


def _ruta_noticias(peticion: Manejador) -> RespuestaRuta:
    return 200, servicio.obtener_noticias()


def _ruta_claude(peticion: Manejador) -> RespuestaRuta:
    return 200, servicio.estado_de_claude()


def _ruta_resumen_get(peticion: Manejador) -> RespuestaRuta:
    return 200, {"ok": True, "resumen": servicio.ultimo_resumen()}


def _ruta_resumen_post(peticion: Manejador) -> RespuestaRuta:
    estado, errores = servicio.iniciar_resumen(peticion.cuerpo_json_opcional())
    return (400, {"ok": False, "errores": errores}) if errores else (202, {"ok": True, "estado": estado})


def _ruta_resumen_estado(peticion: Manejador) -> RespuestaRuta:
    return 200, servicio.estado_del_resumen()


def _ruta_gustos_get(peticion: Manejador) -> RespuestaRuta:
    votos, aviso = servicio.leer_votos()
    return 200, {"ok": True, "votos": votos, "aviso": aviso}


def _ruta_gustos_post(peticion: Manejador) -> RespuestaRuta:
    votos, errores = servicio.guardar_voto(peticion.cuerpo_json())
    return (400, {"ok": False, "errores": errores}) if errores else (200, {"ok": True, "votos": votos})


def _ruta_preguntas(peticion: Manejador) -> RespuestaRuta:
    return 200, {"ok": True, **servicio.responder_pregunta(peticion.cuerpo_json())}


RUTAS_JSON: dict[tuple[str, str], Callable[[Manejador], RespuestaRuta]] = {
    ("GET", "/api/preferencias"): _ruta_preferencias_get,
    ("POST", "/api/preferencias"): _ruta_preferencias_post,
    ("GET", "/api/indicadores"): _ruta_indicadores,
    ("GET", "/api/noticias"): _ruta_noticias,
    ("GET", "/api/claude"): _ruta_claude,
    ("GET", "/api/resumen"): _ruta_resumen_get,
    ("POST", "/api/resumen"): _ruta_resumen_post,
    ("GET", "/api/resumen/estado"): _ruta_resumen_estado,
    ("GET", "/api/gustos"): _ruta_gustos_get,
    ("POST", "/api/gustos"): _ruta_gustos_post,
    ("POST", "/api/preguntas"): _ruta_preguntas,
}


class Manejador(BaseHTTPRequestHandler):
    """Atiende cada pedido HTTP: sirve los archivos estáticos de la página y despacha las rutas JSON de RUTAS_JSON."""

    def do_GET(self) -> None:
        """Atiende un GET."""
        self._atender()

    def do_POST(self) -> None:
        """Atiende un POST."""
        self._atender()

    def _atender(self) -> None:
        """Único lugar donde se despacha la ruta y se manejan los errores (previstos e inesperados)."""
        try:
            if self.command == "GET" and self.path in ARCHIVOS_ESTATICOS:  # lista cerrada, sin rutas libres
                nombre, tipo = ARCHIVOS_ESTATICOS[self.path]
                self._responder_archivo(os.path.join(CARPETA_ESTATICA, nombre), tipo)
                return
            ruta = RUTAS_JSON.get((self.command, self.path))
            if ruta is None:
                self._responder_texto(404, "No encontrado")
                return
            codigo, datos = ruta(self)
            self._responder_json(codigo, datos)
        except ErrorMiCafe as error:
            self._responder_error(error)
        except Exception:  # último recurso: nada que se escape tira el servidor; la traza va al log
            self._error_inesperado()

    def cuerpo_json(self) -> Any:
        """Lee el cuerpo del pedido como JSON. Levanta CuerpoInvalido (400) si no lo es."""
        try:
            largo = int(self.headers.get("Content-Length", 0))
            if largo < 0:
                raise ValueError("largo negativo")
            if largo > LIMITE_CUERPO:
                raise CuerpoInvalido("El cuerpo es demasiado grande.", codigo=413)
            return json.loads(self.rfile.read(largo).decode("utf-8"))
        except ValueError as error:
            raise CuerpoInvalido(MENSAJE_JSON_INVALIDO) from error

    def cuerpo_json_opcional(self) -> Any:
        """Como cuerpo_json, pero un cuerpo vacío (sin Content-Length o en 0) devuelve None."""
        if int(self.headers.get("Content-Length", 0) or 0) == 0:
            return None
        return self.cuerpo_json()

    def send_error(self, codigo: int, mensaje: str | None = None, explicacion: str | None = None) -> None:
        """Errores del protocolo (método no soportado, pedido mal armado) en español y sin texto técnico."""
        textos = {
            400: "El pedido no se entiende.",
            501: "El servidor no atiende ese tipo de pedido.",
        }
        cuerpo = textos.get(codigo, "Pasó un error en el servidor.").encode("utf-8")
        self.close_connection = True
        self.send_response(codigo)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _responder_error(self, error: ErrorMiCafe) -> None:
        """Un error previsto: al log como aviso y a la página solo su mensaje en español."""
        logger.warning("Aviso: %s %s respondió %s: %s", self.command, self.path, error.codigo, error.mensaje)
        try:
            self._responder_json(error.codigo, {"ok": False, "errores": [error.mensaje], **error.extras})
        except OSError:
            pass  # la conexión ya se cortó: no hay a quién responder

    def _error_inesperado(self) -> None:
        """Un error no previsto: va a la consola con su traza y la página recibe un aviso en español."""
        logger.exception("Aviso: error inesperado al atender %s %s.", self.command, self.path)
        try:
            self._responder_json(500, {
                "ok": False,
                "errores": ["Pasó un error inesperado en el servidor. Mirá la consola para más detalle."],
            })
        except OSError:
            pass  # la conexión ya se cortó: no hay a quién responder

    def _responder_archivo(self, ruta: str, tipo: str) -> None:
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
        self._responder(200, tipo, contenido)

    def _responder_texto(self, codigo: int, texto: str) -> None:
        self._responder(codigo, "text/plain; charset=utf-8", texto.encode("utf-8"))

    def _responder_json(self, codigo: int, datos: Any) -> None:
        self._responder(codigo, "application/json; charset=utf-8", json.dumps(datos, ensure_ascii=False).encode("utf-8"))

    def _responder(self, codigo: int, tipo: str, contenido: bytes) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)


def main() -> None:
    """Arranca el servidor en 127.0.0.1:8000 (host y puerto fijos) hasta Ctrl+C."""
    configurar_log()
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    estado = servicio.estado_de_claude()
    if not estado["disponible"]:
        logger.warning("Aviso: Claude no está disponible (%s). El servidor arranca igual.", estado["estado"])
    servidor = ServidorMiCafe((HOST, PUERTO), Manejador)
    logger.info(f"Mi Café escuchando en http://localhost:{PUERTO} (Ctrl+C para cortar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
