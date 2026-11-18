"""Tests del almacén JSON (spec 21): json_seguro y resumenes, con directorio temporal."""

import json
import os
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from micafe.almacen import json_seguro, resumenes
from tests import utiles


class Base(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = carpeta.name

    def escribir_crudo(self, nombre, contenido):
        with open(os.path.join(self.carpeta, nombre), "w", encoding="utf-8") as archivo:
            archivo.write(contenido if isinstance(contenido, str) else json.dumps(contenido))


class JsonSeguro(Base):
    def test_leer_archivo_que_falta_devuelve_el_valor_por_defecto(self):
        self.assertEqual(json_seguro.leer(os.path.join(self.carpeta, "no.json"), {"a": 1}),
                         ({"a": 1}, json_seguro.FALTA))

    def test_leer_archivo_roto_devuelve_el_valor_por_defecto_y_aviso(self):
        self.escribir_crudo("x.json", "{basura")
        self.assertEqual(json_seguro.leer(os.path.join(self.carpeta, "x.json"), []), ([], json_seguro.ROTO))

    def test_leer_archivo_valido(self):
        self.escribir_crudo("x.json", {"ñ": "á"})
        self.assertEqual(json_seguro.leer(os.path.join(self.carpeta, "x.json"), None), ({"ñ": "á"}, None))

    def test_escribir_crea_la_carpeta_y_no_deja_tmp(self):
        ruta = os.path.join(self.carpeta, "nueva", "x.json")
        json_seguro.escribir(ruta, {"texto": "café"})
        self.assertEqual(os.listdir(os.path.dirname(ruta)), ["x.json"])
        with open(ruta, encoding="utf-8") as archivo:
            self.assertIn("café", archivo.read())  # sin escapar, como antes

    def test_escribir_no_deja_tmp_si_falla_y_conserva_el_anterior(self):
        ruta = os.path.join(self.carpeta, "x.json")
        json_seguro.escribir(ruta, {"v": 1})
        with self.assertRaises(TypeError):
            json_seguro.escribir(ruta, {"v": object()})
        self.assertEqual(os.listdir(self.carpeta), ["x.json"])
        self.assertEqual(json_seguro.leer(ruta, None), ({"v": 1}, None))

    def test_escrituras_concurrentes_al_mismo_archivo_no_fallan(self):
        ruta = os.path.join(self.carpeta, "x.json")
        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(lambda n: json_seguro.escribir(ruta, {"v": n}), range(200)))
        datos, estado = json_seguro.leer(ruta, None)
        self.assertIsNone(estado)
        self.assertIn(datos["v"], range(200))
        self.assertEqual(os.listdir(self.carpeta), ["x.json"])

    @unittest.skipIf(os.geteuid() == 0, "root ignora los permisos")
    def test_carpeta_sin_permisos_da_oserror(self):
        os.chmod(self.carpeta, stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(os.chmod, self.carpeta, stat.S_IRWXU)
        with self.assertRaises(OSError):
            json_seguro.escribir(os.path.join(self.carpeta, "x.json"), {})


class Resumenes(Base):
    def test_guardar_escribe_solo_el_de_hoy_y_no_pisa_otros_dias(self):
        self.escribir_crudo("2026-11-17.json", {"fecha": "2026-11-17", "texto": "ayer"})
        registro = resumenes.guardar("texto", [], {"aprobado": True}, utiles.MIERCOLES, self.carpeta)
        self.assertEqual(registro["fecha"], "2026-11-18")
        self.assertEqual(sorted(os.listdir(self.carpeta)), ["2026-11-17.json", "2026-11-18.json"])
        self.assertEqual(resumenes.leer_ultimo(self.carpeta), registro)
        self.assertEqual(resumenes.leer_previos(self.carpeta, anteriores_a="2026-11-18"), ["ayer"])

    def test_guardar_escribe_pedido_solo_si_hubo_y_los_viejos_se_leen_igual(self):
        sin = resumenes.guardar("t", [], {"aprobado": True}, utiles.MIERCOLES, self.carpeta)
        self.assertNotIn("pedido", sin)
        self.assertNotIn("pedido", json_seguro.leer(os.path.join(self.carpeta, "2026-11-18.json"), None)[0])
        self.assertEqual(resumenes.leer_ultimo(self.carpeta), sin)
        con = resumenes.guardar("t", [], {"aprobado": True}, utiles.MIERCOLES, self.carpeta, pedido="más economía")
        self.assertEqual(con["pedido"], "más economía")
        self.assertEqual(resumenes.leer_ultimo(self.carpeta)["pedido"], "más economía")
        vacio = resumenes.guardar("t", [], {"aprobado": True}, utiles.MIERCOLES, self.carpeta, pedido="")
        self.assertNotIn("pedido", vacio)

    def test_leer_ultimo_sin_carpeta_es_none(self):
        self.assertIsNone(resumenes.leer_ultimo(os.path.join(self.carpeta, "no-existe")))

    def test_leer_ultimo_saltea_roto_y_otra_forma(self):
        self.escribir_crudo("2026-11-15.json", {"fecha": "2026-11-15", "texto": "sirve"})
        self.escribir_crudo("2026-11-16.json", ["otra forma"])
        self.escribir_crudo("2026-11-17.json", "{roto")
        self.escribir_crudo("2026-11-18.json", {"fecha": "2026-11-18", "texto": "  "})
        self.assertEqual(resumenes.leer_ultimo(self.carpeta)["fecha"], "2026-11-15")

    def test_leer_previos_sin_carpeta(self):
        self.assertEqual(resumenes.leer_previos(os.path.join(self.carpeta, "no-existe")), [])

    def test_leer_previos_los_ultimos_3_del_mas_nuevo_al_mas_viejo(self):
        for dia in range(10, 15):
            self.escribir_crudo(f"2026-11-{dia}.json", {"texto": f"resumen {dia}"})
        self.assertEqual(resumenes.leer_previos(self.carpeta), ["resumen 14", "resumen 13", "resumen 12"])

    def test_leer_previos_saltea_rotos_sin_texto_y_nombres_raros(self):
        self.escribir_crudo("2026-11-16.json", "{roto")
        self.escribir_crudo("2026-11-17.json", {"texto": "   "})
        self.escribir_crudo("2026-11-15.json", {"texto": "sirve"})
        self.escribir_crudo("notas.json", {"texto": "no es un resumen"})
        self.assertEqual(resumenes.leer_previos(self.carpeta), ["sirve"])


if __name__ == "__main__":
    unittest.main()
