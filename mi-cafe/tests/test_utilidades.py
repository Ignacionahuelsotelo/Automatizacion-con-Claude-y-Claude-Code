"""Tests de utilidades.py: fechas como mes."""

import unittest
from datetime import date, datetime

from micafe.config import ZONA
from micafe.fuentes import utilidades


class MostrarMes(unittest.TestCase):
    def test_los_doce_meses(self):
        esperados = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                     "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        for numero, mes in enumerate(esperados, start=1):
            self.assertEqual(utilidades.mostrar_mes(date(2026, numero, 1)), f"{mes} 2026")

    def test_acepta_datetime(self):
        self.assertEqual(utilidades.mostrar_mes(datetime(2026, 10, 31, 12, 0, tzinfo=ZONA)), "octubre 2026")

    def test_fecha_invalida_devuelve_none(self):
        for malo in (None, "2026-10-31", 5):
            self.assertIsNone(utilidades.mostrar_mes(malo))

    def test_meses_entre(self):
        self.assertEqual(utilidades.meses_entre(date(2026, 9, 30), date(2026, 11, 24)), 2)
        self.assertEqual(utilidades.meses_entre(date(2026, 11, 30), date(2027, 1, 13)), 2)


if __name__ == "__main__":
    unittest.main()
