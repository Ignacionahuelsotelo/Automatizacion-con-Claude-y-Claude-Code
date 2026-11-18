"""Tests de noticias.py: ventana de ayer, lunes, notas sin fecha, tope por medio y feeds caídos."""

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
            "fecha": "17/11/2026 09:00", "link": "https://a.test/1",
        }])

    def _feed_con_notas(self, cantidad):
        return utiles.rss([(f"Nota {n}", f"https://a.test/{n}", f"Tue, 17 Nov 2026 {10 + n:02d}:00:00 -0300")
                           for n in range(cantidad)])

    def test_tope_de_3_por_medio(self):
        datos, _ = self._obtener({"https://a.test/rss": self._feed_con_notas(6)}, [_fuente()])
        self.assertEqual(datos["tope_por_medio"], 3)
        self.assertEqual(len(datos["notas"]), 3)
        # se quedan las 3 más nuevas
        self.assertEqual(sorted(n["titulo"] for n in datos["notas"]), ["Nota 3", "Nota 4", "Nota 5"])

    def test_el_cupo_es_por_medio_y_seccion(self):
        # 5 notas de Política más nuevas que 2 de Tecnología: antes Tecnología quedaba vacía.
        fuentes = [_fuente(seccion="Política"), _fuente(seccion="Tecnología", url="https://a.test/tec")]
        feeds = {"https://a.test/rss": self._feed_con_notas(5),  # 10:00 a 14:00 hs
                 "https://a.test/tec": utiles.rss([(f"Tec {n}", f"https://a.test/tec/{n}", MARTES_A_LA_MANANA)
                                                   for n in range(2)])}
        datos, _ = self._obtener(feeds, fuentes, temas=("Política", "Tecnología"))
        por_seccion = {s: sum(1 for n in datos["notas"] if n["seccion"] == s) for s in ("Política", "Tecnología")}
        self.assertEqual(por_seccion, {"Política": 3, "Tecnología": 2})
        self.assertEqual(datos["tope_por_medio"], 3)  # la regla del resumen no cambia

    def test_el_lunes_el_cupo_por_medio_y_seccion_es_5(self):
        fuentes = [_fuente(seccion="Política"), _fuente(seccion="Economía", url="https://a.test/eco")]
        def feed(pref):
            return utiles.rss([(f"{pref} {n}", f"https://a.test/{pref}/{n}", f"Sat, 14 Nov 2026 {10 + n:02d}:00:00 -0300")
                               for n in range(8)])
        datos, _ = self._obtener({"https://a.test/rss": feed("P"), "https://a.test/eco": feed("E")},
                                 fuentes, ahora=utiles.LUNES)
        self.assertEqual(len(datos["notas"]), 10)
        self.assertEqual(datos["tope_por_medio"], 5)
        self.assertEqual(len({n["link"] for n in datos["notas"]}), 10)

    def test_tope_de_5_los_lunes(self):
        items = [(f"Nota {n}", f"https://a.test/{n}", f"Sat, 14 Nov 2026 {10 + n:02d}:00:00 -0300")
                 for n in range(8)]
        datos, _ = self._obtener({"https://a.test/rss": utiles.rss(items)}, [_fuente()], ahora=utiles.LUNES)
        self.assertEqual(datos["tope_por_medio"], 5)
        self.assertEqual(len(datos["notas"]), 5)

    def test_otro_medio_tiene_su_propio_tope(self):
        fuentes = [_fuente(), _fuente(medio="Medio B", url="https://b.test/rss")]
        feeds = {"https://a.test/rss": self._feed_con_notas(5),
                 "https://b.test/rss": utiles.rss([(f"B {n}", f"https://b.test/{n}", MARTES_A_LA_MANANA)
                                                   for n in range(5)])}
        datos, _ = self._obtener(feeds, fuentes)
        self.assertEqual(len(datos["notas"]), 6)

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

    def test_solo_se_leen_los_feeds_de_los_temas_elegidos_mas_internacional(self):
        fuentes = [_fuente(seccion="Política"), _fuente(medio="B", seccion="Deportes", url="https://b.test/rss"),
                   _fuente(medio="C", seccion="Internacional", url="https://c.test/rss")]
        feed = utiles.rss([("N", "https://x.test/1", MARTES_A_LA_MANANA)])
        feeds = {"https://a.test/rss": feed, "https://b.test/rss": feed, "https://c.test/rss": feed}
        _, leer = self._obtener(feeds, fuentes, temas=("Política",))
        self.assertEqual(leer.pedidas, ["https://a.test/rss", "https://c.test/rss"])

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
        # A: tope 3 de 5 en ventana. B: "Repetida" es de A (gana el primero), así que solo queda "Propia".
        self.assertEqual(datos["por_fuente"], [
            {"medio": "Medio A", "seccion": "Política", "leidas": 7, "en_ventana": 5, "elegidas": 3},
            {"medio": "Medio B", "seccion": "Política", "leidas": 2, "en_ventana": 2, "elegidas": 1},
        ])
        self.assertEqual(len(datos["notas"]), 4)
        self.assertEqual([f["medio"] for f in datos["fallas"]], ["Medio C"])  # el que falló no está en por_fuente

    def test_el_log_trae_solo_conteos(self):
        with self.assertLogs("micafe.fuentes.noticias", level="INFO") as registro:
            noticias.obtener(["Política"], ahora=utiles.MIERCOLES, fuentes=self._fuentes(),
                             leer=_lector(self._feeds()))
        lineas = [m for m in registro.output if "leidas=" in m]
        self.assertEqual(len(lineas), 2)
        self.assertIn("leidas=7, en_ventana=5, elegidas=3", lineas[0])
        for linea in lineas:
            self.assertNotIn("http", linea)
            self.assertNotIn("A0", linea)
            self.assertNotIn("Propia", linea)


if __name__ == "__main__":
    unittest.main()
