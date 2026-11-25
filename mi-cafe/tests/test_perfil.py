"""Tests de perfil.py: decaimiento, multiplicador de tema, acotado, reinicio y prioridades (spec 41)."""

import unittest
from datetime import datetime, timedelta

from micafe.dominio import perfil
from tests import utiles

HOY = datetime(2026, 11, 24, 12, 0, tzinfo=utiles.ZONA)


def voto_nota(dias=0, voto="me_gusta", titulo="Boca ganó el clásico", medio="Infobae", seccion="Deportes"):
    return {"tipo": "nota", "clave": f"https://x.test/{dias}-{titulo}", "voto": voto, "titulo": titulo,
            "medio": medio, "seccion": seccion, "votado_en": (HOY - timedelta(days=dias)).isoformat()}


def voto_tema(dias=0, voto="me_gusta", clave="Economía"):
    return {"tipo": "tema", "clave": clave, "voto": voto, "votado_en": (HOY - timedelta(days=dias)).isoformat()}


class Calculo(unittest.TestCase):
    def test_decaimiento_hoy_14_y_28_dias(self):
        for dias, esperado in ((0, 1.0), (14, 0.5), (28, 0.25)):
            p = perfil.calcular([voto_nota(dias)], HOY)
            self.assertAlmostEqual(p["medios"]["Infobae"], esperado, places=3)
            self.assertAlmostEqual(p["secciones"]["Deportes"], esperado, places=3)

    def test_un_voto_negativo_resta(self):
        p = perfil.calcular([voto_nota(0, "no_me_gusta")], HOY)
        self.assertAlmostEqual(p["medios"]["Infobae"], -1.0)

    def test_un_voto_a_tema_vale_el_triple(self):
        tema = perfil.calcular([voto_tema()], HOY)["secciones"]["Economía"]
        nota = perfil.calcular([voto_nota(seccion="Economía")], HOY)["secciones"]["Economía"]
        self.assertAlmostEqual(tema, 3 * nota)

    def test_los_terminos_del_titulo_pesan_la_mitad_y_sin_palabras_vacias(self):
        p = perfil.calcular([voto_nota()], HOY)
        self.assertAlmostEqual(p["terminos"]["boca"], 0.5)
        self.assertAlmostEqual(p["terminos"]["clasico"], 0.5)
        self.assertNotIn("el", p["terminos"])

    def test_todo_queda_entre_menos_5_y_5(self):
        votos = [voto_nota(0) for _ in range(300)] + [voto_tema(0, clave="Política") for _ in range(300)]
        p = perfil.calcular(votos, HOY)
        for grupo in ("secciones", "medios", "terminos"):
            for valor in p[grupo].values():
                self.assertLessEqual(abs(valor), 5)
        self.assertEqual(p["secciones"]["Política"], 5)
        negativo = perfil.calcular([voto_nota(0, "no_me_gusta") for _ in range(300)], HOY)
        self.assertEqual(negativo["medios"]["Infobae"], -5)

    def test_votos_futuros_ilegibles_o_mal_formados_se_ignoran(self):
        votos = [voto_nota(-2), {**voto_nota(), "votado_en": "ayer"}, {**voto_nota(), "votado_en": None},
                 {**voto_nota(), "votado_en": "2026-11-20T10:00:00"}, {**voto_nota(), "voto": "raro"}, "x"]
        self.assertEqual(perfil.calcular(votos, HOY), perfil.perfil_vacio())

    def test_reinicio_ignora_los_anteriores_y_cuenta_los_posteriores(self):
        reinicio = (HOY - timedelta(days=3)).isoformat()
        p = perfil.calcular([voto_nota(10), voto_nota(1, medio="La Nación")], HOY, reinicio)
        self.assertEqual(p["votos_contados"], 1)
        self.assertEqual(list(p["medios"]), ["La Nación"])

    def test_sin_votos_el_perfil_esta_vacio(self):
        self.assertEqual(perfil.calcular([], HOY), perfil.perfil_vacio())
        self.assertEqual(perfil.prioridades(perfil.perfil_vacio()), [])
        self.assertEqual(perfil.lineas_para_pedido(perfil.perfil_vacio()), [])


class Prioridades(unittest.TestCase):
    def test_etiquetas_con_signo_y_sin_titulos_en_el_prompt(self):
        p = perfil.calcular([voto_tema(0, clave="Economía"), voto_nota(0, "no_me_gusta", medio="Medio X", seccion="Política")], HOY)
        etiquetas = {x["etiqueta"]: x["signo"] for x in perfil.prioridades(p)}
        self.assertEqual(etiquetas["Te interesa más Economía"], 1)
        self.assertEqual(etiquetas["Poco interés en el medio Medio X"], -1)
        lineas = perfil.lineas_para_pedido(p)
        self.assertIn("- Te interesa más Economía.", lineas)
        self.assertNotIn("boca", " ".join(lineas).lower())

    def test_el_ruido_chico_no_es_prioridad_y_hay_maximo(self):
        self.assertEqual(perfil.prioridades(perfil.calcular([voto_nota(60)], HOY)), [])
        votos = [voto_nota(0, medio=f"Medio {n}") for n in range(20)]
        self.assertEqual(len(perfil.prioridades(perfil.calcular(votos, HOY), maximo=3)), 3)


if __name__ == "__main__":
    unittest.main()
