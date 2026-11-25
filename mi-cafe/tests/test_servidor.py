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
        self.assertEqual(datos["preferencias"]["version"], 2)
        self.assertEqual([t for t, v in datos["preferencias"]["temas"].items() if v["activo"]],
                         ["Política", "Economía", "Internacional", "Deportes", "Tecnología"])
        self.assertIn("opciones", datos)
        self.assertIsNone(datos["aviso"])

    def test_las_opciones_traen_las_secciones_de_config(self):
        from micafe import config
        datos = self.json("GET", "/api/preferencias")[1]
        self.assertEqual(datos["opciones"]["secciones"], config.TEMAS)
        self.assertIn("Internacional", datos["opciones"]["secciones"])

    def test_las_opciones_v2_estan_completas(self):
        from micafe import config
        from micafe.textos import normalizar_texto
        opciones = self.json("GET", "/api/preferencias")[1]["opciones"]
        self.assertEqual(set(opciones), {"indicadores", "secciones", "subtemas", "medios", "prioridades",
                                         "maximo_palabras", "maximo_caracteres"})
        self.assertEqual(opciones["subtemas"], list(config.SUBTEMAS))
        self.assertEqual(opciones["prioridades"], ["alta", "normal", "baja"])
        self.assertEqual(opciones["maximo_palabras"], config.MAXIMO_PALABRAS_PREFERENCIA)
        self.assertEqual(opciones["maximo_caracteres"], config.MAXIMO_CARACTERES_PALABRA)
        self.assertEqual(opciones["medios"], sorted(set(opciones["medios"]), key=normalizar_texto))
        self.assertIn("Perfil", opciones["medios"])
        self.assertIn("dolar_otros", opciones["indicadores"])

    def test_post_v2_guarda_y_devuelve_v2_y_los_errores_son_400_en_espanol(self):
        cuerpo = {"version": 2, "temas": {"Deportes": {"activo": True, "prioridad": "alta"}}, "subtemas": ["Tenis"],
                  "medios": {"preferidos": [], "excluidos": ["Perfil"]}, "palabras": {"seguir": ["Boca"], "evitar": []},
                  "indicadores": ["dolar"]}
        codigo, datos = self.json("POST", "/api/preferencias", cuerpo)
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["preferencias"]["medios"]["excluidos"], ["Perfil"])
        self.assertEqual(self.json("GET", "/api/preferencias")[1]["preferencias"], datos["preferencias"])
        malo = {**cuerpo, "temas": {"Deportes": {"activo": True, "prioridad": "altísima"}}}
        codigo, datos = self.json("POST", "/api/preferencias", malo)
        self.assertEqual(codigo, 400)
        self.assertFalse(datos["ok"])
        self.assertIn("altísima", datos["errores"][0])
        self.assertEqual(self.json("GET", "/api/preferencias")[1]["preferencias"]["temas"]["Deportes"]["prioridad"], "alta")

    def test_lo_que_arma_la_pantalla_se_guarda_y_los_topes_se_rechazan(self):
        """Spec 50: la pantalla reenvía el v2 entero del GET con cambios, usando solo `opciones`."""
        datos = self.json("GET", "/api/preferencias")[1]
        opciones, prefs = datos["opciones"], datos["preferencias"]
        self.assertEqual(list(prefs["temas"]), opciones["secciones"])
        self.assertTrue(set(prefs["indicadores"]) <= set(opciones["indicadores"]))
        medio = opciones["medios"][0]
        prefs["temas"][opciones["secciones"][0]] = {"activo": False, "prioridad": opciones["prioridades"][2]}
        prefs["medios"]["excluidos"] = [medio]
        prefs["palabras"]["seguir"] = ["<b>Boca</b>"]
        codigo, respuesta = self.json("POST", "/api/preferencias", prefs)
        self.assertEqual(codigo, 200)
        guardadas = self.json("GET", "/api/preferencias")[1]["preferencias"]
        self.assertEqual(guardadas, respuesta["preferencias"])
        self.assertEqual(guardadas["medios"]["excluidos"], [medio])
        self.assertEqual(guardadas["palabras"]["seguir"], ["<b>Boca</b>"])
        # Los topes que le llegan a la pantalla son los que el servidor hace valer.
        largo = {**guardadas, "palabras": {"seguir": ["a" * (opciones["maximo_caracteres"] + 1)], "evitar": []}}
        self.assertEqual(self.json("POST", "/api/preferencias", largo)[0], 400)
        muchas = {**guardadas, "palabras": {"seguir": [f"p{i}" for i in range(opciones["maximo_palabras"] + 1)], "evitar": []}}
        self.assertEqual(self.json("POST", "/api/preferencias", muchas)[0], 400)
        sin_temas = {**guardadas, "temas": {t: {"activo": False, "prioridad": "normal"} for t in opciones["secciones"]}}
        codigo, respuesta = self.json("POST", "/api/preferencias", sin_temas)
        self.assertEqual((codigo, respuesta["errores"]), (400, ["Elegí al menos un tema."]))

    def test_post_valido_guarda_en_la_carpeta_temporal(self):
        codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": ["dolar"], "temas": ["Deportes"]})
        self.assertEqual(codigo, 200)
        self.assertTrue(datos["ok"])
        self.assertTrue(os.path.exists(os.path.join(self.datos, "preferencias.json")))
        prefs = self.json("GET", "/api/preferencias")[1]["preferencias"]
        self.assertEqual([t for t, v in prefs["temas"].items() if v["activo"]], ["Deportes"])

    def test_json_invalido_es_400_en_espanol(self):
        codigo, datos = self.json("POST", "/api/preferencias", "esto no es json")
        self.assertEqual(codigo, 400)
        self.assertEqual(datos, {"ok": False, "errores": ["El cuerpo no es JSON válido."]})

    def test_json_invalido_es_400_tambien_en_gustos_y_preguntas(self):
        for ruta in ("/api/gustos", "/api/preguntas"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.json("POST", ruta, "{roto")[0], 400)

    def test_temas_vacios_es_400_con_el_mensaje_en_espanol(self):
        codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": ["dolar"], "temas": []})
        self.assertEqual(codigo, 400)
        self.assertEqual(datos["errores"], ["Elegí al menos un tema."])
        self.assertFalse(os.path.exists(os.path.join(self.datos, "preferencias.json")))

    def test_valor_desconocido_es_400_con_el_motivo(self):
        codigo, datos = self.json("POST", "/api/preferencias", {"indicadores": ["bitcoin"], "temas": []})
        self.assertEqual(codigo, 400)
        self.assertFalse(datos["ok"])
        self.assertTrue(datos["errores"])


class PreferenciasConcurrentes(ServidorDePrueba):
    """Spec 28: tildar varias casillas seguidas hace varios POST a la vez."""

    def test_veinte_post_concurrentes_dan_200_y_dejan_un_archivo_valido(self):
        combinaciones = [{"indicadores": ["dolar", "riesgo_pais", "acciones"][: n % 4],
                          "temas": ["Política", "Economía", "Internacional", "Deportes", "Tecnología"][: 1 + n % 5]}
                         for n in range(20)]
        # 8 hilos a la vez: la cola de escucha del servidor (COLA_DE_ESCUCHA) los aguanta.
        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = list(pool.map(lambda c: self.json("POST", "/api/preferencias", c), combinaciones))
        self.assertEqual([codigo for codigo, _ in resultados], [200] * 20)
        with open(os.path.join(self.datos, "preferencias.json"), encoding="utf-8") as archivo:
            final = json.load(archivo)
        self.assertEqual(final["version"], 2)
        self.assertIn({"indicadores": final["indicadores"],
                       "temas": [t for t, v in final["temas"].items() if v["activo"]]}, combinaciones)
        self.assertEqual(os.listdir(self.datos), ["preferencias.json"])  # sin .tmp sueltos

    def test_todo_subconjunto_se_guarda_y_deja_andar_indicadores_y_noticias(self):
        def subconjuntos(lista, minimo=0):
            return [list(c) for n in range(minimo, len(lista) + 1) for c in itertools.combinations(lista, n)]

        base = {"indicadores": [], "generado_en": "x", "avisos": []}
        extra = {"indicadores": [], "avisos": []}
        salida = {"notas": [], "fallas": [], "ventana": {}, "tope_por_medio": 3, "generado_en": "x"}
        with mock.patch.object(servicio.indicadores, "obtener", return_value=base), \
                mock.patch.object(servicio.acciones, "obtener_todo", return_value=extra), \
                mock.patch.object(servicio.noticias, "obtener", return_value=salida):
            for indicadores in subconjuntos(["dolar", "riesgo_pais", "acciones"]):
                for temas in subconjuntos(["Política", "Economía", "Internacional", "Deportes", "Tecnología"], 1):
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

    def test_get_expone_plan_pedido_y_pedido_sin_notas(self):
        plan = {"secciones": [{"seccion": "Deportes", "cupo": 2, "pedidas": 0, "motivos": []}], "completo": False}
        self.guardar_resumen_en_disco({**RESUMEN, "pedido": "tecnología", "pedido_sin_notas": True, "plan": plan})
        resumen = self.json("GET", "/api/resumen")[1]["resumen"]
        self.assertEqual((resumen["pedido"], resumen["pedido_sin_notas"], resumen["plan"]), ("tecnología", True, plan))

    def test_pedido_sin_notas_avisa_que_temas_destildados_nombra(self):
        self.json("POST", "/api/preferencias", {"indicadores": [], "temas": ["Política", "Deportes"]})
        self.guardar_resumen_en_disco({**RESUMEN, "pedido": "Tecnología y economía", "pedido_sin_notas": True})
        resumen = self.json("GET", "/api/resumen")[1]["resumen"]
        self.assertEqual(resumen["temas_destildados_pedido"], ["Economía", "Tecnología"])

    def test_resumen_viejo_sin_esos_campos_responde_200(self):
        self.guardar_resumen_en_disco(RESUMEN)
        codigo, datos = self.json("GET", "/api/resumen")
        self.assertEqual(codigo, 200)
        for campo in ("plan", "pedido", "pedido_sin_notas", "temas_destildados_pedido"):
            self.assertNotIn(campo, datos["resumen"])

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
        self.json("POST", "/api/preferencias", {"indicadores": ["dolar"], "temas": ["Deportes"]})
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


class NoticiasOrdenadas(ServidorDePrueba):
    def nota(self, titulo, fecha, medio="Medio A", seccion="Deportes"):
        return {"titulo": titulo, "medio": medio, "seccion": seccion, "fecha": fecha, "link": f"https://x.test/{titulo}"}

    def pedir_noticias(self, notas):
        salida = {"notas": notas, "fallas": [], "ventana": {}, "tope_por_medio": 3, "generado_en": "x"}
        with mock.patch.object(servicio.noticias, "obtener", return_value=salida):
            return self.json("GET", "/api/noticias")

    def test_sin_pedido_va_por_frescura_y_trae_motivos(self):
        vieja = self.nota("vieja", "17/11/2026 08:00")
        nueva = self.nota("nueva", "17/11/2026 22:00")
        codigo, datos = self.pedir_noticias([vieja, nueva])
        self.assertEqual(codigo, 200)
        self.assertEqual([n["titulo"] for n in datos["notas"]], ["nueva", "vieja"])
        self.assertEqual(datos["notas"][0]["motivos"], ["frescura"])
        self.assertEqual(datos["notas"][1]["motivos"], [])
        self.assertNotIn("puntaje", datos["notas"][0])

    def test_con_el_pedido_de_hoy_las_que_encajan_van_primero(self):
        hoy = servicio.datetime.now(servicio.ZONA).date().isoformat()
        self.guardar_resumen_en_disco({**RESUMEN, "fecha": hoy, "pedido": "river"})
        otra = self.nota("tenis en Australia", "17/11/2026 22:00")
        river = self.nota("River goleó", "17/11/2026 08:00")
        datos = self.pedir_noticias([otra, river])[1]
        self.assertEqual(datos["notas"][0]["titulo"], "River goleó")
        self.assertTrue(any(m.startswith("pedido:") for m in datos["notas"][0]["motivos"]))

    def test_subtema_solo_en_las_notas_de_deportes(self):
        dep = {**self.nota("partido", "17/11/2026 22:00"), "subtema": "Tenis"}
        pol = self.nota("ley", "17/11/2026 21:00", seccion="Política")
        notas = {n["titulo"]: n for n in self.pedir_noticias([dep, pol])[1]["notas"]}
        self.assertEqual(notas["partido"]["subtema"], "Tenis")
        self.assertNotIn("subtema", notas["ley"])

    def test_el_pedido_de_otro_dia_no_cuenta(self):
        self.guardar_resumen_en_disco({**RESUMEN, "fecha": "2020-01-01", "pedido": "river"})
        datos = self.pedir_noticias([self.nota("tenis", "17/11/2026 22:00"), self.nota("River goleó", "17/11/2026 08:00")])[1]
        self.assertEqual(datos["notas"][0]["titulo"], "tenis")

    def test_un_medio_con_votos_positivos_muestra_medio_que_te_gusta(self):
        for i in range(4):
            self.json("POST", "/api/gustos", {"tipo": "nota", "clave": f"https://x.test/v{i}", "voto": "me_gusta",
                                             "titulo": f"voto {i}", "medio": "Medio B", "seccion": "Deportes"})
        datos = self.pedir_noticias([self.nota("a", "17/11/2026 10:00", medio="Medio A"),
                                     self.nota("b", "17/11/2026 10:00", medio="Medio B")])[1]
        self.assertEqual(datos["notas"][0]["medio"], "Medio B")
        self.assertIn("medio que te gusta", datos["notas"][0]["motivos"])


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


class Perfil(ServidorDePrueba):
    def votar(self, **voto):
        self.assertEqual(self.json("POST", "/api/gustos", voto)[0], 200)

    def test_get_sin_votos_responde_200_con_listas_vacias(self):
        codigo, datos = self.json("GET", "/api/perfil")
        self.assertEqual(codigo, 200)
        self.assertEqual(datos, {"ok": True, "prioridades": [], "reiniciado_en": None, "votos_que_cuentan": 0})

    def test_get_con_votos_trae_prioridades_en_espanol_sin_numeros(self):
        for _ in range(2):
            self.votar(tipo="tema", clave="Economía", voto="me_gusta")
        datos = self.json("GET", "/api/perfil")[1]
        self.assertEqual(datos["votos_que_cuentan"], 1)
        self.assertEqual(datos["prioridades"][0]["etiqueta"], "Te interesa más Economía")
        self.assertEqual(datos["prioridades"][0]["signo"], 1)

    def test_reiniciar_sin_confirmacion_es_400_en_espanol(self):
        for cuerpo in (None, {}, {"confirmar": False}, {"confirmar": "true"}, [True]):
            codigo, datos = self.json("POST", "/api/perfil/reiniciar", cuerpo)
            self.assertEqual(codigo, 400)
            self.assertEqual(datos["errores"], ["Confirmá el reinicio para ignorar lo aprendido."])

    def test_reiniciar_con_cuerpo_mal_formado_es_400(self):
        self.assertEqual(self.pedir("POST", "/api/perfil/reiniciar", "{roto")[0], 400)

    def test_reiniciar_deja_el_perfil_vacio_y_conserva_los_votos(self):
        self.votar(tipo="tema", clave="Economía", voto="me_gusta")
        codigo, datos = self.json("POST", "/api/perfil/reiniciar", {"confirmar": True})
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["prioridades"], [])
        self.assertEqual(datos["votos_que_cuentan"], 0)
        self.assertTrue(datos["reiniciado_en"])
        with open(os.path.join(self.datos, "gustos.json"), encoding="utf-8") as archivo:
            guardado = json.load(archivo)
        self.assertEqual(len(guardado["votos"]), 1)
        self.assertEqual(guardado["reiniciado_en"], datos["reiniciado_en"])
        self.assertEqual(self.json("GET", "/api/perfil")[1]["prioridades"], [])


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
