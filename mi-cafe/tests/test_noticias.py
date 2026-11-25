"""Tests de noticias.py: ventana de ayer, lunes, notas sin fecha, tope por medio y feeds caídos."""

import threading
import time
import unittest
from datetime import timedelta
from urllib.error import HTTPError, URLError

from micafe.fuentes import noticias
from tests import utiles

MARTES_A_LA_MANANA = "Tue, 17 Nov 2026 09:00:00 -0300"


def _fuente(medio="Medio A", seccion="Política", url="https://a.test/rss"):
    return {"medio": medio, "seccion": seccion, "url": url}


def _lector(feeds):
    """Reemplazo de noticias.leer_feed: {url: bytes o excepción}. Anota las URLs pedidas."""
    pedidas = []

    def leer(url):
        pedidas.append(url)
        respuesta = feeds[url]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    leer.pedidas = pedidas
    return leer


class Ventana(unittest.TestCase):
    def test_de_martes_a_viernes_es_solo_ayer(self):
        desde, hasta, tope = noticias.ventana(utiles.MIERCOLES)
        self.assertEqual((desde.day, hasta.day), (17, 18))
        self.assertEqual(tope, 3)
        self.assertEqual(desde.tzinfo, utiles.ZONA)

    def test_el_lunes_va_de_viernes_a_domingo(self):
        desde, hasta, tope = noticias.ventana(utiles.LUNES)
        self.assertEqual((desde.day, desde.weekday()), (13, 4))  # viernes 13
        self.assertEqual((hasta.day, hasta.weekday()), (16, 0))  # hasta el lunes 00:00
        self.assertEqual(tope, 5)

    def test_usa_la_fecha_de_buenos_aires_aunque_ahora_venga_en_otra_zona(self):
        # 01:00 UTC del miércoles todavía es martes a la noche en Buenos Aires.
        from datetime import datetime, timezone
        ahora = datetime(2026, 11, 18, 1, 0, tzinfo=timezone.utc)
        desde, hasta, _ = noticias.ventana(ahora)
        self.assertEqual((desde.day, hasta.day), (16, 17))  # ayer fue el lunes 16: hoy es martes 17


class LecturaDelFeed(unittest.TestCase):
    def test_descarta_notas_sin_fecha_con_fecha_rota_o_sin_link(self):
        notas = noticias.notas_del_feed(utiles.fixture("rss.xml").encode("utf-8"), _fuente())
        self.assertEqual([n["link"] for n in notas],
                         ["https://medio.test/ayer-1", "https://medio.test/ayer-2", "https://medio.test/hoy"])

    def test_documento_que_no_es_rss_levanta_error(self):
        with self.assertRaises(ValueError):
            noticias.notas_del_feed(b"<html><body>hola</body></html>", _fuente())

    def test_xml_roto_levanta_error(self):
        with self.assertRaises(SyntaxError):
            noticias.notas_del_feed(b"<rss><channel>", _fuente())

    def test_fecha_sin_zona_horaria_se_descarta(self):
        self.assertIsNone(noticias.fecha_de("17 Nov 2026 10:00:00"))


class ReclasificacionPorCategoria(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        self.fixture = utiles.fixture("rss_categorias.xml").encode("utf-8")

    def test_funcion_pura_reasigna_y_descarta_lo_desconocido(self):
        notas = noticias.notas_del_feed(self.fixture, _fuente(seccion="Política"))
        resultado = {n["titulo"]: n["seccion"] for n in noticias.reclasificar_por_categoria(notas)}
        self.assertEqual(resultado, {"Nota de sociedad": "Sociedad", "Nota de política": "Política",
                                     "Nota de ciencia": "Salud y Ciencia"})
        self.assertEqual(notas[0]["seccion"], "Política")  # no modifica las originales

    def test_feed_marcado_se_reclasifica_y_lo_desconocido_no_aparece_en_ninguna_seccion(self):
        fuente = dict(_fuente(), reclasificar_por_categoria=True)
        datos = noticias.obtener(["Política", "Sociedad", "Salud y Ciencia"], ahora=utiles.MIERCOLES,
                                 fuentes=[fuente], leer=_lector({"https://a.test/rss": self.fixture}))
        self.assertEqual({n["titulo"]: n["seccion"] for n in datos["notas"]},
                         {"Nota de sociedad": "Sociedad", "Nota de política": "Política",
                          "Nota de ciencia": "Salud y Ciencia"})

    def test_solo_quedan_las_secciones_tildadas(self):
        fuente = dict(_fuente(), reclasificar_por_categoria=True)
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES,
                                 fuentes=[fuente], leer=_lector({"https://a.test/rss": self.fixture}))
        self.assertEqual([n["titulo"] for n in datos["notas"]], ["Nota de política"])

    def test_feed_sin_la_marca_no_se_reclasifica(self):
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES,
                                 fuentes=[_fuente()], leer=_lector({"https://a.test/rss": self.fixture}))
        self.assertEqual(len(datos["notas"]), 5)
        self.assertEqual({n["seccion"] for n in datos["notas"]}, {"Política"})


class BajadaYCategorias(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        notas = noticias.notas_del_feed(utiles.fixture("rss_bajada.xml").encode("utf-8"), _fuente())
        self.por_link = {n["link"].rsplit("/", 1)[1]: n for n in notas}

    def test_html_y_entidades_quedan_en_texto_plano(self):
        self.assertEqual(self.por_link["html"]["bajada"], "Hola & chau")
        self.assertEqual(self.por_link["entidades"]["bajada"], "\u201cGran triunfo\u201d & fiesta")

    def test_descarta_script_y_style_y_colapsa_espacios(self):
        self.assertEqual(self.por_link["script"]["bajada"], "Texto con saltos")

    def test_sin_description_o_vacia_la_nota_entra_con_bajada_vacia(self):
        for clave in ("nada", "vacia"):
            self.assertEqual(self.por_link[clave]["bajada"], "")
            self.assertEqual(self.por_link[clave]["categorias"], [])

    def test_bajada_larga_se_recorta_en_limite_de_palabra_con_puntos_suspensivos(self):
        bajada = noticias.limpiar_bajada("<p>" + "palabra " * 100 + "</p>")
        self.assertLessEqual(len(bajada), 300)
        self.assertTrue(bajada.endswith("palabra\u2026"))
        self.assertEqual(noticias.limpiar_bajada("corta"), "corta")
        self.assertEqual(len(noticias.limpiar_bajada("x" * 400)), 300)  # sin espacios: corta igual

    def test_categorias_sin_vacias_ni_repetidas(self):
        self.assertEqual(self.por_link["html"]["categorias"], ["F\u00fatbol", "futbol", "River"])

    def test_categorias_con_tope_de_5(self):
        self.assertEqual(self.por_link["cats"]["categorias"], ["a", "b", "c", "d", "e"])


class ObtenerNoticias(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)

    def _obtener(self, feeds, fuentes, temas=("Política", "Economía"), ahora=utiles.MIERCOLES):
        leer = _lector(feeds)
        datos = noticias.obtener(list(temas), ahora=ahora, fuentes=fuentes, leer=leer)
        return datos, leer

    def test_solo_entran_las_notas_de_ayer_en_buenos_aires(self):
        items = [
            ("Entra a la mañana", "https://a.test/1", "Tue, 17 Nov 2026 00:00:00 -0300"),
            ("Entra a la noche", "https://a.test/2", "Tue, 17 Nov 2026 23:59:59 -0300"),
            ("Entra por UTC", "https://a.test/3", "Wed, 18 Nov 2026 02:00:00 +0000"),  # martes 23:00 en BA
            ("Es de hoy", "https://a.test/4", "Wed, 18 Nov 2026 00:00:00 -0300"),
            ("Es de anteayer", "https://a.test/5", "Mon, 16 Nov 2026 23:59:59 -0300"),
        ]
        datos, _ = self._obtener({"https://a.test/rss": utiles.rss(items)}, [_fuente()])
        self.assertEqual(sorted(n["titulo"] for n in datos["notas"]),
                         ["Entra a la mañana", "Entra a la noche", "Entra por UTC"])
        self.assertEqual(datos["ventana"], {"desde": "17/11/2026", "hasta": "17/11/2026"})

    def test_los_lunes_la_ventana_es_de_viernes_a_domingo(self):
        items = [
            ("Jueves", "https://a.test/j", "Thu, 12 Nov 2026 23:00:00 -0300"),
            ("Viernes", "https://a.test/v", "Fri, 13 Nov 2026 00:00:00 -0300"),
            ("Sabado", "https://a.test/s", "Sat, 14 Nov 2026 12:00:00 -0300"),
            ("Domingo", "https://a.test/d", "Sun, 15 Nov 2026 23:59:00 -0300"),
            ("Lunes", "https://a.test/l", "Mon, 16 Nov 2026 08:00:00 -0300"),
        ]
        datos, _ = self._obtener({"https://a.test/rss": utiles.rss(items)}, [_fuente()], ahora=utiles.LUNES)
        self.assertEqual(sorted(n["titulo"] for n in datos["notas"]), ["Domingo", "Sabado", "Viernes"])
        self.assertEqual(datos["ventana"], {"desde": "13/11/2026", "hasta": "15/11/2026"})

    def test_notas_sin_fecha_se_descartan(self):
        feed = utiles.fixture("rss.xml").encode("utf-8")
        datos, _ = self._obtener({"https://a.test/rss": feed}, [_fuente()])
        titulos = [n["titulo"] for n in datos["notas"]]
        self.assertNotIn("Nota sin fecha", titulos)
        self.assertNotIn("Nota con fecha rota", titulos)
        self.assertEqual(len(titulos), 2)

    def test_cada_nota_trae_link_medio_seccion_y_fecha(self):
        feed = utiles.rss([("Nota", "https://a.test/1", MARTES_A_LA_MANANA)])
        datos, _ = self._obtener({"https://a.test/rss": feed}, [_fuente()])
        self.assertEqual(datos["notas"], [{
            "titulo": "Nota", "medio": "Medio A", "seccion": "Política",
            "fecha": "17/11/2026 09:00", "link": "https://a.test/1", "bajada": "", "categorias": [],
        }])

    def _feed_con_notas(self, cantidad):
        return utiles.rss([(f"Nota {n}", f"https://a.test/{n}", f"Tue, 17 Nov 2026 {10 + n:02d}:00:00 -0300")
                           for n in range(cantidad)])

    def test_cupo_de_8_por_medio_y_seccion_y_tope_del_resumen_de_3(self):
        datos, _ = self._obtener({"https://a.test/rss": self._feed_con_notas(10)}, [_fuente()])
        self.assertEqual(datos["tope_por_medio"], 3)  # la regla del resumen no cambia
        self.assertEqual(len(datos["notas"]), 8)
        # se quedan las 8 más nuevas
        self.assertEqual(sorted(n["titulo"] for n in datos["notas"]), [f"Nota {n}" for n in range(2, 10)])

    def test_el_cupo_es_por_medio_y_seccion(self):
        # 5 notas de Política más nuevas que 2 de Tecnología: antes Tecnología quedaba vacía.
        fuentes = [_fuente(seccion="Política"), _fuente(seccion="Tecnología", url="https://a.test/tec")]
        feeds = {"https://a.test/rss": self._feed_con_notas(10),  # 10:00 a 19:00 hs
                 "https://a.test/tec": utiles.rss([(f"Tec {n}", f"https://a.test/tec/{n}", MARTES_A_LA_MANANA)
                                                   for n in range(2)])}
        datos, _ = self._obtener(feeds, fuentes, temas=("Política", "Tecnología"))
        por_seccion = {s: sum(1 for n in datos["notas"] if n["seccion"] == s) for s in ("Política", "Tecnología")}
        self.assertEqual(por_seccion, {"Política": 8, "Tecnología": 2})
        self.assertEqual(datos["tope_por_medio"], 3)  # la regla del resumen no cambia

    def test_el_lunes_el_cupo_por_medio_y_seccion_es_13(self):
        fuentes = [_fuente(seccion="Política"), _fuente(seccion="Economía", url="https://a.test/eco")]
        def feed(pref):
            return utiles.rss([(f"{pref} {n}", f"https://a.test/{pref}/{n}", f"Sat, 14 Nov 2026 {10 + n:02d}:00:00 -0300")
                               for n in range(14)])
        datos, _ = self._obtener({"https://a.test/rss": feed("P"), "https://a.test/eco": feed("E")},
                                 fuentes, ahora=utiles.LUNES)
        self.assertEqual(len(datos["notas"]), 26)
        self.assertEqual(datos["tope_por_medio"], 5)
        self.assertEqual(len({n["link"] for n in datos["notas"]}), 26)

    def test_tope_de_5_los_lunes_y_cupo_de_13(self):
        items = [(f"Nota {n}", f"https://a.test/{n}", f"Sat, 14 Nov 2026 {10 + n:02d}:00:00 -0300")
                 for n in range(14)]
        datos, _ = self._obtener({"https://a.test/rss": utiles.rss(items)}, [_fuente()], ahora=utiles.LUNES)
        self.assertEqual(datos["tope_por_medio"], 5)
        self.assertEqual(len(datos["notas"]), 13)

    def test_otro_medio_tiene_su_propio_tope(self):
        fuentes = [_fuente(), _fuente(medio="Medio B", url="https://b.test/rss")]
        feeds = {"https://a.test/rss": self._feed_con_notas(5),
                 "https://b.test/rss": utiles.rss([(f"B {n}", f"https://b.test/{n}", MARTES_A_LA_MANANA)
                                                   for n in range(5)])}
        datos, _ = self._obtener(feeds, fuentes)
        self.assertEqual(len(datos["notas"]), 10)

    def test_sin_repetidos_por_link(self):
        fuentes = [_fuente(), _fuente(medio="Medio B", url="https://b.test/rss")]
        igual = utiles.rss([("Misma", "https://x.test/misma", MARTES_A_LA_MANANA)])
        datos, _ = self._obtener({"https://a.test/rss": igual, "https://b.test/rss": igual}, fuentes)
        self.assertEqual(len(datos["notas"]), 1)
        self.assertEqual(datos["notas"][0]["medio"], "Medio A")  # gana el primer feed

    def test_feed_caido_se_descarta_y_queda_el_aviso(self):
        fuentes = [_fuente(), _fuente(medio="Medio B", url="https://b.test/rss"),
                   _fuente(medio="Medio C", url="https://c.test/rss"), _fuente(medio="Medio D", url="https://d.test/rss")]
        feeds = {
            "https://a.test/rss": URLError(ConnectionRefusedError("sin conexión")),
            "https://b.test/rss": HTTPError("https://b.test/rss", 500, "error", None, None),
            "https://c.test/rss": b"<html>esto no es un rss</html>",
            "https://d.test/rss": utiles.rss([("Anda", "https://d.test/1", MARTES_A_LA_MANANA)]),
        }
        datos, _ = self._obtener(feeds, fuentes)
        self.assertEqual([n["titulo"] for n in datos["notas"]], ["Anda"])
        self.assertEqual([(f["medio"], f["motivo"]) for f in datos["fallas"]], [
            ("Medio A", "no se pudo conectar"),
            ("Medio B", "respondió con error HTTP 500"),
            ("Medio C", "el documento no es un RSS válido"),
        ])

    def test_solo_se_leen_los_feeds_de_los_temas_elegidos(self):
        fuentes = [_fuente(seccion="Política"), _fuente(medio="B", seccion="Deportes", url="https://b.test/rss"),
                   _fuente(medio="C", seccion="Internacional", url="https://c.test/rss")]
        feed = utiles.rss([("N", "https://x.test/1", MARTES_A_LA_MANANA)])
        feeds = {"https://a.test/rss": feed, "https://b.test/rss": feed, "https://c.test/rss": feed}
        datos, leer = self._obtener(feeds, fuentes, temas=("Política",))
        self.assertEqual(leer.pedidas, ["https://a.test/rss"])
        self.assertNotIn("Internacional", [n["seccion"] for n in datos["notas"]])

    def test_con_internacional_tildada_se_pide_su_feed_y_con_un_solo_tema_no_se_pide_otro(self):
        fuentes = [_fuente(seccion="Política"), _fuente(medio="B", seccion="Deportes", url="https://b.test/rss"),
                   _fuente(medio="C", seccion="Internacional", url="https://c.test/rss")]
        feed = utiles.rss([("N", "https://x.test/1", MARTES_A_LA_MANANA)])
        feeds = {"https://a.test/rss": feed, "https://b.test/rss": feed, "https://c.test/rss": feed}
        datos, leer = self._obtener(feeds, fuentes, temas=("Internacional",))
        self.assertEqual(leer.pedidas, ["https://c.test/rss"])
        self.assertEqual([n["seccion"] for n in datos["notas"]], ["Internacional"])

    def test_las_secciones_salen_en_orden_fijo(self):
        fuentes = [_fuente(seccion="Economía", url="https://e.test/rss"), _fuente(seccion="Política")]
        feeds = {"https://e.test/rss": utiles.rss([("Eco", "https://x.test/e", MARTES_A_LA_MANANA)]),
                 "https://a.test/rss": utiles.rss([("Pol", "https://x.test/p", MARTES_A_LA_MANANA)])}
        datos, _ = self._obtener(feeds, fuentes)
        self.assertEqual([n["seccion"] for n in datos["notas"]], ["Política", "Economía"])


class FeedsNuevos(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)

    def test_feed_nuevo_aplica_ventana_y_descarta_sin_fecha_sin_link_o_con_fecha_iso(self):
        fuente = _fuente("Perfil", "Tecnología", "https://perfil.test/tec")
        leer = _lector({"https://perfil.test/tec": utiles.fixture("rss_perfil_gmt.xml").encode("utf-8")})
        datos = noticias.obtener(["Tecnología"], ahora=utiles.MIERCOLES, fuentes=[fuente], leer=leer)
        self.assertEqual([n["titulo"] for n in datos["notas"]], ["Nota de ayer con GMT"])
        self.assertEqual(datos["notas"][0]["medio"], "Perfil")

    def test_feed_nuevo_caido_no_rompe_a_los_demas(self):
        fuentes = [_fuente("Perfil", "Tecnología", "https://perfil.test/tec"),
                   _fuente("Ámbito", "Tecnología", "https://ambito.test/tec")]
        leer = _lector({"https://perfil.test/tec": URLError("caído"),
                        "https://ambito.test/tec": utiles.fixture("rss_perfil_gmt.xml").encode("utf-8")})
        datos = noticias.obtener(["Tecnología"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=leer)
        self.assertEqual(len(datos["notas"]), 1)
        self.assertEqual([f["medio"] for f in datos["fallas"]], ["Perfil"])


class DiagnosticoPorFuente(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)

    def _feeds(self):
        # Feed A: 7 notas leídas, 5 en la ventana (martes 17), 1 de anteayer y 1 de hoy.
        items_a = [(f"A{n}", f"https://a.test/{n}", f"Tue, 17 Nov 2026 {10 + n:02d}:00:00 -0300") for n in range(5)]
        items_a += [("Vieja", "https://a.test/vieja", "Mon, 16 Nov 2026 10:00:00 -0300"),
                    ("De hoy", "https://a.test/hoy", "Wed, 18 Nov 2026 08:00:00 -0300")]
        # Feed B (otro medio): repite un link de A y suma una propia.
        items_b = [("Repetida", "https://a.test/4", MARTES_A_LA_MANANA),
                   ("Propia", "https://b.test/1", MARTES_A_LA_MANANA)]
        return {"https://a.test/rss": utiles.rss(items_a), "https://b.test/rss": utiles.rss(items_b),
                "https://c.test/rss": URLError(ConnectionRefusedError("x"))}

    def _fuentes(self):
        return [_fuente(), _fuente(medio="Medio B", url="https://b.test/rss"),
                _fuente(medio="Medio C", url="https://c.test/rss")]

    def test_cuenta_leidas_en_ventana_y_elegidas_por_feed(self):
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=self._fuentes(),
                                 leer=_lector(self._feeds()))
        # A: cupo 8 y 5 en ventana, entran todas. B: "Repetida" es de A (gana el primero), así que solo queda "Propia".
        self.assertEqual(datos["por_fuente"], [
            {"medio": "Medio A", "seccion": "Política", "leidas": 7, "en_ventana": 5, "elegidas": 5},
            {"medio": "Medio B", "seccion": "Política", "leidas": 2, "en_ventana": 2, "elegidas": 1},
        ])
        self.assertEqual(len(datos["notas"]), 6)
        self.assertEqual([f["medio"] for f in datos["fallas"]], ["Medio C"])  # el que falló no está en por_fuente

    def test_el_log_trae_solo_conteos(self):
        with self.assertLogs("micafe.fuentes.noticias", level="INFO") as registro:
            noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=self._fuentes(),
                             leer=_lector(self._feeds()))
        lineas = [m for m in registro.output if "leidas=" in m]
        self.assertEqual(len(lineas), 2)
        self.assertIn("leidas=7, en_ventana=5, elegidas=5", lineas[0])
        for linea in lineas:
            self.assertNotIn("http", linea)
            self.assertNotIn("A0", linea)
            self.assertNotIn("Propia", linea)


if __name__ == "__main__":
    unittest.main()


class BajadaEnObtener(unittest.TestCase):
    def _obtener(self):
        feeds = {"https://a.test/rss": utiles.fixture("rss_bajada.xml").encode("utf-8")}
        return noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=[_fuente()], leer=_lector(feeds))

    def test_las_candidatas_traen_bajada_y_categorias(self):
        por_titulo = {n["titulo"]: n for n in self._obtener()["notas"]}
        # El cupo por medio y sección es 3: quedan las 3 más nuevas del fixture.
        self.assertEqual(por_titulo["Muchas categorias"]["categorias"], ["a", "b", "c", "d", "e"])
        self.assertEqual(por_titulo["Sin nada"]["bajada"], "")
        self.assertEqual(por_titulo["Sin nada"]["categorias"], [])

    def test_el_log_no_trae_titulos_ni_bajadas(self):
        with self.assertLogs("micafe", level="DEBUG") as registro:
            self._obtener()
        salida = "\n".join(registro.output)
        self.assertIn("Feed Medio A", salida)
        for prohibido in ("Muchas categorias", "Sin nada", "Con HTML", "Hola & chau", "Texto con saltos"):
            self.assertNotIn(prohibido, salida)


class LecturaEnParalelo(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)

    def _lector_lento(self, feeds, demoras):
        """Lector falso con demoras por url; registra pedidas y el máximo de lecturas simultáneas."""
        estado = {"activas": 0, "maximo": 0, "pedidas": []}
        candado = threading.Lock()

        def leer(url):
            with candado:
                estado["pedidas"].append(url)
                estado["activas"] += 1
                estado["maximo"] = max(estado["maximo"], estado["activas"])
            try:
                time.sleep(demoras.get(url, 0))
                respuesta = feeds[url]
                if isinstance(respuesta, Exception):
                    raise respuesta
                return respuesta
            finally:
                with candado:
                    estado["activas"] -= 1

        leer.estado = estado
        return leer

    def _fuentes(self, cantidad):
        return [_fuente(medio=f"Medio {i}", url=f"https://m{i}.test/rss") for i in range(cantidad)]

    def _feeds(self, cantidad):
        return {f"https://m{i}.test/rss": utiles.rss([(f"Nota {i}", f"https://x.test/{i}", MARTES_A_LA_MANANA)])
                for i in range(cantidad)}

    def test_el_orden_es_el_de_las_fuentes_aunque_el_primero_tarde_mas(self):
        fuentes, feeds = self._fuentes(4), self._feeds(4)
        feeds["https://m1.test/rss"] = URLError(ConnectionRefusedError("x"))
        feeds["https://m0.test/rss"] = HTTPError("https://m0.test/rss", 404, "no", None, None)
        leer = self._lector_lento(feeds, {"https://m0.test/rss": 0.3, "https://m1.test/rss": 0.2})
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=leer)
        self.assertEqual([c["medio"] for c in datos["por_fuente"]], ["Medio 2", "Medio 3"])
        self.assertEqual([(f["medio"], f["motivo"]) for f in datos["fallas"]],
                         [("Medio 0", "respondió con error HTTP 404"), ("Medio 1", "no se pudo conectar")])

    def test_resultado_igual_al_secuencial(self):
        fuentes, feeds = self._fuentes(5), self._feeds(5)
        rapido = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=lambda u: feeds[u])
        lento = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes,
                                 leer=self._lector_lento(feeds, {"https://m0.test/rss": 0.2}))
        self.assertEqual(rapido["notas"], lento["notas"])
        self.assertEqual(rapido["por_fuente"], lento["por_fuente"])
        self.assertEqual(len(lento["notas"]), 5)

    def test_fallas_mezcladas_no_frenan_a_los_demas(self):
        fuentes, feeds = self._fuentes(4), self._feeds(4)
        feeds["https://m0.test/rss"] = TimeoutError("lento")
        feeds["https://m1.test/rss"] = b"<rss><channel>"
        feeds["https://m2.test/rss"] = b"<html>no</html>"
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes,
                                 leer=self._lector_lento(feeds, {}))
        self.assertEqual([n["titulo"] for n in datos["notas"]], ["Nota 3"])
        self.assertEqual([f["motivo"] for f in datos["fallas"]],
                         ["tardó demasiado en responder", "el XML no es válido", "el documento no es un RSS válido"])

    def test_link_repetido_se_lo_queda_el_primero_aunque_el_segundo_termine_antes(self):
        fuentes = self._fuentes(2)
        igual = utiles.rss([("Misma", "https://x.test/misma", MARTES_A_LA_MANANA)])
        feeds = {"https://m0.test/rss": igual, "https://m1.test/rss": igual}
        leer = self._lector_lento(feeds, {"https://m0.test/rss": 0.2})
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=leer)
        self.assertEqual([n["medio"] for n in datos["notas"]], ["Medio 0"])
        self.assertEqual([c["elegidas"] for c in datos["por_fuente"]], [1, 0])

    def test_tiempo_menor_que_la_suma_y_tope_de_lecturas_simultaneas(self):
        cantidad = 12
        fuentes, feeds = self._fuentes(cantidad), self._feeds(cantidad)
        leer = self._lector_lento(feeds, {u: 0.3 for u in feeds})
        inicio = time.monotonic()
        noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=leer)
        total = time.monotonic() - inicio
        self.assertLess(total, cantidad * 0.3 * 0.7)
        self.assertGreater(leer.estado["maximo"], 1)
        self.assertLessEqual(leer.estado["maximo"], noticias.HILOS_FEEDS)

    def test_solo_se_piden_las_urls_de_las_secciones_tildadas(self):
        fuentes = [_fuente(url="https://a.test/rss"), _fuente(medio="B", seccion="Deportes", url="https://b.test/rss")]
        feed = utiles.rss([("N", "https://x.test/1", MARTES_A_LA_MANANA)])
        leer = self._lector_lento({"https://a.test/rss": feed, "https://b.test/rss": feed}, {})
        noticias.obtener(["Deportes"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=leer)
        self.assertEqual(leer.estado["pedidas"], ["https://b.test/rss"])

    def test_un_error_imprevisto_se_propaga(self):
        fuentes, feeds = self._fuentes(2), self._feeds(2)
        feeds["https://m0.test/rss"] = RuntimeError("bug")
        with self.assertRaises(RuntimeError):
            noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=fuentes, leer=self._lector_lento(feeds, {}))


class SubtemasDeDeportes(unittest.TestCase):
    """Spec 45: clasificación de las notas de Deportes en subtemas."""

    def setUp(self):
        utiles.silenciar(self)

    def test_el_subtema_de_la_fuente_gana(self):
        self.assertEqual(noticias.subtema_de({"titulo": "Boca ganó"}, "Tenis"), "Tenis")

    def test_por_categoria_del_rss(self):
        self.assertEqual(noticias.subtema_de({"titulo": "Algo", "categorias": ["Básquet"]}), "Básquet")
        self.assertEqual(noticias.subtema_de({"titulo": "Algo", "categorias": ["NBA"]}), "Básquet")

    def test_por_palabra_clave_en_titulo_y_en_bajada_sin_tildes_ni_mayusculas(self):
        self.assertEqual(noticias.subtema_de({"titulo": "VÉLEZ renovó"}), "Fútbol argentino")
        self.assertEqual(noticias.subtema_de({"titulo": "Final", "bajada": "juega Djokovic hoy"}), "Tenis")
        self.assertEqual(noticias.subtema_de({"titulo": "Se corre el GRAN PREMIO"}), "Automovilismo")

    def test_palabra_completa_y_nada_que_encaje_es_otros(self):
        self.assertEqual(noticias.subtema_de({"titulo": "Los bocadillos del día"}), "Otros")
        self.assertEqual(noticias.subtema_de({"titulo": "Ping pong"}), "Otros")

    def test_desempate_por_el_orden_de_subtemas(self):
        self.assertEqual(noticias.subtema_de({"titulo": "Boca y el Real Madrid"}), "Fútbol argentino")

    def test_fuente_con_subtema_clasifica_todas_sus_notas(self):
        fuente = dict(_fuente(seccion="Deportes"), subtema="Tenis")
        datos = noticias.obtener(["Deportes"], ahora=utiles.MIERCOLES, fuentes=[fuente],
                                 leer=_lector({"https://a.test/rss": utiles.fixture("rss_ole.xml").encode("utf-8")}))
        self.assertEqual({n["subtema"] for n in datos["notas"]}, {"Tenis"})

    def test_feed_general_clasifica_por_palabras_clave(self):
        datos = noticias.obtener(["Deportes"], ahora=utiles.MIERCOLES, fuentes=[_fuente(seccion="Deportes")],
                                 leer=_lector({"https://a.test/rss": utiles.fixture("rss_ole.xml").encode("utf-8")}))
        self.assertEqual({n["link"].rsplit("/", 1)[1]: n["subtema"] for n in datos["notas"]},
                         {"boca-river": "Fútbol argentino", "davis": "Tenis", "campazzo": "Básquet",
                          "colapinto": "Automovilismo", "otros": "Otros"})

    def test_solo_deportes_lleva_subtema(self):
        datos = noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=[_fuente(seccion="Política")],
                                 leer=_lector({"https://a.test/rss": utiles.fixture("rss_ole.xml").encode("utf-8")}))
        self.assertTrue(datos["notas"])
        self.assertTrue(all("subtema" not in n for n in datos["notas"]))
