"""Tests de preferencias.py: leer, guardar, validación y archivo roto o ausente."""

import json
import os
import tempfile
import unittest

from micafe.almacen import preferencias
from tests import utiles


class PreferenciasEnDisco(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = os.path.join(carpeta.name, "datos", "preferencias.json")

    def test_sin_archivo_usa_todo_por_defecto_sin_aviso(self):
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIsNone(aviso)
        self.assertEqual(prefs["indicadores"], ["dolar", "riesgo_pais", "acciones"])
        self.assertEqual(prefs["temas"], ["Política", "Economía", "Deportes", "Tecnología"])

    def test_guardar_crea_la_carpeta_y_leer_devuelve_lo_guardado(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["riesgo_pais"], "temas": ["Deportes"]})
        self.assertEqual(errores, [])
        self.assertEqual(preferencias.leer(self.ruta), (prefs, None))
        self.assertEqual(prefs, {"indicadores": ["riesgo_pais"], "temas": ["Deportes"]})

    def test_guardar_ordena_y_saca_repetidos(self):
        prefs, _ = preferencias.guardar(self.ruta, {"indicadores": ["acciones", "dolar", "dolar"],
                                                    "temas": ["Tecnología", "Política"]})
        self.assertEqual(prefs, {"indicadores": ["dolar", "acciones"], "temas": ["Política", "Tecnología"]})

    def test_se_puede_no_elegir_nada(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": [], "temas": []})
        self.assertEqual((prefs, errores), ({"indicadores": [], "temas": []}, []))

    def test_valor_desconocido_se_rechaza_y_no_guarda_nada(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["dolar"], "temas": ["Farándula"]})
        self.assertIsNone(prefs)
        self.assertTrue(any("Farándula" in e for e in errores))
        self.assertFalse(os.path.exists(self.ruta))

    def test_archivo_roto_usa_por_defecto_y_avisa(self):
        os.makedirs(os.path.dirname(self.ruta))
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write("{no es json")
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("roto", aviso)

    def test_archivo_con_valores_invalidos_usa_por_defecto_y_avisa(self):
        os.makedirs(os.path.dirname(self.ruta))
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"indicadores": ["bitcoin"], "temas": []}, archivo)
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("no es válido", aviso)


class Validar(unittest.TestCase):
    def test_no_es_un_objeto(self):
        for malo in (None, [], "texto", 5):
            with self.subTest(malo=malo):
                prefs, errores = preferencias.validar(malo)
                self.assertIsNone(prefs)
                self.assertTrue(errores)

    def test_faltan_claves_o_no_son_listas(self):
        _, errores = preferencias.validar({"indicadores": "dolar"})
        self.assertEqual(len(errores), 2)


if __name__ == "__main__":
    unittest.main()
