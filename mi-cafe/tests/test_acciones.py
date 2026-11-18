"""Tests de acciones.py: data912 (GGAL, YPFD, PAMP) y MSCI Merval desde Rava."""

import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

from micafe.fuentes import acciones
from tests import utiles

URL_ROBOTS = acciones.URL_ROBOTS
AYER = date(2026, 11, 17)


def _url_rava(dia):
    return f"{acciones.URL_RAVA}{dia.year}/{dia.month:02d}/{dia.day:02d}/"


def _pagina_rava(dia, cierre="81.794"):
    """Página de Rava inventada: el JSON-LD dice que el índice cerró en `cierre` el día `dia`."""
    meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
    texto = utiles.fixture("rava_merval.html")
    return texto.replace("81.794", cierre).replace("17 de noviembre", f"{dia.day} de {meses[dia.month]}")


class UltimoCierreData912(unittest.TestCase):
    def test_toma_la_ultima_fila_menor_o_igual_a_ayer(self):
        filas = utiles.fixture_json("data912_ggal.json")  # trae una fila del 18/11, o sea de hoy
        self.assertEqual(acciones._ultimo_cierre(filas, AYER), (5123.45, AYER))

    def test_ignora_filas_invalidas(self):
        filas = [{"date": "2026-11-16", "c": 100.0}, {"date": "2026-11-17", "c": -5},
                 {"date": "no es fecha", "c": 9}, "basura", {"date": "2026-11-17"}]
        self.assertEqual(acciones._ultimo_cierre(filas, AYER), (100.0, date(2026, 11, 16)))

    def test_sin_filas_validas_no_hay_cierre(self):
        self.assertEqual(acciones._ultimo_cierre([], AYER), (None, None))
        self.assertEqual(acciones._ultimo_cierre({"no": "lista"}, AYER), (None, None))


class ObtenerData912(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.copia = os.path.join(carpeta.name, "acciones.json")

    def test_indicadores_con_monto_fecha_de_la_fila_y_fuente(self):
        falso = mock.Mock(return_value=(utiles.fixture_json("data912_ggal.json"), None))
        with mock.patch.object(acciones, "_pedir_json", falso):
            datos = acciones.obtener(self.copia, ahora=utiles.MIERCOLES)
        self.assertEqual(len(datos["indicadores"]), 3)
        ggal = datos["indicadores"][0]
        self.assertEqual(ggal["clave"], "accion_ggal")
        self.assertEqual(ggal["valor"], "$ 5.123,45")
        self.assertEqual(ggal["fecha"], "17/11/2026")
        self.assertIn("data912", ggal["fuente"])
        self.assertFalse(ggal["desactualizado"])
        self.assertEqual(datos["avisos"], [])

    def test_sin_dato_si_falla_la_fuente_y_avisa(self):
        falso = mock.Mock(return_value=(None, "no se pudo conectar"))
        with mock.patch.object(acciones, "_pedir_json", falso):
            datos = acciones.obtener(self.copia, ahora=utiles.MIERCOLES)
        for indicador in datos["indicadores"]:
            self.assertIsNone(indicador["valor"])
            self.assertIsNone(indicador["fecha"])
        self.assertEqual(len(datos["avisos"]), 3)
        self.assertTrue(all("sin dato" in aviso for aviso in datos["avisos"]))

    def test_dato_desactualizado_marca_y_avisa(self):
        filas = [{"date": "2026-11-12", "c": 5000.0}]
        with mock.patch.object(acciones, "_pedir_json", mock.Mock(return_value=(filas, None))):
            datos = acciones.obtener(self.copia, ahora=utiles.MIERCOLES)
        self.assertTrue(all(i["desactualizado"] for i in datos["indicadores"]))
        self.assertTrue(any("desactualizado" in a and "12/11/2026" in a for a in datos["avisos"]))

    def test_copia_de_menos_de_3_horas_no_vuelve_a_consultar(self):
        falso = mock.Mock(return_value=(utiles.fixture_json("data912_ggal.json"), None))
        with mock.patch.object(acciones, "_pedir_json", falso):
            acciones.obtener(self.copia, ahora=utiles.MIERCOLES)
            self.assertEqual(falso.call_count, 3)
            acciones.obtener(self.copia, ahora=utiles.MIERCOLES + timedelta(hours=2))
            self.assertEqual(falso.call_count, 3)
            acciones.obtener(self.copia, ahora=utiles.MIERCOLES + timedelta(hours=3))
            self.assertEqual(falso.call_count, 6)

    def test_una_consulta_fallida_no_queda_como_vigente(self):
        with mock.patch.object(acciones, "_pedir_json", mock.Mock(return_value=(None, "no se pudo conectar"))):
            acciones.obtener(self.copia, ahora=utiles.MIERCOLES)
        falso = mock.Mock(return_value=(utiles.fixture_json("data912_ggal.json"), None))
        with mock.patch.object(acciones, "_pedir_json", falso):
            acciones.obtener(self.copia, ahora=utiles.MIERCOLES + timedelta(minutes=5))
        self.assertEqual(falso.call_count, 3)


class FormatoDePuntos(unittest.TestCase):
    def test_entero_con_punto_de_miles(self):
        self.assertEqual(acciones._formatear_puntos(81794), "81.794")

    def test_con_decimales_usa_coma(self):
        self.assertEqual(acciones._formatear_puntos(81794.5), "81.794,50")


class JsonLdDeRava(unittest.TestCase):
    def test_lee_cierre_y_fecha(self):
        self.assertEqual(acciones._leer_json_ld(utiles.fixture("rava_merval.html")), (81794.0, AYER))

    def test_sin_json_ld_no_hay_dato(self):
        self.assertIsNone(acciones._leer_json_ld("<html><body>nada</body></html>"))


class MervalDeRava(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.copia = os.path.join(carpeta.name, "acciones.json")
        self.pedidos = []

    def _html(self, paginas, robots="User-agent: *\nDisallow: /privado/\n"):
        """Reemplazo de acciones._pedir_html. `paginas` = {fecha: html}; el resto da 404."""
        def falso(url):
            self.pedidos.append(url)
            if url == URL_ROBOTS:
                return robots, None
            for dia, html in paginas.items():
                if url == _url_rava(dia):
                    return html, None
            return None, "404"
        return falso

    def _obtener(self, paginas, ahora=utiles.MIERCOLES, **kwargs):
        with mock.patch.object(acciones, "_pedir_html", self._html(paginas, **kwargs)):
            return acciones.obtener_merval(self.copia, ahora=ahora)

    def _pedidos_a_rava(self):
        return [p for p in self.pedidos if p.startswith(acciones.URL_RAVA)]

    def test_cierre_de_ayer_con_formato_de_puntos(self):
        resultado = self._obtener({AYER: _pagina_rava(AYER)})
        indicador = resultado["indicador"]
        self.assertEqual(indicador["valor"], "81.794 puntos")
        self.assertEqual(indicador["fecha"], "17/11/2026")
        self.assertIn("Rava", indicador["fuente"])
        self.assertEqual(resultado["avisos"], [])

    def test_el_nombre_es_msci_merval_y_no_sp(self):
        indicador = self._obtener({AYER: _pagina_rava(AYER)})["indicador"]
        self.assertEqual(indicador["nombre"], "MSCI Merval")
        self.assertNotIn("S&P", indicador["nombre"])
        self.assertEqual(acciones.NOMBRE_MERVAL, "MSCI Merval")

    def test_fecha_del_json_ld_distinta_a_la_de_la_url_es_sin_dato(self):
        otro_dia = date(2026, 11, 12)
        resultado = self._obtener({AYER: _pagina_rava(otro_dia)})
        self.assertIsNone(resultado["indicador"]["valor"])
        self.assertTrue(any("validar" in a for a in resultado["avisos"]))

    def test_retrocede_cuando_no_hay_rueda(self):
        viernes = date(2026, 11, 13)
        resultado = self._obtener({viernes: _pagina_rava(viernes, "80.100")})
        self.assertEqual(resultado["indicador"]["valor"], "80.100 puntos")
        self.assertEqual(self._pedidos_a_rava(),
                         [_url_rava(AYER - timedelta(days=n)) for n in range(5)])

    def test_retrocede_hasta_7_dias_y_8_consultas(self):
        ultimo = AYER - timedelta(days=7)
        resultado = self._obtener({ultimo: _pagina_rava(ultimo, "79.000")})
        self.assertEqual(resultado["indicador"]["valor"], "79.000 puntos")
        self.assertEqual(len(self._pedidos_a_rava()), 8)

    def test_sin_pagina_en_8_dias_no_hay_dato_y_no_pasa_de_8_consultas(self):
        resultado = self._obtener({})
        self.assertIsNone(resultado["indicador"]["valor"])
        self.assertEqual(len(self._pedidos_a_rava()), 8)
        self.assertIn("El MSCI Merval se muestra sin dato.", resultado["avisos"])

    def test_dato_desactualizado_avisa(self):
        viernes = date(2026, 11, 13)  # miércoles 18: pasaron 3 días hábiles
        resultado = self._obtener({viernes: _pagina_rava(viernes)})
        self.assertTrue(resultado["indicador"]["desactualizado"])
        self.assertTrue(any("desactualizado" in a for a in resultado["avisos"]))

    def test_error_de_rava_que_no_es_404_corta_y_avisa(self):
        def falso(url):
            return (("User-agent: *\n", None) if url == URL_ROBOTS else (None, "no se pudo conectar"))
        with mock.patch.object(acciones, "_pedir_html", falso):
            resultado = acciones.obtener_merval(self.copia, ahora=utiles.MIERCOLES)
        self.assertIsNone(resultado["indicador"]["valor"])
        self.assertTrue(any("No se pudo consultar Rava" in a for a in resultado["avisos"]))

    def test_robots_que_bloquea_la_ruta_no_consulta_rava(self):
        resultado = self._obtener({AYER: _pagina_rava(AYER)},
                                  robots="User-agent: *\nDisallow: /cotizaciones/\n")
        self.assertIsNone(resultado["indicador"]["valor"])
        self.assertEqual(self._pedidos_a_rava(), [])

    def test_respaldo_desactivado_no_consulta_data912(self):
        self.assertIsNone(acciones.TICKER_RESPALDO)
        with mock.patch.object(acciones, "_pedir_json") as pedir:
            resultado = self._obtener({})
        pedir.assert_not_called()
        self.assertNotIn("Se usó data912 para el MSCI Merval.", resultado["avisos"])

    def test_copia_de_menos_de_3_horas_no_vuelve_a_consultar(self):
        self._obtener({AYER: _pagina_rava(AYER)})
        self.pedidos.clear()
        resultado = self._obtener({AYER: _pagina_rava(AYER)}, ahora=utiles.MIERCOLES + timedelta(hours=1))
        self.assertEqual(self.pedidos, [])
        self.assertEqual(resultado["indicador"]["valor"], "81.794 puntos")

    def test_consulta_fallida_no_deja_copia_vigente(self):
        self._obtener({})
        self.pedidos.clear()
        self._obtener({AYER: _pagina_rava(AYER)}, ahora=utiles.MIERCOLES + timedelta(minutes=10))
        self.assertTrue(self._pedidos_a_rava())


class ObtenerTodo(unittest.TestCase):
    def test_primero_el_msci_merval_y_despues_los_tres_tickers(self):
        utiles.silenciar(self)
        with tempfile.TemporaryDirectory() as carpeta:
            copia = os.path.join(carpeta, "acciones.json")
            html = lambda url: (("User-agent: *\n", None) if url == URL_ROBOTS else (_pagina_rava(AYER), None))
            json_ = mock.Mock(return_value=(utiles.fixture_json("data912_ggal.json"), None))
            with mock.patch.object(acciones, "_pedir_html", html), \
                    mock.patch.object(acciones, "_pedir_json", json_):
                datos = acciones.obtener_todo(copia, ahora=utiles.MIERCOLES)
        self.assertEqual([i["clave"] for i in datos["indicadores"]],
                         ["accion_mmsci", "accion_ggal", "accion_ypfd", "accion_pamp"])


if __name__ == "__main__":
    unittest.main()
