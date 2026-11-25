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
        self.assertEqual((config.CANDIDATAS_POR_MEDIO_Y_SECCION, config.CANDIDATAS_POR_MEDIO_Y_SECCION_LUNES), (8, 13))
        self.assertEqual((config.MINIMO_PALABRAS, config.MAXIMO_PALABRAS), (550, 650))
        self.assertEqual(config.NOMBRE_MERVAL, "MSCI Merval")
        self.assertEqual(config.HILOS_FEEDS, 6)
        self.assertIsInstance(config.HILOS_FEEDS, int)
        self.assertGreater(config.HILOS_FEEDS, 0)


class FuentesRSS(unittest.TestCase):
    def test_temas_en_orden_fijo(self):
        # Policiales quedó afuera (spec 44): solo Infobae tiene un feed válido.
        self.assertEqual(config.TEMAS, ["Política", "Economía", "Internacional", "Sociedad", "Deportes",
                                        "Salud y Ciencia", "Espectáculos y Cultura", "Tecnología"])
        self.assertEqual(config.SECCIONES, config.TEMAS)
        self.assertEqual(config.TEMAS_POR_DEFECTO,
                         ["Política", "Economía", "Internacional", "Deportes", "Tecnología"])
        self.assertTrue(set(config.TEMAS_POR_DEFECTO) <= set(config.TEMAS))

    def test_sinonimos_y_categorias_apuntan_a_temas_que_existen(self):
        self.assertTrue(set(config.TEMA_DE_CLAVE_SINONIMO.values()) <= set(config.TEMAS))
        self.assertTrue(set(config.TEMA_DE_CLAVE_SINONIMO) <= set(config.SINONIMOS_TEMAS))
        self.assertTrue(set(config.CATEGORIAS_A_TEMA.values()) <= set(config.TEMAS))

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


class Subtemas(unittest.TestCase):
    def test_orden_fijo_otros_al_final_y_palabras_clave(self):
        nombres = list(config.SUBTEMAS)
        self.assertEqual(nombres, ["Fútbol argentino", "Fútbol internacional", "Tenis", "Básquet",
                                   "Automovilismo", "Otros"])
        self.assertEqual(len(nombres), len(set(nombres)))
        self.assertEqual(config.SUBTEMAS["Otros"], [])
        self.assertTrue(all(config.SUBTEMAS[n] for n in nombres[:-1]))

    def test_cada_subtema_de_una_fuente_esta_en_subtemas_y_es_de_deportes(self):
        for fuente in config.FUENTES_RSS:
            if "subtema" in fuente:
                self.assertIn(fuente["subtema"], config.SUBTEMAS)
                self.assertEqual(fuente["seccion"], "Deportes")

    def test_ole_tiene_feeds_de_deportes(self):
        self.assertTrue([f for f in config.FUENTES_RSS if f["medio"] == "Olé"])


class IdsDelBCRA(unittest.TestCase):
    def test_ids_enteros_positivos_y_sin_repetir(self):
        ids = list(config.BCRA_IDS.values())
        self.assertTrue(all(isinstance(i, int) and not isinstance(i, bool) and i > 0 for i in ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(config.BCRA_IDS), {"reservas", "badlar", "tamar", "plazo_fijo_30", "a3500"})

    def test_la_plantilla_de_url_tiene_el_id(self):
        self.assertIn("{id}", config.URL_BCRA_VARIABLE)
        self.assertTrue(config.URL_BCRA_VARIABLE.startswith("https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/"))


class SeriesDeArgentinaDatos(unittest.TestCase):
    def test_las_urls_son_https_y_distintas(self):
        urls = [config.URL_INFLACION, config.URL_INFLACION_INTERANUAL, config.URL_UVA]
        self.assertTrue(all(u.startswith("https://api.argentinadatos.com/") for u in urls))
        self.assertEqual(len(urls), len(set(urls)))

    def test_la_clave_de_copia_de_cada_serie_es_unica(self):
        from micafe.fuentes import indicadores
        claves = ["dolares", "riesgo_pais", "inflacion", "inflacion_interanual", "uva"] + [f"bcra_{s}" for s in config.BCRA_IDS]
        self.assertEqual(len(claves), len(set(claves)))
        self.assertEqual(set(indicadores.CLAVES_MENSUALES), {"inflacion", "inflacion_interanual"})


class PreferenciasV2(unittest.TestCase):
    def test_topes_y_pesos_existen_y_son_positivos(self):
        for nombre in ("MAXIMO_PALABRAS_PREFERENCIA", "MAXIMO_CARACTERES_PALABRA", "PESO_MEDIO_PREFERIDO",
                       "PESO_PALABRA_SEGUIR", "PESO_PALABRA_EVITAR", "PESO_SUBTEMA_ELEGIDO", "PESO_SUBTEMA_NO_ELEGIDO",
                       "MAXIMO_PUNTAJE_PREFERENCIAS", "PESO_PRIORIDAD_ALTA", "PESO_PRIORIDAD_BAJA"):
            with self.subTest(nombre):
                self.assertGreater(getattr(config, nombre), 0)
        self.assertEqual((config.MAXIMO_PALABRAS_PREFERENCIA, config.MAXIMO_CARACTERES_PALABRA), (20, 40))

    def test_prioridades_del_plan(self):
        self.assertEqual(config.PRIORIDADES_TEMA, ["alta", "normal", "baja"])
        self.assertEqual((config.PESO_PRIORIDAD_ALTA, config.PESO_PRIORIDAD_BAJA), (1.5, 0.5))

    def test_las_preferencias_pesan_menos_que_el_pedido_y_mas_que_el_tope_del_perfil(self):
        self.assertLess(config.MAXIMO_PUNTAJE_PREFERENCIAS, min(config.PESOS_PUNTAJE["titulo"], config.PESOS_PUNTAJE["bajada"],
                                                              config.PESOS_PUNTAJE["categoria"]))
        self.assertGreater(config.MAXIMO_PUNTAJE_PREFERENCIAS, config.MAXIMO_PUNTAJE_PERFIL)
        suma = (config.PESO_MEDIO_PREFERIDO + config.PESO_PALABRA_SEGUIR + config.PESO_SUBTEMA_ELEGIDO)
        self.assertGreater(suma, config.MAXIMO_PUNTAJE_PREFERENCIAS)  # el acotado sirve de algo

    def test_no_hay_opcion_de_largo(self):
        self.assertFalse([n for n in dir(config) if "LARGO" in n.upper() and "PREFERENCIA" in n.upper()])
