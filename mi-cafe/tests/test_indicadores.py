"""Tests de indicadores.py: formato, brechas, "sin dato" y copia local de 3 horas."""

import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

from micafe import config
from micafe.fuentes import indicadores, utilidades
from tests import utiles


def _url_bcra(serie):
    return config.URL_BCRA_VARIABLE.format(id=config.BCRA_IDS[serie])


_SERIES_AD = {
    "inflacion": (config.URL_INFLACION, "argentinadatos_inflacion.json"),
    "inflacion_interanual": (config.URL_INFLACION_INTERANUAL, "argentinadatos_inflacion_interanual.json"),
    "uva": (config.URL_UVA, "argentinadatos_uva.json"),
}


def _fuentes(dolar=True, riesgo=True, reservas=True, filtro_dolar=None, bcra=None, ad=None):
    """`bcra` y `ad` opcionales: {serie: respuesta o (None, motivo)} para pisar lo de cada serie."""
    """Devuelve un reemplazo de indicadores._pedir_json que responde con los fixtures."""
    llamadas = []

    def falso(url):
        llamadas.append(url)
        if url == indicadores.URL_DOLARAPI:
            filas = utiles.fixture_json("dolarapi.json")
            if filtro_dolar:
                filas = filtro_dolar(filas)
            return (filas, None) if dolar else (None, "no se pudo conectar")
        if url == indicadores.URL_RIESGO_PAIS:
            return (utiles.fixture_json("argentinadatos_riesgo_pais.json"), None) if riesgo else (None, "tardó demasiado en responder")
        for serie, (url_serie, archivo) in _SERIES_AD.items():
            if url == url_serie:
                if ad and serie in ad:
                    pisada = ad[serie]
                    return pisada if isinstance(pisada, tuple) else (pisada, None)
                return utiles.fixture_json(archivo), None
        for serie in config.BCRA_IDS:
            if url == _url_bcra(serie):
                if bcra and serie in bcra:
                    pisada = bcra[serie]
                    return pisada if isinstance(pisada, tuple) else (pisada, None)
                if serie == "reservas":
                    return (utiles.fixture_json("bcra_reservas.json"), None) if reservas else (None, "respondió con error HTTP 500")
                return utiles.fixture_json("bcra_a3500.json" if serie == "a3500" else "bcra_tasa.json"), None
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

    def _obtener(self, falso, elegidos=("dolar", "riesgo_pais", "reservas"), ahora=utiles.MIERCOLES):
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

    def test_otros_dolares_con_formato_grupo_y_fuente(self):
        datos = self._obtener(_fuentes(), elegidos=("dolar", "dolar_otros"))
        por_clave = self._por_clave(datos)
        esperado = {
            "dolar_mayorista": "venta $ 1.010,00 (compra $ 990,00)",
            "dolar_tarjeta": "venta $ 1.500,50 (compra $ 1.300,50)",
            "dolar_cripto": "venta $ 1.177,74 (compra $ 1.149,06)",
        }
        for clave, valor in esperado.items():
            with self.subTest(clave=clave):
                self.assertEqual(por_clave[clave]["valor"], valor)
                self.assertEqual(por_clave[clave]["grupo"], "dolar_otros")
                self.assertEqual(por_clave[clave]["fecha"], "17/11/2026 12:00")
                self.assertIn("DolarApi", por_clave[clave]["fuente"])
        self.assertEqual(por_clave["dolar_oficial"]["grupo"], "dolar")
        self.assertNotIn("brecha_mayorista", por_clave)

    def test_sin_dolar_otros_en_elegidos_no_trae_los_tres(self):
        claves = [i["clave"] for i in self._obtener(_fuentes(), elegidos=("dolar",))["indicadores"]]
        for clave in ("dolar_mayorista", "dolar_tarjeta", "dolar_cripto"):
            self.assertNotIn(clave, claves)

    def test_solo_otros_dolares_no_trae_los_dolares_de_siempre(self):
        claves = [i["clave"] for i in self._obtener(_fuentes(), elegidos=("dolar_otros",))["indicadores"]]
        self.assertEqual(claves, ["dolar_mayorista", "dolar_tarjeta", "dolar_cripto", "dolar_a3500"])

    def test_si_falta_una_casa_queda_sin_dato_y_las_otras_siguen(self):
        falso = _fuentes(filtro_dolar=lambda filas: [f for f in filas if f["casa"] != "cripto"])
        por_clave = self._por_clave(self._obtener(falso, elegidos=("dolar", "dolar_otros")))
        self.assertIsNone(por_clave["dolar_cripto"]["valor"])
        self.assertIsNotNone(por_clave["dolar_mayorista"]["valor"])
        self.assertIsNotNone(por_clave["dolar_tarjeta"]["valor"])

    def test_casa_sin_fecha_queda_sin_dato(self):
        def sin_fecha(filas):
            return [dict(f, fechaActualizacion=None) if f["casa"] == "tarjeta" else f for f in filas]
        por_clave = self._por_clave(self._obtener(_fuentes(filtro_dolar=sin_fecha), elegidos=("dolar_otros",)))
        self.assertIsNone(por_clave["dolar_tarjeta"]["valor"])
        self.assertIsNotNone(por_clave["dolar_cripto"]["valor"])

    def test_una_sola_consulta_a_dolarapi(self):
        falso = _fuentes()
        self._obtener(falso, elegidos=("dolar", "dolar_otros"))
        self.assertEqual(falso.llamadas.count(indicadores.URL_DOLARAPI), 1)

    def test_otros_dolares_desactualizados_con_ahora_fijo(self):
        datos = self._obtener(_fuentes(), elegidos=("dolar_otros",), ahora=utiles.MIERCOLES + timedelta(days=2))
        self.assertTrue(self._por_clave(datos)["dolar_cripto"]["desactualizado"])

    def test_solo_trae_lo_que_eligio_la_persona(self):
        datos = self._obtener(_fuentes(), elegidos=("riesgo_pais",))
        claves = [i["clave"] for i in datos["indicadores"]]
        self.assertEqual(claves, ["riesgo_pais"])  # sin "reservas" tildada no se trae


class SeriesDelBCRA(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.copia = os.path.join(carpeta.name, "indicadores.json")

    def _obtener(self, falso, elegidos, ahora=utiles.MIERCOLES):
        with mock.patch.object(indicadores, "_pedir_json", falso):
            return indicadores.obtener(self.copia, list(elegidos), ahora=ahora)

    @staticmethod
    def _por_clave(datos):
        return {i["clave"]: i for i in datos["indicadores"]}

    def test_sin_reservas_tasas_ni_otros_dolares_no_hay_pedidos_al_bcra(self):
        falso = _fuentes()
        self._obtener(falso, ("dolar", "riesgo_pais"))
        self.assertEqual([u for u in falso.llamadas if "bcra" in u], [])

    def test_reservas_solo_si_estan_elegidas(self):
        falso = _fuentes()
        datos = self._obtener(falso, ("reservas",))
        self.assertEqual([i["clave"] for i in datos["indicadores"]], ["reservas"])
        self.assertEqual(falso.llamadas, [_url_bcra("reservas")])

    def test_tasas_con_formato_tna_fecha_y_fuente(self):
        falso = _fuentes()
        datos = self._obtener(falso, ("tasas",))
        self.assertEqual([i["clave"] for i in datos["indicadores"]], ["badlar", "tamar", "plazo_fijo_30"])
        badlar = self._por_clave(datos)["badlar"]
        self.assertEqual(badlar["valor"], "32,50 % TNA")  # la fila de fecha más reciente, aunque venga desordenada
        self.assertEqual(badlar["fecha"], "17/11/2026")
        self.assertEqual(badlar["grupo"], "tasas")
        self.assertIn("BCRA", badlar["fuente"])
        self.assertEqual(self._por_clave(datos)["plazo_fijo_30"]["nombre"], "Plazo fijo a 30 días")
        self.assertEqual(len(falso.llamadas), 3)

    def test_a3500_dentro_de_otros_dolares(self):
        a3500 = self._por_clave(self._obtener(_fuentes(), ("dolar_otros",)))["dolar_a3500"]
        self.assertEqual(a3500["valor"], "$ 1.234,50")
        self.assertEqual(a3500["grupo"], "dolar_otros")
        self.assertEqual(a3500["nombre"], "Dólar A3500 (referencia BCRA)")

    def test_maximo_cinco_pedidos_al_bcra(self):
        falso = _fuentes()
        self._obtener(falso, ("dolar", "dolar_otros", "riesgo_pais", "reservas", "tasas"))
        self.assertEqual(len([u for u in falso.llamadas if "bcra" in u]), 5)

    def test_serie_vacia_o_con_basura_queda_sin_dato(self):
        malas = {
            "badlar": {"results": [{"detalle": []}]},
            "tamar": {"results": [{"detalle": [{"fecha": "2026-11-17", "valor": "no es número"}, {"fecha": "ayer", "valor": 1}]}]},
            "plazo_fijo_30": {"status": 200},
        }
        datos = self._obtener(_fuentes(bcra=malas), ("tasas",))
        for i in datos["indicadores"]:
            self.assertIsNone(i["valor"])

    def test_fecha_futura_es_sin_dato(self):
        futura = {"results": [{"detalle": [{"fecha": "2026-11-30", "valor": 20.0}]}]}
        datos = self._obtener(_fuentes(bcra={"badlar": futura}), ("tasas",))
        self.assertIsNone(self._por_clave(datos)["badlar"]["valor"])
        self.assertIsNotNone(self._por_clave(datos)["tamar"]["valor"])

    def test_dato_viejo_se_muestra_con_su_fecha_y_desactualizado(self):
        datos = self._obtener(_fuentes(), ("tasas",), ahora=utiles.MIERCOLES + timedelta(days=2))
        badlar = self._por_clave(datos)["badlar"]
        self.assertEqual(badlar["fecha"], "17/11/2026")
        self.assertTrue(badlar["desactualizado"])
        self.assertTrue(any("BADLAR" in a and "desactualizado" in a for a in datos["avisos"]))

    def test_si_fallan_varias_series_hay_un_solo_aviso_y_las_otras_siguen(self):
        caidas = {"badlar": (None, "respondió con error HTTP 500"), "tamar": (None, "devolvió algo que no se pudo leer")}
        datos = self._obtener(_fuentes(bcra=caidas), ("tasas",))
        por_clave = self._por_clave(datos)
        self.assertIsNone(por_clave["badlar"]["valor"])
        self.assertIsNone(por_clave["tamar"]["valor"])
        self.assertEqual(por_clave["plazo_fijo_30"]["valor"], "32,50 % TNA")
        avisos = [a for a in datos["avisos"] if "BCRA" in a]
        self.assertEqual(len(avisos), 1)
        self.assertIn("No se pudo consultar BCRA", avisos[0])


class InflacionYUva(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.copia = os.path.join(carpeta.name, "indicadores.json")

    def _obtener(self, falso, elegidos=("inflacion",), ahora=utiles.MIERCOLES):
        with mock.patch.object(indicadores, "_pedir_json", falso):
            return indicadores.obtener(self.copia, list(elegidos), ahora=ahora)

    @staticmethod
    def _por_clave(datos):
        return {i["clave"]: i for i in datos["indicadores"]}

    def test_formato_fecha_grupo_y_fuente(self):
        datos = self._obtener(_fuentes())
        self.assertEqual([i["clave"] for i in datos["indicadores"]], ["inflacion", "inflacion_interanual", "uva"])
        por_clave = self._por_clave(datos)
        self.assertEqual(por_clave["inflacion"]["valor"], "2,20 % mensual")
        self.assertEqual(por_clave["inflacion"]["fecha"], "octubre 2026")
        self.assertEqual(por_clave["inflacion_interanual"]["valor"], "33,10 % interanual")
        self.assertEqual(por_clave["inflacion_interanual"]["fecha"], "octubre 2026")
        self.assertEqual(por_clave["uva"]["valor"], "$ 2.201,80")  # la fila del 18/11: la del 19 y la del 25 son futuras
        self.assertEqual(por_clave["uva"]["fecha"], "18/11/2026")
        for i in datos["indicadores"]:
            self.assertEqual(i["grupo"], "inflacion")
            self.assertIn("ArgentinaDatos", i["fuente"])
            self.assertFalse(i["desactualizado"])
        self.assertEqual(datos["avisos"], [])

    def test_septiembre_en_noviembre_esta_desactualizado_y_octubre_no(self):
        viejo = [{"fecha": "2026-09-30", "valor": 1.9}]
        datos = self._obtener(_fuentes(ad={"inflacion": viejo}))
        por_clave = self._por_clave(datos)
        self.assertTrue(por_clave["inflacion"]["desactualizado"])
        self.assertEqual(por_clave["inflacion"]["fecha"], "septiembre 2026")
        self.assertFalse(por_clave["inflacion_interanual"]["desactualizado"])
        self.assertIn("Inflación mensual: el dato es de septiembre 2026 y está desactualizado.", datos["avisos"])

    def test_desactualizado_a_uno_dos_y_tres_meses(self):
        for fecha, esperado in (("2026-10-31", False), ("2026-09-30", True), ("2026-08-31", True)):
            os.path.exists(self.copia) and os.remove(self.copia)  # sin copia vigente de la vuelta anterior
            datos = self._obtener(_fuentes(ad={"inflacion": [{"fecha": fecha, "valor": 2.0}]}),
                                  ahora=utiles.MIERCOLES)
            self.assertEqual(self._por_clave(datos)["inflacion"]["desactualizado"], esperado, fecha)

    def test_cruce_de_anio(self):
        enero = utiles.MIERCOLES.replace(year=2027, month=1, day=13)
        datos = self._obtener(_fuentes(ad={"inflacion": [{"fecha": "2026-11-30", "valor": 2.0}]}), ahora=enero)
        self.assertTrue(self._por_clave(datos)["inflacion"]["desactualizado"])

    def test_la_uva_usa_la_regla_de_un_dia_habil(self):
        datos = self._obtener(_fuentes(), ahora=utiles.MIERCOLES + timedelta(days=5))
        self.assertTrue(self._por_clave(datos)["uva"]["desactualizado"])

    def test_fecha_futura_valor_no_numerico_y_forma_rara_son_sin_dato(self):
        malas = {
            "inflacion": [{"fecha": "2026-11-30", "valor": 2.0}],
            "inflacion_interanual": [{"fecha": "2026-10-31", "valor": "33,1"}],
            "uva": {"status": 200},
        }
        for i in self._obtener(_fuentes(ad=malas))["indicadores"]:
            self.assertIsNone(i["valor"])

    def test_una_falla_no_afecta_a_las_otras_y_hay_un_solo_aviso(self):
        caidas = {"inflacion": (None, "respondió con error HTTP 500"), "uva": (None, "no se pudo conectar")}
        datos = self._obtener(_fuentes(ad=caidas))
        por_clave = self._por_clave(datos)
        self.assertIsNone(por_clave["inflacion"]["valor"])
        self.assertIsNone(por_clave["uva"]["valor"])
        self.assertEqual(por_clave["inflacion_interanual"]["valor"], "33,10 % interanual")
        avisos = [a for a in datos["avisos"] if "ArgentinaDatos" in a]
        self.assertEqual(len(avisos), 1)

    def test_un_pedido_por_serie_y_ninguno_si_no_esta_tildada(self):
        falso = _fuentes()
        self._obtener(falso)
        self.assertEqual(falso.llamadas, [config.URL_INFLACION, config.URL_INFLACION_INTERANUAL, config.URL_UVA])
        sin = _fuentes()
        self._obtener(sin, ("riesgo_pais",))
        self.assertEqual([u for u in sin.llamadas if u in (config.URL_INFLACION, config.URL_INFLACION_INTERANUAL, config.URL_UVA)], [])

    def test_copia_vigente_no_consulta_y_vencida_si(self):
        self._obtener(_fuentes())
        vigente = _fuentes()
        self._obtener(vigente, ahora=utiles.MIERCOLES + timedelta(hours=2, minutes=59))
        self.assertEqual(vigente.llamadas, [])
        vencida = _fuentes()
        self._obtener(vencida, ahora=utiles.MIERCOLES + timedelta(hours=3, minutes=1))
        self.assertEqual(len(vencida.llamadas), 3)

    def test_consulta_fallida_no_queda_vigente(self):
        self._obtener(_fuentes(ad={"uva": (None, "no se pudo conectar")}))
        # La copia de la UVA guarda la falla con su hora: la consulta fallida no se tiene por dato vigente.
        otra = _fuentes()
        datos = self._obtener(otra, ahora=utiles.MIERCOLES + timedelta(hours=3))
        self.assertIn(config.URL_UVA, otra.llamadas)
        self.assertIsNotNone(self._por_clave(datos)["uva"]["valor"])

    def test_la_copia_tiene_una_clave_por_serie(self):
        self._obtener(_fuentes())
        copia = utilidades.leer_copia(self.copia)
        for clave in ("inflacion", "inflacion_interanual", "uva"):
            self.assertIn(clave, copia)


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
