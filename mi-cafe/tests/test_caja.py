"""Tests de caja.py: validación del pedido y respuesta con `claude` simulado."""

import json
import os
import tempfile
import unittest
from unittest import mock

from micafe.dominio import caja
from micafe.dominio import resumen
from tests import utiles

LINK = "https://infobae.test/1"
NOTA = ["Una nota sobre el dólar", "El oficial cerró a 1.234,50 pesos.", LINK]
PEDIDO = {"fecha": "2026-11-17", "link": LINK, "pregunta": "  ¿Qué pasó   con el dólar? "}


class ValidarPedido(unittest.TestCase):
    def test_pedido_valido_limpia_los_espacios_de_la_pregunta(self):
        pedido, errores = caja.validar_pedido(PEDIDO)
        self.assertEqual(errores, [])
        self.assertEqual(pedido, {"fecha": "2026-11-17", "link": LINK, "pregunta": "¿Qué pasó con el dólar?"})

    def test_no_es_un_objeto(self):
        pedido, errores = caja.validar_pedido(["x"])
        self.assertIsNone(pedido)
        self.assertEqual(len(errores), 1)

    def test_fecha_link_y_pregunta_invalidos(self):
        _, errores = caja.validar_pedido({"fecha": "17/11/2026", "link": "ftp://x", "pregunta": "   "})
        self.assertEqual(len(errores), 3)

    def test_pregunta_de_500_pasa_y_de_501_no(self):
        self.assertEqual(caja.validar_pedido({**PEDIDO, "pregunta": "a" * 500})[1], [])
        _, errores = caja.validar_pedido({**PEDIDO, "pregunta": "a" * 501})
        self.assertTrue(any("muy larga" in e for e in errores))


class Cifras(unittest.TestCase):
    def test_ignora_separadores(self):
        self.assertEqual(caja.cifras("1.234,50 y 7"), {"123450", "7"})


class NotaDelResumen(unittest.TestCase):
    def test_encuentra_el_bloque_de_la_nota_por_su_link(self):
        with tempfile.TemporaryDirectory() as carpeta:
            texto = "Lo más importante de hoy: algo.\n\nPolítica\n" + "\n".join(NOTA) + "\n\nLo que viene hoy: nada."
            with open(os.path.join(carpeta, "2026-11-17.json"), "w", encoding="utf-8") as archivo:
                json.dump({"texto": texto}, archivo)
            self.assertEqual(caja.nota_del_resumen("2026-11-17", LINK, carpeta), NOTA)
            self.assertIsNone(caja.nota_del_resumen("2026-11-17", "https://otro.test/x", carpeta))
            self.assertIsNone(caja.nota_del_resumen("2026-11-16", LINK, carpeta))  # no hay resumen ese día


class Responder(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.skill = os.path.join(carpeta.name, "SKILL.md")
        with open(self.skill, "w", encoding="utf-8") as archivo:
            archivo.write("---\nname: x\n---\nREGLAS DE LA CAJA")

    def _responder(self, datos=PEDIDO, nota=NOTA, claude="Cerró a 1.234,50 pesos."):
        with mock.patch.object(caja, "nota_del_resumen", return_value=nota), \
                mock.patch("micafe.dominio.resumen.ejecutar_claude", return_value=claude) as ejecutar:
            return caja.responder(datos, ruta_skill=self.skill), ejecutar

    def test_responde_con_claude_simulado_y_le_pasa_solo_la_nota_y_la_pregunta(self):
        respuesta, ejecutar = self._responder()
        self.assertEqual(respuesta, {"respuesta": "Cerró a 1.234,50 pesos.", "link": LINK})
        pedido = ejecutar.call_args.args[0]
        self.assertIn("REGLAS DE LA CAJA", pedido)
        self.assertIn("El oficial cerró a 1.234,50 pesos.", pedido)
        self.assertIn("¿Qué pasó con el dólar?", pedido)

    def test_pedido_invalido_es_400_y_no_llama_a_claude(self):
        with mock.patch("micafe.dominio.resumen.ejecutar_claude") as ejecutar:
            with self.assertRaises(resumen.ErrorResumen) as contexto:
                caja.responder({"fecha": "mal"}, ruta_skill=self.skill)
        ejecutar.assert_not_called()
        self.assertEqual(contexto.exception.codigo, 400)

    def test_nota_que_no_esta_en_el_resumen_es_404(self):
        with mock.patch.object(caja, "nota_del_resumen", return_value=None):
            with self.assertRaises(resumen.ErrorResumen) as contexto:
                caja.responder(PEDIDO, ruta_skill=self.skill)
        self.assertEqual(contexto.exception.codigo, 404)

    def test_respuesta_con_cifras_que_no_estan_en_la_nota_no_se_muestra(self):
        with self.assertRaises(resumen.ErrorResumen) as contexto:
            self._responder(claude="Cerró a 1.500,00 pesos.")
        self.assertIn("cifras que no están en la nota", contexto.exception.mensaje)

    def test_errores_de_claude_se_propagan(self):
        with mock.patch.object(caja, "nota_del_resumen", return_value=NOTA), \
                mock.patch("micafe.dominio.resumen.ejecutar_claude", side_effect=resumen.ErrorResumen("tardó", codigo=504)):
            with self.assertRaises(resumen.ErrorResumen) as contexto:
                caja.responder(PEDIDO, ruta_skill=self.skill)
        self.assertEqual(contexto.exception.codigo, 504)

    def test_skill_ausente_avisa(self):
        with mock.patch.object(caja, "nota_del_resumen", return_value=NOTA):
            with self.assertRaises(resumen.ErrorResumen) as contexto:
                caja.responder(PEDIDO, ruta_skill="/no/existe/SKILL.md")
        self.assertIn("No se pudo leer la skill", contexto.exception.mensaje)


if __name__ == "__main__":
    unittest.main()
