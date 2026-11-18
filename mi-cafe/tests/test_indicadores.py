"""Tests de indicadores.py: formato, brechas, "sin dato" y copia local de 3 horas."""

import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

from micafe.fuentes import indicadores, utilidades
from tests import utiles


def _fuentes(dolar=True, riesgo=True, reservas=True):
    """Devuelve un reemplazo de indicadores._pedir_json que responde con los fixtures."""
    llamadas = []

    def falso(url):
        llamadas.append(url)
        if url == indicadores.URL_DOLARAPI:
            return (utiles.fixture_json("dolarapi.json"), None) if dolar else (None, "no se pudo conectar")
        if url == indicadores.URL_RIESGO_PAIS:
            return (utiles.fixture_json("argentinadatos_riesgo_pais.json"), None) if riesgo else (None, "tardó demasiado en responder")
        if url == indicadores.URL_RESERVAS:
            return (utiles.fixture_json("bcra_reservas.json"), None) if reservas else (None, "respondió con error HTTP 500")
        raise AssertionError(f"URL inesperada: {url}")

    falso.llamadas = llamadas
    return falso


class FormatoDeMontos(unittest.TestCase):
    def test_monto_con_punto_de_miles_y_coma_decimal(self):
        self.assertEqual(utilidades.monto(1234.5), "$ 1.234,50")

    def test_monto_grande_con_varios_miles(self):
        self.assertEqual(utilidades.monto(1234567.891), "$ 1.234.567,89")

    def test_monto_chico(self):
        self.assertEqual(utilidades.monto(5), "$ 5,00")

    def test_numero_sin_decimales(self):
        self.assertEqual(utilidades.formatear_numero(1234, 0), "1.234")


class DiasHabiles(unittest.TestCase):
    def test_de_viernes_a_lunes_es_un_dia_habil(self):
        self.assertEqual(utilidades.dias_habiles_entre(date(2026, 11, 13), date(2026, 11, 16)), 1)

    def test_mismo_dia_es_cero(self):
        self.assertEqual(utilidades.dias_habiles_entre(date(2026, 11, 17), date(2026, 11, 17)), 0)

    def test_de_martes_a_jueves_son_dos(self):
        self.assertEqual(utilidades.dias_habiles_entre(date(2026, 11, 17), date(2026, 11, 19)), 2)


class ObtenerIndicadores(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.copia = os.path.join(self.carpeta.name, "indicadores.json")

    def _obtener(self, falso, elegidos=("dolar", "riesgo_pais"), ahora=utiles.MIERCOLES):
        with mock.patch.object(indicadores, "_pedir_json", falso):
            return indicadores.obtener(self.copia, list(elegidos), ahora=ahora)

    @staticmethod
    def _por_clave(datos):
        return {i["clave"]: i for i in datos["indicadores"]}

    def test_dolares_con_formato_fecha_y_fuente(self):
        datos = self._obtener(_fuentes())
        oficial = self._por_clave(datos)["dolar_oficial"]
        self.assertEqual(oficial["valor"], "venta $ 1.000,00 (compra $ 980,00)")
        self.assertEqual(oficial["fecha"], "17/11/2026 12:00")
        self.assertIn("DolarApi", oficial["fuente"])
        self.assertFalse(oficial["desactualizado"])

    def test_brecha_calculada_contra_el_oficial(self):
        por_clave = self._por_clave(self._obtener(_fuentes()))
        self.assertEqual(por_clave["brecha_blue"]["valor"], "20,00 %")
        self.assertEqual(por_clave["brecha_bolsa"]["valor"], "10,05 %")
        self.assertEqual(por_clave["brecha_contadoconliqui"]["valor"], "23,45 %")

    def test_riesgo_pais_y_reservas(self):
        por_clave = self._por_clave(self._obtener(_fuentes()))
        self.assertEqual(por_clave["riesgo_pais"]["valor"], "580 puntos básicos")
        self.assertEqual(por_clave["riesgo_pais"]["fecha"], "17/11/2026")
        self.assertEqual(por_clave["reservas"]["valor"], "US$ 41.234,50 millones")
        self.assertEqual(por_clave["reservas"]["fecha"], "17/11/2026")

    def test_sin_dato_si_falla_dolarapi_y_los_demas_siguen(self):
        datos = self._obtener(_fuentes(dolar=False))
        por_clave = self._por_clave(datos)
        for clave in ("dolar_oficial", "dolar_blue", "brecha_blue", "brecha_bolsa"):
            self.assertIsNone(por_clave[clave]["valor"], clave)
            self.assertIsNone(por_clave[clave]["fecha"], clave)
        self.assertEqual(por_clave["riesgo_pais"]["valor"], "580 puntos básicos")
        self.assertTrue(any("No se pudo consultar DolarApi" in a for a in datos["avisos"]))

    def test_sin_dato_si_falla_riesgo_pais_y_reservas(self):
        datos = self._obtener(_fuentes(riesgo=False, reservas=False))
        por_clave = self._por_clave(datos)
        self.assertIsNone(por_clave["riesgo_pais"]["valor"])
        self.assertIsNone(por_clave["reservas"]["valor"])
        self.assertEqual(len(datos["avisos"]), 2)

    def test_sin_dato_si_la_respuesta_no_tiene_la_forma_esperada(self):
        def raro(url):
            return {"cualquier": "cosa"}, None
        por_clave = self._por_clave(self._obtener(raro))
        self.assertIsNone(por_clave["dolar_blue"]["valor"])
        self.assertIsNone(por_clave["riesgo_pais"]["valor"])
        self.assertIsNone(por_clave["reservas"]["valor"])

    def test_dato_viejo_queda_desactualizado_y_avisa(self):
        # Se consulta tres días hábiles después de la fecha del dato.
        datos = self._obtener(_fuentes(), ahora=utiles.MIERCOLES + timedelta(days=2))
        riesgo = self._por_clave(datos)["riesgo_pais"]
        self.assertTrue(riesgo["desactualizado"])
        self.assertTrue(any("Riesgo país" in a and "desactualizado" in a for a in datos["avisos"]))

    def test_solo_trae_lo_que_eligio_la_persona(self):
        datos = self._obtener(_fuentes(), elegidos=("riesgo_pais",))
        claves = [i["clave"] for i in datos["indicadores"]]
        self.assertEqual(claves, ["riesgo_pais", "reservas"])  # reservas se trae siempre


class CopiaLocal(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.copia = os.path.join(carpeta.name, "indicadores.json")

    def _consultas_a_riesgo(self, ahora):
        falso = _fuentes()
        with mock.patch.object(indicadores, "_pedir_json", falso):
            indicadores.obtener(self.copia, ["riesgo_pais"], ahora=ahora)
        return falso.llamadas.count(indicadores.URL_RIESGO_PAIS)

    def test_primera_vez_consulta_y_guarda_la_copia(self):
        self.assertEqual(self._consultas_a_riesgo(utiles.MIERCOLES), 1)
        self.assertTrue(os.path.exists(self.copia))

    def test_antes_de_3_horas_usa_la_copia(self):
        self._consultas_a_riesgo(utiles.MIERCOLES)
        self.assertEqual(self._consultas_a_riesgo(utiles.MIERCOLES + timedelta(hours=2, minutes=59)), 0)

    def test_pasadas_las_3_horas_vuelve_a_consultar(self):
        self._consultas_a_riesgo(utiles.MIERCOLES)
        self.assertEqual(self._consultas_a_riesgo(utiles.MIERCOLES + timedelta(hours=3)), 1)

    def test_copia_rota_se_ignora_y_se_consulta(self):
        with open(self.copia, "w", encoding="utf-8") as archivo:
            archivo.write("{esto no es json")
        self.assertEqual(self._consultas_a_riesgo(utiles.MIERCOLES), 1)

    def test_la_copia_no_se_usa_si_cambio_la_url(self):
        self._consultas_a_riesgo(utiles.MIERCOLES)
        with mock.patch.object(indicadores, "URL_RIESGO_PAIS", "https://otra.test/riesgo"):
            falso = mock.Mock(return_value=({"fecha": "2026-11-17", "valor": 600}, None))
            with mock.patch.object(indicadores, "_pedir_json", falso):
                indicadores.obtener(self.copia, ["riesgo_pais"], ahora=utiles.MIERCOLES + timedelta(hours=1))
        riesgo_llamado = [c.args[0] for c in falso.call_args_list]
        self.assertIn("https://otra.test/riesgo", riesgo_llamado)


if __name__ == "__main__":
    unittest.main()
