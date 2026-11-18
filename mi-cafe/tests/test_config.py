"""Tests de micafe/config.py: rutas esperadas, puerto fijo y MICAFE_DATOS."""

import os
import subprocess
import sys
import tempfile
import unittest

from micafe import config

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigPorDefecto(unittest.TestCase):
    def test_rutas_esperadas(self):
        if os.environ.get("MICAFE_DATOS"):
            self.skipTest("MICAFE_DATOS está definida en este entorno")
        self.assertEqual(config.CARPETA_PROYECTO, RAIZ)
        self.assertEqual(config.CARPETA_DATOS, os.path.join(RAIZ, "datos"))
        self.assertEqual(config.ARCHIVO_PREFERENCIAS, os.path.join(RAIZ, "datos", "preferencias.json"))
        self.assertEqual(config.ARCHIVO_GUSTOS, os.path.join(RAIZ, "datos", "gustos.json"))
        self.assertEqual(config.ARCHIVO_INDICADORES, os.path.join(RAIZ, "datos", "indicadores.json"))
        self.assertEqual(config.ARCHIVO_ACCIONES, os.path.join(RAIZ, "datos", "acciones.json"))
        self.assertEqual(config.CARPETA_RESUMENES, os.path.join(RAIZ, "datos", "resumenes"))
        self.assertEqual(config.ARCHIVO_INDEX, os.path.join(RAIZ, "micafe", "web", "estatico", "index.html"))
        self.assertTrue(os.path.isfile(config.ARCHIVO_SKILL_RESUMEN))
        self.assertTrue(os.path.isfile(config.ARCHIVO_SKILL_CORRECTOR))
        self.assertTrue(os.path.isfile(config.ARCHIVO_SKILL_PREGUNTAS))

    def test_valores_fijos(self):
        self.assertEqual((config.HOST, config.PUERTO), ("127.0.0.1", 8000))
        self.assertEqual(str(config.ZONA), "America/Argentina/Buenos_Aires")
        self.assertEqual(config.TIMEOUT_CLAUDE, 300)
        self.assertEqual((config.TOPE_POR_MEDIO, config.TOPE_POR_MEDIO_LUNES), (3, 5))
        self.assertEqual((config.CANDIDATAS_POR_MEDIO_Y_SECCION, config.CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES), (3, 5))
        self.assertEqual((config.MINIMO_PALABRAS, config.MAXIMO_PALABRAS), (550, 650))
        self.assertEqual(config.NOMBRE_MERVAL, "MSCI Merval")


class FuentesRSS(unittest.TestCase):
    def test_lista_bien_formada(self):
        for fuente in config.FUENTES_RSS:
            self.assertTrue(fuente["medio"].strip())
            self.assertIn(fuente["seccion"], config.SECCIONES)
            self.assertTrue(fuente["url"].startswith("https://"))
        urls = [f["url"] for f in config.FUENTES_RSS]
        self.assertEqual(len(urls), len(set(urls)))

    def test_cada_seccion_tiene_al_menos_dos_medios_distintos(self):
        for seccion in config.SECCIONES:
            medios = {f["medio"] for f in config.FUENTES_RSS if f["seccion"] == seccion}
            self.assertGreaterEqual(len(medios), 2, seccion)


class ConfigConVariableDeEntorno(unittest.TestCase):
    def test_micafe_datos_redirige_datos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            codigo = ("from micafe import config; "
                      "print(config.CARPETA_DATOS); print(config.ARCHIVO_PREFERENCIAS); "
                      "print(config.CARPETA_RESUMENES); print(config.PUERTO, config.HOST)")
            entorno = dict(os.environ, MICAFE_DATOS=carpeta)
            salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=entorno,
                                    capture_output=True, text=True, check=True).stdout.split("\n")
        self.assertEqual(salida[0], carpeta)
        self.assertEqual(salida[1], os.path.join(carpeta, "preferencias.json"))
        self.assertEqual(salida[2], os.path.join(carpeta, "resumenes"))
        self.assertEqual(salida[3], "8000 127.0.0.1")  # el puerto y el host no se sobrescriben


if __name__ == "__main__":
    unittest.main()
