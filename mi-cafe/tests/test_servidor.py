"""Tests de servidor.py: se levanta en un puerto libre (0) con las fuentes simuladas y carpetas temporales."""

import http.client
import itertools
import json
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

from micafe.dominio import servicio
from micafe.dominio.progreso import Progreso
from micafe.errores import ErrorResumen
from micafe.web import servidor
from tests import utiles

RESUMEN = {"fecha": "2026-11-17", "generado_en": "17/11/2026 08:00", "indicadores": [],
           "texto": "Lo más importante de hoy: algo.", "chequeo": {"aprobado": True}}


class ServidorDePrueba(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)  # el servidor imprime cada pedido y las trazas en consola
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.datos = carpeta.name
        self.resumenes = os.path.join(self.datos, "resumenes")

        # Todo lo que el servidor lee o escribe va a la carpeta temporal, nunca a datos/.
        for nombre, valor in {
            "ARCHIVO_PREFERENCIAS": os.path.join(self.datos, "preferencias.json"),
            "ARCHIVO_INDICADORES": os.path.join(self.datos, "indicadores.json"),
            "ARCHIVO_GUSTOS": os.path.join(self.datos, "gustos.json"),
            "ARCHIVO_ACCIONES": os.path.join(self.datos, "acciones.json"),
            "CARPETA_RESUMENES": self.resumenes,
        }.items():
            parche = mock.patch.object(servicio, nombre, valor)
            parche.start()
            self.addCleanup(parche.stop)

        self.httpd = servidor.ServidorMiCafe(("127.0.0.1", 0), servidor.Manejador)
        self.puerto = self.httpd.server_address[1]
        hilo = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        hilo.start()
        self.addCleanup(hilo.join, 5)
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def pedir(self, metodo, ruta, cuerpo=None):
        """Devuelve (codigo, cabeceras, bytes)."""
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=5)
        try:
            if isinstance(cuerpo, (dict, list)):
                cuerpo = json.dumps(cuerpo)
            conexion.request(metodo, ruta, body=cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo)
            respuesta = conexion.getresponse()
            return respuesta.status, respuesta, respuesta.read()
        finally:
            conexion.close()

    def json(self, metodo, ruta, cuerpo=None):
        codigo, _, datos = self.pedir(metodo, ruta, cuerpo)
        return codigo, json.loads(datos.decode("utf-8"))

    def guardar_resumen_en_disco(self, registro=RESUMEN):
        os.makedirs(self.resumenes, exist_ok=True)
        with open(os.path.join(self.resumenes, f"{registro['fecha']}.json"), "w", encoding="utf-8") as archivo:
            json.dump(registro, archivo)


class Rutas(ServidorDePrueba):
    def test_la_raiz_sirve_el_index(self):
        codigo, respuesta, cuerpo = self.pedir("GET", "/")
        self.assertEqual(codigo, 200)
        self.assertIn("text/html", respuesta.getheader("Content-Type"))
        self.assertIn(b"<html", cuerpo.lower())

    def test_estaticos_con_su_tipo_y_charset(self):
        for ruta, tipo in (("/", "text/html"), ("/estilos.css", "text/css"), ("/app.js", "text/javascript")):
            codigo, respuesta, cuerpo = self.pedir("GET", ruta)
            self.assertEqual(codigo, 200, ruta)
            self.assertEqual(respuesta.getheader("Content-Type"), tipo + "; charset=utf-8")
            self.assertTrue(cuerpo)

    def test_rutas_fuera_de_la_lista_o_con_escapes_son_404(self):
        for ruta in ("/../servidor.py", "/%2e%2e/config.py", "/app.js/..", "/index.html", "/micafe/config.py",
                     "//etc/passwd", "/estilos.css/"):
            codigo, _, cuerpo = self.pedir("GET", ruta)
            self.assertEqual(codigo, 404, ruta)
            self.assertNotIn(b"import ", cuerpo, ruta)

    def test_ruta_inexistente_es_404_en_get_y_en_post(self):
        self.assertEqual(self.pedir("GET", "/no-existe")[0], 404)
        self.assertEqual(self.pedir("POST", "/no-existe", {})[0], 404)

    def test_metodo_no_soportado_es_501_en_espanol(self):
        codigo, _, cuerpo = self.pedir("PUT", "/api/preferencias", "{}")
        self.assertEqual(codigo, 501)
        self.assertIn("El servidor no atiende ese tipo de pedido.", cuerpo.decode("utf-8"))


class Preferencias(ServidorDePrueba):
    def test_get_sin_archivo_devuelve_las_de_por_defecto_y_las_opciones(self):
        codigo, datos = self.json("GET", "/api/preferencias")
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["preferencias"]["temas"], ["Política", "Economía", "Deportes", "Tecnología"])
        self.assertIn("opciones", datos)
        self.assertIsNone(datos["aviso"])

    def test_post_valido_guarda_en_la_carpeta_temporal(self):
        codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": ["dolar"], "temas": ["Deportes"]})
        self.assertEqual(codigo, 200)
        self.assertTrue(datos["ok"])
        self.assertTrue(os.path.exists(os.path.join(self.datos, "preferencias.json")))
        self.assertEqual(self.json("GET", "/api/preferencias")[1]["preferencias"]["temas"], ["Deportes"])

    def test_json_invalido_es_400_en_espanol(self):
        codigo, datos = self.json("POST", "/api/preferencias", "esto no es json")
        self.assertEqual(codigo, 400)
        self.assertEqual(datos, {"ok": False, "errores": ["El cuerpo no es JSON válido."]})

    def test_json_invalido_es_400_tambien_en_gustos_y_preguntas(self):
        for ruta in ("/api/gustos", "/api/preguntas"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.json("POST", ruta, "{roto")[0], 400)

    def test_valor_desconocido_es_400_con_el_motivo(self):
        codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": ["bitcoin"], "temas": []})
        self.assertEqual(codigo, 400)
        self.assertFalse(datos["ok"])
        self.assertTrue(datos["errores"])


class PreferenciasConcurrentes(ServidorDePrueba):
    """Spec 28: tildar varias casillas seguidas hace varios POST a la vez."""

    def test_veinte_post_concurrentes_dan_200_y_dejan_un_archivo_valido(self):
        combinaciones = [{"indicadores": ["dolar", "riesgo_pais", "acciones"][: n % 4],
                          "temas": ["Política", "Economía", "Deportes", "Tecnología"][: (n + 1) % 5]}
                         for n in range(20)]
        # 8 hilos a la vez: la cola de escucha del servidor (COLA_DE_ESCUCHA) los aguanta.
        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = list(pool.map(lambda c: self.json("POST", "/api/preferencias", c), combinaciones))
        self.assertEqual([codigo for codigo, _ in resultados], [200] * 20)
        with open(os.path.join(self.datos, "preferencias.json"), encoding="utf-8") as archivo:
            final = json.load(archivo)
        self.assertIn(final, combinaciones)
        self.assertEqual(os.listdir(self.datos), ["preferencias.json"])  # sin .tmp sueltos

    def test_todo_subconjunto_se_guarda_y_deja_andar_indicadores_y_noticias(self):
        def subconjuntos(lista):
            return [list(c) for n in range(len(lista) + 1) for c in itertools.combinations(lista, n)]

        base = {"indicadores": [], "generado_en": "x", "avisos": []}
        extra = {"indicadores": [], "avisos": []}
        salida = {"notas": [], "fallas": [], "ventana": {}, "tope_por_medio": 3, "generado_en": "x"}
        with mock.patch.object(servicio.indicadores, "obtener", return_value=base), \
                mock.patch.object(servicio.acciones, "obtener_todo", return_value=extra), \
                mock.patch.object(servicio.noticias, "obtener", return_value=salida):
            for indicadores in subconjuntos(["dolar", "riesgo_pais", "acciones"]):
                for temas in subconjuntos(["Política", "Economía", "Deportes", "Tecnología"]):
                    with self.subTest(indicadores=indicadores, temas=temas):
                        cuerpo = {"indicadores": indicadores, "temas": temas}
                        self.assertEqual(self.json("POST", "/api/preferencias", cuerpo)[0], 200)
                        self.assertEqual(self.json("GET", "/api/indicadores")[0], 200)
                        self.assertEqual(self.json("GET", "/api/noticias")[0], 200)


class ErrorInesperado(ServidorDePrueba):
    def test_error_no_previsto_en_get_es_500_con_aviso_en_espanol_y_el_servidor_sigue(self):
        with mock.patch.object(servicio.preferencias, "leer", side_effect=RuntimeError("se rompió")):
            codigo, datos = self.json("GET", "/api/preferencias")
        self.assertEqual(codigo, 500)
        self.assertFalse(datos["ok"])
        self.assertEqual(datos["errores"], ["Pasó un error inesperado en el servidor. Mirá la consola para más detalle."])
        self.assertEqual(self.pedir("GET", "/")[0], 200)  # sigue andando

    def test_error_no_previsto_en_post_es_500(self):
        with mock.patch.object(servicio.gustos, "guardar", side_effect=RuntimeError("se rompió")):
            codigo, datos = self.json("POST", "/api/gustos", {"tipo": "tema", "clave": "Deportes", "voto": "me_gusta"})
        self.assertEqual(codigo, 500)
        self.assertIn("inesperado", datos["errores"][0])

    def test_error_de_escritura_es_500_con_aviso_sobre_la_carpeta_datos(self):
        with mock.patch.object(servicio.preferencias, "guardar", side_effect=PermissionError("sin permiso")):
            codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": [], "temas": []})
        self.assertEqual(codigo, 500)
        self.assertIn("carpeta datos/", datos["errores"][0])


class ResumenGuardado(ServidorDePrueba):
    def test_get_sin_resumen_devuelve_none(self):
        codigo, datos = self.json("GET", "/api/resumen")
        self.assertEqual((codigo, datos), (200, {"ok": True, "resumen": None}))

    def test_get_con_resumen_devuelve_el_mas_reciente(self):
        self.guardar_resumen_en_disco({**RESUMEN, "fecha": "2026-11-16", "texto": "el viejo"})
        self.guardar_resumen_en_disco(RESUMEN)
        codigo, datos = self.json("GET", "/api/resumen")
        self.assertEqual(codigo, 200)
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["resumen"]["fecha"], "2026-11-17")
        self.assertEqual(datos["resumen"]["texto"], RESUMEN["texto"])

    def test_get_suma_notas_votables_sin_tocar_el_archivo_y_el_voto_se_acepta(self):
        texto = ("Lo más importante de hoy: algo.\n\nPolítica\nTítulo uno\nCuerpo.\nPor qué importa: sí.\n"
                 "Infobae, 17/11/2026\nhttps://infobae.test/1")
        self.guardar_resumen_en_disco({**RESUMEN, "texto": texto})
        ruta = os.path.join(self.resumenes, "2026-11-17.json")
        with open(ruta, "rb") as archivo:
            antes = archivo.read()
        codigo, datos = self.json("GET", "/api/resumen")
        self.assertEqual(codigo, 200)
        nota = datos["resumen"]["notas"][0]
        self.assertEqual(nota, {"titulo": "Título uno", "medio": "Infobae", "seccion": "Política",
                                "link": "https://infobae.test/1"})
        with open(ruta, "rb") as archivo:
            self.assertEqual(archivo.read(), antes)
        voto = {"tipo": "nota", "clave": nota["link"], "voto": "me_gusta",
                "titulo": nota["titulo"], "medio": nota["medio"], "seccion": nota["seccion"]}
        self.assertEqual(self.json("POST", "/api/gustos", voto)[0], 200)
        with open(os.path.join(self.datos, "gustos.json"), encoding="utf-8") as archivo:
            guardado = json.load(archivo)
        self.assertIn("Título uno", json.dumps(guardado, ensure_ascii=False))

    def test_get_saltea_un_resumen_roto(self):
        self.guardar_resumen_en_disco({**RESUMEN, "fecha": "2026-11-16"})
        with open(os.path.join(self.resumenes, "2026-11-17.json"), "w", encoding="utf-8") as archivo:
            archivo.write("{roto")
        self.assertEqual(self.json("GET", "/api/resumen")[1]["resumen"]["fecha"], "2026-11-16")


class Indicadores(ServidorDePrueba):
    def test_get_con_las_fuentes_simuladas(self):
        base = {"indicadores": [{"clave": "reservas", "valor": None}], "generado_en": "x", "avisos": []}
        extra = {"indicadores": [{"clave": "accion_mmsci", "valor": None}], "avisos": ["aviso de acciones"]}
        with mock.patch.object(servicio.indicadores, "obtener", return_value=base) as dolares, \
                mock.patch.object(servicio.acciones, "obtener_todo", return_value=extra) as acciones:
            codigo, datos = self.json("GET", "/api/indicadores")
        self.assertEqual(codigo, 200)
        self.assertEqual([i["clave"] for i in datos["indicadores"]], ["reservas", "accion_mmsci"])
        self.assertEqual(datos["avisos"], ["aviso de acciones"])
        dolares.assert_called_once()
        acciones.assert_called_once()

    def test_sin_acciones_elegidas_no_se_consulta_acciones(self):
        self.json("POST", "/api/preferencias", {"indicadores": ["dolar"], "temas": []})
        base = {"indicadores": [], "generado_en": "x", "avisos": []}
        with mock.patch.object(servicio.indicadores, "obtener", return_value=base), \
                mock.patch.object(servicio.acciones, "obtener_todo") as acciones:
            self.json("GET", "/api/indicadores")
        acciones.assert_not_called()


class EstadoDeClaude(ServidorDePrueba):
    def test_get_responde_200_aunque_claude_no_este(self):
        for estado in ({"disponible": True, "estado": "ok", "mensaje": "Claude: listo"},
                       {"disponible": False, "estado": "no_instalado", "mensaje": "No se encontró el comando `claude`."}):
            with mock.patch.object(servicio.resumen, "comprobar_claude", return_value=estado):
                codigo, datos = self.json("GET", "/api/claude")
            self.assertEqual(codigo, 200)
            self.assertEqual(datos, estado)

    def test_sin_claude_en_el_path_el_mensaje_es_el_de_no_instalado(self):
        with mock.patch("micafe.dominio.resumen.shutil.which", return_value=None):
            codigo, datos = self.json("GET", "/api/claude")
        self.assertEqual(codigo, 200)
        self.assertFalse(datos["disponible"])
        self.assertTrue(datos["mensaje"].startswith("No se encontró el comando `claude`"))


class Noticias(ServidorDePrueba):
    def test_get_con_las_fuentes_simuladas_usa_los_temas_elegidos(self):
        self.json("POST", "/api/preferencias", {"indicadores": [], "temas": ["Deportes"]})
        salida = {"notas": [], "fallas": [], "ventana": {}, "tope_por_medio": 3, "generado_en": "x"}
        with mock.patch.object(servicio.noticias, "obtener", return_value=salida) as obtener:
            codigo, datos = self.json("GET", "/api/noticias")
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["tope_por_medio"], 3)
        obtener.assert_called_once_with(["Deportes"])


class LogYErrores(ServidorDePrueba):
    def test_error_inesperado_va_al_log_con_traza_y_no_a_la_pagina(self):
        with mock.patch.object(servicio.preferencias, "leer", side_effect=RuntimeError("secreto técnico")):
            with self.assertLogs("micafe.web.servidor", level="ERROR") as registro:
                codigo, _, cuerpo = self.pedir("GET", "/api/preferencias")
        self.assertEqual(codigo, 500)
        self.assertIn("secreto técnico", "\n".join(registro.output))
        texto = cuerpo.decode("utf-8")
        for prohibido in ("Traceback", "secreto técnico", ".py", "RuntimeError"):
            self.assertNotIn(prohibido, texto)

    def test_error_previsto_queda_en_el_log_y_responde_su_mensaje(self):
        error = ErrorResumen("Claude tardó mucho.", codigo=504)
        with mock.patch.object(servicio.caja, "responder", side_effect=error):
            with self.assertLogs("micafe.web.servidor", level="WARNING") as registro:
                codigo, datos = self.json("POST", "/api/preguntas", {})
        self.assertEqual((codigo, datos), (504, {"ok": False, "errores": ["Claude tardó mucho."]}))
        self.assertIn("Claude tardó mucho.", registro.output[0])

    def test_error_de_fuente_queda_en_el_log_y_la_pagina_sigue(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("sin red")):
            with self.assertLogs("micafe.fuentes", level="WARNING") as registro:
                codigo, datos = self.json("GET", "/api/indicadores")
        self.assertEqual(codigo, 200)
        self.assertTrue(registro.output)
        self.assertNotIn("Traceback", json.dumps(datos))
        self.assertNotIn(".py", json.dumps(datos))


if __name__ == "__main__":
    unittest.main()


class ResumenEnSegundoPlano(ServidorDePrueba):
    def setUp(self):
        super().setUp()
        for objeto, nombre, kwargs in [
            (servicio, "progreso_resumen", {"new": Progreso()}),
            (servicio.resumen, "comprobar_claude", {"return_value": {"disponible": True, "estado": "ok", "mensaje": "ok"}}),
        ]:
            parche = mock.patch.object(objeto, nombre, **kwargs)
            parche.start()
            self.addCleanup(parche.stop)

    def esperar(self, estado_final, plazo=5):
        limite = time.time() + plazo
        while time.time() < limite:
            codigo, datos = self.json("GET", "/api/resumen/estado")
            if datos["estado"] == estado_final:
                return datos
            time.sleep(0.01)
        self.fail(f"nunca llegó a {estado_final}")

    def test_estado_libre_al_arrancar(self):
        codigo, datos = self.json("GET", "/api/resumen/estado")
        self.assertEqual((codigo, datos["estado"]), (200, "libre"))

    def test_post_responde_202_enseguida_aunque_el_armado_tarde_y_el_segundo_da_409(self):
        liberar = threading.Event()
        registro = dict(RESUMEN, indicadores=[])

        def lento(avisar=None, pedido=None):
            avisar("redactando", 1)
            liberar.wait(5)
            return {"resumen": registro, "avisos": {"indicadores": [], "noticias": []}}

        with mock.patch.object(servicio, "preparar_resumen", side_effect=lento):
            inicio = time.time()
            codigo, datos = self.json("POST", "/api/resumen")
            self.assertLess(time.time() - inicio, 1)
            self.assertEqual(codigo, 202)
            self.assertTrue(datos["ok"])
            self.assertEqual(datos["estado"]["estado"], "en_curso")

            codigo, datos = self.json("POST", "/api/resumen")
            self.assertEqual(codigo, 409)
            self.assertEqual(datos, {"ok": False, "errores": ["Ya se está preparando un resumen. Esperá a que termine."]})

            en_curso = self.json("GET", "/api/resumen/estado")[1]
            self.assertEqual(en_curso["etapa"], "redactando")
            self.assertEqual(en_curso["intento"], 1)
            liberar.set()
            listo = self.esperar("listo")
        self.assertEqual(listo["resultado"]["resumen"]["fecha"], "2026-11-17")

    def test_fallo_llega_como_fallo_con_errores_y_avisos(self):
        error = ErrorResumen("Claude falló.", extras={"avisos": {"noticias": ["x"]}})
        with mock.patch.object(servicio, "preparar_resumen", side_effect=error):
            self.assertEqual(self.json("POST", "/api/resumen")[0], 202)
            fallo = self.esperar("fallo")
        self.assertEqual(fallo["errores"], ["Claude falló."])
        self.assertEqual(fallo["avisos"], {"noticias": ["x"]})


class PedidoEnElPost(ResumenEnSegundoPlano):
    def con_preparar_falso(self):
        recibido = {}

        def falso(avisar=None, pedido=None):
            recibido["pedido"] = pedido
            return {"resumen": dict(RESUMEN, indicadores=[]), "avisos": {"indicadores": [], "noticias": []}}

        parche = mock.patch.object(servicio, "preparar_resumen", side_effect=falso)
        parche.start()
        self.addCleanup(parche.stop)
        return recibido

    def test_sin_cuerpo_con_objeto_vacio_o_pedido_vacio_da_202_sin_pedido(self):
        recibido = self.con_preparar_falso()
        for cuerpo in (None, {}, {"pedido": ""}):
            self.assertEqual(self.json("POST", "/api/resumen", cuerpo)[0], 202, cuerpo)
            self.esperar("listo")
            self.assertIsNone(recibido["pedido"])

    def test_con_pedido_da_202_y_lo_normaliza(self):
        recibido = self.con_preparar_falso()
        codigo, datos = self.json("POST", "/api/resumen", {"pedido": "más\neconomía"})
        self.assertEqual(codigo, 202)
        self.esperar("listo")
        self.assertEqual(recibido["pedido"], "más economía")
        self.assertNotIn("economía", json.dumps(self.json("GET", "/api/resumen/estado")[1]["etapas"]))

    def test_pedido_invalido_da_400_en_espanol_y_no_inicia_nada(self):
        recibido = self.con_preparar_falso()
        casos = (({"pedido": "a" * 501}, "El pedido es muy largo (máximo 500 caracteres)."),
                 ({"pedido": 7}, "El pedido tiene que ser un texto."))
        for cuerpo, mensaje in casos:
            self.assertEqual(self.json("POST", "/api/resumen", cuerpo), (400, {"ok": False, "errores": [mensaje]}))
        self.assertEqual(recibido, {})
        self.assertEqual(self.json("GET", "/api/resumen/estado")[1]["estado"], "libre")

    def test_get_devuelve_el_pedido_guardado_tal_cual(self):
        self.guardar_resumen_en_disco({**RESUMEN, "pedido": "más economía"})
        self.assertEqual(self.json("GET", "/api/resumen")[1]["resumen"]["pedido"], "más economía")
