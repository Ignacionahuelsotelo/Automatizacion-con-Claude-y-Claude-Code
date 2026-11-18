"""Todos los módulos de micafe/ se pueden importar (spec 23): atrapa errores de sintaxis o de anotaciones."""

import importlib
import pkgutil
import unittest

import micafe


class ImportacionesTest(unittest.TestCase):
    def test_se_importan_todos_los_modulos(self):
        nombres = [m.name for m in pkgutil.walk_packages(micafe.__path__, "micafe.")]
        self.assertIn("micafe.modelos", nombres)
        self.assertIn("micafe.web.servidor", nombres)
        for nombre in nombres:
            with self.subTest(modulo=nombre):
                importlib.import_module(nombre)

    def test_cada_modulo_tiene_docstring(self):
        for modulo in pkgutil.walk_packages(micafe.__path__, "micafe."):
            with self.subTest(modulo=modulo.name):
                self.assertTrue((importlib.import_module(modulo.name).__doc__ or "").strip())


if __name__ == "__main__":
    unittest.main()
