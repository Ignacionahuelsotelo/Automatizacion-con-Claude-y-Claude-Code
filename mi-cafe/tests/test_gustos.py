"""Tests de gustos.py: votos, validación, archivo roto o ausente y reinicio."""

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

    def test_se_pueden_votar_los_temas_nuevos(self):
        for tema in ("Sociedad", "Salud y Ciencia", "Espectáculos y Cultura"):
            votos, errores = gustos.guardar(self.ruta, {"tipo": "tema", "clave": tema, "voto": "me_gusta"})
            self.assertEqual(errores, [], tema)
        self.assertEqual([v["clave"] for v in votos], ["Sociedad", "Salud y Ciencia", "Espectáculos y Cultura"])

    def test_se_puede_votar_el_tema_internacional(self):
        votos, errores = gustos.guardar(self.ruta, {"tipo": "tema", "clave": "Internacional", "voto": "me_gusta"})
        self.assertEqual(errores, [])
        self.assertEqual(votos[0]["clave"], "Internacional")

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


class Reinicio(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = os.path.join(carpeta.name, "gustos.json")

    def test_un_archivo_viejo_sin_reiniciado_en_se_lee_igual(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"votos": [_voto(1)]}, archivo)
        self.assertEqual(gustos.leer(self.ruta), ([_voto(1)], None))
        self.assertIsNone(gustos.leer_reinicio(self.ruta))

    def test_sin_archivo_no_hay_reinicio(self):
        self.assertIsNone(gustos.leer_reinicio(self.ruta))

    def test_reiniciar_guarda_la_fecha_y_no_borra_votos(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"votos": [_voto(1), _voto(2)]}, archivo)
        ahora = datetime(2026, 11, 20, 9, 0, tzinfo=utiles.ZONA)
        self.assertEqual(gustos.reiniciar(self.ruta, ahora), "2026-11-20T09:00:00-03:00")
        self.assertEqual(gustos.leer_reinicio(self.ruta), "2026-11-20T09:00:00-03:00")
        self.assertEqual(len(gustos.leer(self.ruta)[0]), 2)

    def test_un_voto_nuevo_conserva_el_reinicio(self):
        gustos.reiniciar(self.ruta, datetime(2026, 11, 20, 9, 0, tzinfo=utiles.ZONA))
        gustos.guardar(self.ruta, NOTA)
        self.assertEqual(gustos.leer_reinicio(self.ruta), "2026-11-20T09:00:00-03:00")
        self.assertEqual(len(gustos.leer(self.ruta)[0]), 1)

    def test_reiniciado_en_ilegible_se_ignora(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"votos": [], "reiniciado_en": "ayer"}, archivo)
        self.assertIsNone(gustos.leer_reinicio(self.ruta))

    def test_el_historial_no_se_recorta(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"votos": [_voto(n) for n in range(50)]}, archivo)
        self.assertEqual(len(gustos.leer(self.ruta)[0]), 50)


if __name__ == "__main__":
    unittest.main()
