"""Tests de gustos.py: votos, validación, archivo roto o ausente y últimos 30 votos."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from micafe.almacen import gustos
from tests import utiles

NOTA = {"tipo": "nota", "clave": "https://infobae.test/1", "voto": "me_gusta",
        "titulo": "Una  nota", "medio": "Infobae", "seccion": "Política"}
TEMA = {"tipo": "tema", "clave": "Deportes", "voto": "no_me_gusta"}


def _voto(n):
    """Voto guardado número `n`: cuanto más grande, más nuevo."""
    momento = datetime(2026, 11, 1, 10, 0, tzinfo=utiles.ZONA) + timedelta(minutes=n)
    return {"tipo": "nota", "clave": f"https://x.test/{n}", "voto": "me_gusta", "titulo": f"Nota {n}",
            "medio": "Medio", "seccion": "Política", "votado_en": momento.isoformat(timespec="seconds")}


class GustosEnDisco(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = os.path.join(carpeta.name, "datos", "gustos.json")

    def _escribir_crudo(self, contenido):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido if isinstance(contenido, str) else json.dumps(contenido))

    def test_sin_archivo_no_hay_votos_ni_aviso(self):
        self.assertEqual(gustos.leer(self.ruta), ([], None))

    def test_guardar_y_leer_un_voto_de_nota_y_uno_de_tema(self):
        gustos.guardar(self.ruta, NOTA)
        votos, errores = gustos.guardar(self.ruta, TEMA)
        self.assertEqual(errores, [])
        self.assertEqual(len(votos), 2)
        leidos, aviso = gustos.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual(leidos[0]["titulo"], "Una nota")  # espacios limpiados
        self.assertEqual(leidos[1]["clave"], "Deportes")
        self.assertIn("-03:00", leidos[1]["votado_en"])  # hora de Buenos Aires

    def test_votar_de_nuevo_cambia_el_voto_y_no_duplica(self):
        gustos.guardar(self.ruta, NOTA)
        votos, _ = gustos.guardar(self.ruta, {**NOTA, "voto": "no_me_gusta"})
        self.assertEqual(len(votos), 1)
        self.assertEqual(votos[0]["voto"], "no_me_gusta")

    def test_voto_none_quita_el_voto(self):
        gustos.guardar(self.ruta, NOTA)
        votos, errores = gustos.guardar(self.ruta, {"tipo": "nota", "clave": NOTA["clave"], "voto": None})
        self.assertEqual((votos, errores), ([], []))
        self.assertEqual(gustos.leer(self.ruta), ([], None))

    def test_pedido_invalido_no_escribe_nada(self):
        casos = [
            "no es un objeto",
            {"tipo": "nota", "clave": "no-es-link", "voto": "me_gusta", "titulo": "t", "medio": "m", "seccion": "s"},
            {"tipo": "tema", "clave": "Farándula", "voto": "me_gusta"},
            {"tipo": "otro", "clave": "x", "voto": "me_gusta"},
            {"tipo": "tema", "clave": "Deportes", "voto": "quizás"},
            {"tipo": "nota", "clave": "https://a.test/1", "voto": "me_gusta"},  # falta el título
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                votos, errores = gustos.guardar(self.ruta, caso)
                self.assertIsNone(votos)
                self.assertTrue(errores)
        self.assertFalse(os.path.exists(self.ruta))

    def test_archivo_roto_se_sigue_sin_gustos_y_avisa(self):
        self._escribir_crudo("{roto")
        votos, aviso = gustos.leer(self.ruta)
        self.assertEqual(votos, [])
        self.assertIn("roto", aviso)

    def test_archivo_con_otra_forma_avisa(self):
        self._escribir_crudo({"otra": "cosa"})
        votos, aviso = gustos.leer(self.ruta)
        self.assertEqual(votos, [])
        self.assertIn("formato", aviso)

    def test_votos_ilegibles_se_ignoran_y_los_buenos_quedan(self):
        self._escribir_crudo({"votos": [_voto(1), {"tipo": "tema", "clave": "Deportes"}, "basura"]})
        votos, aviso = gustos.leer(self.ruta)
        self.assertEqual([v["clave"] for v in votos], ["https://x.test/1"])
        self.assertIn("se ignoraron", aviso)

    def test_guardar_sobre_un_archivo_roto_lo_reemplaza(self):
        self._escribir_crudo("{roto")
        votos, errores = gustos.guardar(self.ruta, TEMA)
        self.assertEqual(errores, [])
        self.assertEqual(len(votos), 1)
        self.assertEqual(len(gustos.leer(self.ruta)[0]), 1)


class UltimosVotos(unittest.TestCase):
    def test_solo_los_ultimos_30_del_mas_nuevo_al_mas_viejo(self):
        votos = [_voto(n) for n in range(45)]
        ultimos = gustos.ultimos(votos)
        self.assertEqual(len(ultimos), 30)
        self.assertEqual(ultimos[0]["clave"], "https://x.test/44")
        self.assertEqual(ultimos[-1]["clave"], "https://x.test/15")

    def test_lineas_para_el_pedido(self):
        votos = [{**_voto(1), "voto": "no_me_gusta"},
                 {"tipo": "tema", "clave": "Deportes", "voto": "me_gusta",
                  "votado_en": "2026-11-17T10:00:00-03:00"}]
        lineas = gustos.lineas_para_pedido(votos)
        self.assertEqual(lineas, [
            "- Tema Deportes: me gusta.",  # el más nuevo primero
            "- Nota «Nota 1» (Medio, Política): no me gusta.",
        ])

    def test_sin_votos_no_hay_lineas(self):
        self.assertEqual(gustos.lineas_para_pedido([]), [])

    def test_el_pedido_nunca_pasa_de_30_lineas(self):
        self.assertEqual(len(gustos.lineas_para_pedido([_voto(n) for n in range(50)])), 30)


if __name__ == "__main__":
    unittest.main()
