"""Tests de dominio/progreso.py: el estado del armado en memoria (spec 30)."""

import threading
import unittest

from micafe.config import ETAPAS_RESUMEN
from micafe.dominio.progreso import Progreso
from tests import utiles


def situaciones(estado):
    return [etapa["situacion"] for etapa in estado["etapas"]]


class ProgresoDePrueba(unittest.TestCase):
    def test_arranca_libre_con_todo_pendiente(self):
        estado = Progreso().instantanea()
        self.assertEqual(estado["estado"], "libre")
        self.assertEqual([e["clave"] for e in estado["etapas"]], [c for c, _ in ETAPAS_RESUMEN])
        self.assertEqual(set(situaciones(estado)), {"pendiente"})
        self.assertIsNone(estado["etapa"])
        self.assertNotIn("resultado", estado)

    def test_iniciar_pone_en_curso_con_la_hora_y_un_segundo_iniciar_es_rechazado(self):
        progreso = Progreso()
        self.assertTrue(progreso.iniciar(utiles.MIERCOLES))
        self.assertFalse(progreso.iniciar())
        estado = progreso.instantanea()
        self.assertEqual(estado["estado"], "en_curso")
        self.assertRegex(estado["inicio"], r"^\d\d/\d\d/\d{4} \d\d:\d\d$")

    def test_avanzar_marca_hechas_las_anteriores_y_en_curso_la_actual(self):
        progreso = Progreso()
        progreso.iniciar()
        progreso.avanzar("indicadores")
        self.assertEqual(situaciones(progreso.instantanea()),
                         ["hecha", "hecha", "en_curso", "pendiente", "pendiente", "pendiente"])

    def test_el_intento_queda_en_el_estado(self):
        progreso = Progreso()
        progreso.iniciar()
        progreso.avanzar("redactando", 2)
        self.assertEqual(progreso.instantanea()["intento"], 2)
        self.assertEqual(progreso.instantanea()["intentos_max"], 3)
        progreso.avanzar("corrigiendo")
        self.assertIsNone(progreso.instantanea()["intento"])

    def test_terminar_deja_listo_con_el_resultado_y_todo_hecho(self):
        progreso = Progreso()
        progreso.iniciar()
        progreso.terminar({"resumen": {"texto": "x"}, "avisos": {}})
        estado = progreso.instantanea()
        self.assertEqual(estado["estado"], "listo")
        self.assertEqual(estado["resultado"]["resumen"], {"texto": "x"})
        self.assertEqual(set(situaciones(estado)), {"hecha"})
        self.assertTrue(progreso.iniciar())  # permite otro armado

    def test_fallar_deja_fallo_con_errores_y_avisos(self):
        progreso = Progreso()
        progreso.iniciar()
        progreso.avanzar("redactando", 1)
        progreso.fallar(["Claude falló."], {"avisos": {"noticias": ["x"]}})
        estado = progreso.instantanea()
        self.assertEqual(estado["estado"], "fallo")
        self.assertEqual(estado["errores"], ["Claude falló."])
        self.assertEqual(estado["avisos"], {"noticias": ["x"]})
        self.assertNotIn("resultado", estado)
        self.assertTrue(progreso.iniciar())

    def test_la_instantanea_es_una_copia(self):
        progreso = Progreso()
        progreso.iniciar()
        progreso.instantanea()["etapas"].clear()
        self.assertEqual(len(progreso.instantanea()["etapas"]), len(ETAPAS_RESUMEN))

    def test_con_hilos_solo_uno_logra_iniciar(self):
        progreso = Progreso()
        resultados = []
        hilos = [threading.Thread(target=lambda: resultados.append(progreso.iniciar())) for _ in range(20)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        self.assertEqual(resultados.count(True), 1)


if __name__ == "__main__":
    unittest.main()
