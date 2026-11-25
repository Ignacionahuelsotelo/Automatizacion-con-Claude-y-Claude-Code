"""Tests de preferencias.py: leer, guardar, validación y archivo roto o ausente."""

import json
import os
import tempfile
import unittest

from micafe import config
from micafe.almacen import json_seguro, preferencias
from micafe.textos import normalizar_texto
from tests import utiles


class PreferenciasEnDisco(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = os.path.join(carpeta.name, "datos", "preferencias.json")

    def test_sin_archivo_usa_todo_por_defecto_sin_aviso(self):
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIsNone(aviso)
        self.assertEqual(prefs["indicadores"], ["dolar", "dolar_otros", "riesgo_pais", "reservas", "tasas", "inflacion", "acciones"])
        self.assertEqual(preferencias.temas_activos(prefs), ["Política", "Economía", "Internacional", "Deportes", "Tecnología"])
        self.assertNotIn("Sociedad", preferencias.temas_activos(prefs))  # los temas nuevos no se tildan solos (spec 44)

    def test_guardar_crea_la_carpeta_y_leer_devuelve_lo_guardado(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["riesgo_pais"], "temas": ["Deportes"]})
        self.assertEqual(errores, [])
        self.assertEqual(preferencias.leer(self.ruta), (prefs, None))
        self.assertEqual((prefs["indicadores"], preferencias.temas_activos(prefs)), (["riesgo_pais"], ["Deportes"]))

    def test_guardar_ordena_y_saca_repetidos(self):
        prefs, _ = preferencias.guardar(self.ruta, {"indicadores": ["acciones", "dolar", "dolar"],
                                                    "temas": ["Tecnología", "Política"]})
        self.assertEqual((prefs["indicadores"], preferencias.temas_activos(prefs)), (["dolar", "acciones"], ["Política", "Tecnología"]))

    def test_sin_indicadores_se_guarda_pero_sin_temas_se_rechaza(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": [], "temas": ["Deportes"]})
        self.assertEqual((prefs["indicadores"], preferencias.temas_activos(prefs), errores), ([], ["Deportes"], []))
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": [], "temas": []})
        self.assertIsNone(prefs)
        self.assertEqual(errores, ["Elegí al menos un tema."])
        self.assertEqual(preferencias.temas_activos(preferencias.leer(self.ruta)[0]), ["Deportes"])  # no pisó lo guardado

    def test_dolar_otros_es_valido_y_un_archivo_viejo_lo_deja_destildado(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["dolar_otros"], "temas": ["Deportes"]})
        self.assertEqual((prefs["indicadores"], errores), (["dolar_otros"], []))
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar", "riesgo_pais", "acciones"], "temas": ["Deportes"]})
        leidas, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertNotIn("dolar_otros", leidas["indicadores"])

    def test_reservas_y_tasas_son_validas(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["tasas", "reservas"], "temas": ["Deportes"]})
        self.assertEqual((prefs["indicadores"], errores), (["reservas", "tasas"], []))

    def test_archivo_viejo_sin_version_se_lee_con_reservas_tildadas(self):
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar", "acciones"], "temas": ["Deportes"]})
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual(prefs["indicadores"], ["dolar", "reservas", "acciones"])

    def test_inflacion_es_valida_y_un_archivo_viejo_la_deja_destildada(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["inflacion", "dolar"], "temas": ["Deportes"]})
        self.assertEqual((prefs["indicadores"], errores), (["dolar", "inflacion"], []))
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar"], "temas": ["Deportes"]})
        self.assertNotIn("inflacion", preferencias.leer(self.ruta)[0]["indicadores"])

    def test_archivo_guardado_ahora_respeta_reservas_destildadas(self):
        preferencias.guardar(self.ruta, {"indicadores": ["dolar"], "temas": ["Deportes"]})
        self.assertEqual(preferencias.leer(self.ruta)[0]["indicadores"], ["dolar"])

    def test_internacional_se_guarda(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": [], "temas": ["Internacional"]})
        self.assertEqual((preferencias.temas_activos(prefs), errores), (["Internacional"], []))
        self.assertEqual(preferencias.temas_activos(preferencias.leer(self.ruta)[0]), ["Internacional"])

    def test_archivo_viejo_sin_internacional_se_lee_igual_y_queda_destildada(self):
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar"], "temas": ["Política", "Deportes"]})
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual(preferencias.temas_activos(prefs), ["Política", "Deportes"])

    def test_temas_nuevos_se_pueden_guardar_en_orden_fijo(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": [],
                                                          "temas": ["Espectáculos y Cultura", "Sociedad", "Salud y Ciencia"]})
        self.assertEqual((preferencias.temas_activos(prefs), errores), (["Sociedad", "Salud y Ciencia", "Espectáculos y Cultura"], []))

    def test_archivo_viejo_con_temas_vacios_se_lee_sin_aviso(self):
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar"], "temas": []})
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual((prefs["indicadores"], preferencias.temas_activos(prefs)), (["dolar", "reservas"], []))

    def test_valor_desconocido_se_rechaza_y_no_guarda_nada(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["dolar"], "temas": ["Farándula"]})
        self.assertIsNone(prefs)
        self.assertTrue(any("Farándula" in e for e in errores))
        self.assertFalse(os.path.exists(self.ruta))

    def test_archivo_roto_usa_por_defecto_y_avisa(self):
        os.makedirs(os.path.dirname(self.ruta))
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write("{no es json")
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("roto", aviso)

    def test_archivo_con_valores_invalidos_usa_por_defecto_y_avisa(self):
        os.makedirs(os.path.dirname(self.ruta))
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"indicadores": ["bitcoin"], "temas": []}, archivo)
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("no es válido", aviso)


class Validar(unittest.TestCase):
    def test_no_es_un_objeto(self):
        for malo in (None, [], "texto", 5):
            with self.subTest(malo=malo):
                prefs, errores = preferencias.validar(malo)
                self.assertIsNone(prefs)
                self.assertTrue(errores)

    def test_faltan_claves_o_no_son_listas(self):
        _, errores = preferencias.validar({"indicadores": "dolar"})
        self.assertEqual(len(errores), 2)


def v2(**cambios):
    """Un cuerpo v2 válido (Deportes activo) con los cambios pedidos."""
    base = {"version": 2, "temas": {"Deportes": {"activo": True, "prioridad": "alta"}}, "subtemas": ["Tenis"],
            "medios": {"preferidos": ["Infobae"], "excluidos": ["Perfil"]},
            "palabras": {"seguir": ["Boca"], "evitar": ["farándula"]}, "indicadores": ["dolar", "acciones"]}
    base.update(cambios)
    return base


class EsquemaV2(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = os.path.join(carpeta.name, "datos", "preferencias.json")

    def test_por_defecto_es_v2_con_todos_los_temas(self):
        prefs = preferencias.por_defecto()
        self.assertEqual(prefs["version"], 2)
        self.assertEqual(list(prefs["temas"]), config.TEMAS)
        self.assertEqual(prefs["temas"]["Sociedad"], {"activo": False, "prioridad": "normal"})
        self.assertEqual((prefs["subtemas"], prefs["medios"], prefs["palabras"]),
                         ([], {"preferidos": [], "excluidos": []}, {"seguir": [], "evitar": []}))
        self.assertNotIn("largo", prefs)

    def test_v2_valido_se_guarda_se_completa_y_se_relee_igual(self):
        prefs, errores = preferencias.guardar(self.ruta, v2())
        self.assertEqual(errores, [])
        self.assertEqual(list(prefs["temas"]), config.TEMAS)  # los que faltaban, completos y en orden
        self.assertEqual(prefs["temas"]["Deportes"], {"activo": True, "prioridad": "alta"})
        self.assertEqual(prefs["temas"]["Política"], {"activo": False, "prioridad": "normal"})
        self.assertEqual(preferencias.leer(self.ruta), (prefs, None))
        self.assertEqual(json_seguro.leer(self.ruta, None)[0], prefs)

    def test_v1_en_el_post_se_migra(self):
        prefs, errores = preferencias.guardar(self.ruta, {"indicadores": ["dolar"], "temas": ["Deportes", "Política"]})
        self.assertEqual(errores, [])
        self.assertEqual(prefs["version"], 2)
        self.assertEqual(prefs["temas"]["Política"], {"activo": True, "prioridad": "normal"})
        self.assertEqual((prefs["subtemas"], prefs["medios"]["excluidos"], prefs["palabras"]["seguir"]), ([], [], []))

    def test_lee_v1_viejo_lo_migra_en_memoria_y_no_toca_el_disco(self):
        viejo = {"indicadores": ["dolar", "acciones"], "temas": ["Deportes", "Tecnología"]}
        json_seguro.escribir(self.ruta, viejo)
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual(prefs["version"], 2)
        self.assertEqual(preferencias.temas_activos(prefs), ["Deportes", "Tecnología"])
        self.assertEqual(prefs["indicadores"], ["dolar", "reservas", "acciones"])  # reservas, spec 47
        self.assertNotIn("dolar_otros", prefs["indicadores"])
        self.assertEqual(json_seguro.leer(self.ruta, None)[0], viejo)  # sin reescribir
        preferencias.guardar(self.ruta, prefs)  # el primer guardado lo deja en v2
        self.assertEqual(json_seguro.leer(self.ruta, None)[0], prefs)

    def test_lee_el_archivo_v1_con_la_marca_de_version_de_la_spec_47(self):
        json_seguro.escribir(self.ruta, {"indicadores": ["dolar"], "temas": ["Deportes"], "version": 2})
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual((prefs["indicadores"], preferencias.temas_activos(prefs)), (["dolar"], ["Deportes"]))  # sin reservas

    def test_version_futura_usa_por_defecto_con_aviso(self):
        json_seguro.escribir(self.ruta, {**v2(), "version": 3})
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("versión más nueva", aviso)
        self.assertEqual(preferencias.validar({**v2(), "version": 3})[1],
                         ["Las preferencias son de una versión más nueva que la que entiende esta app."])

    def test_v2_roto_usa_por_defecto_con_aviso(self):
        json_seguro.escribir(self.ruta, v2(temas={"Deportes": {"activo": True, "prioridad": "altísima"}}))
        prefs, aviso = preferencias.leer(self.ruta)
        self.assertEqual(prefs, preferencias.por_defecto())
        self.assertIn("no es válido", aviso)

    def test_valores_desconocidos_rechazan_todo_en_espanol_y_no_guardan(self):
        casos = {
            "tema": v2(temas={"Farándula": {"activo": True, "prioridad": "alta"}}),
            "prioridad": v2(temas={"Deportes": {"activo": True, "prioridad": "altísima"}}),
            "subtema": v2(subtemas=["Ajedrez"]),
            "medio": v2(medios={"preferidos": ["Diario Inventado"], "excluidos": []}),
            "indicador": v2(indicadores=["bitcoin"]),
        }
        for nombre, cuerpo in casos.items():
            with self.subTest(nombre):
                prefs, errores = preferencias.guardar(self.ruta, cuerpo)
                self.assertIsNone(prefs)
                self.assertTrue(errores)
                self.assertFalse(os.path.exists(self.ruta))

    def test_sin_tema_activo_pide_elegir_uno(self):
        prefs, errores = preferencias.validar(v2(temas={"Deportes": {"activo": False, "prioridad": "normal"}}))
        self.assertEqual((prefs, errores), (None, ["Elegí al menos un tema."]))

    def test_un_medio_en_las_dos_listas_da_error(self):
        _, errores = preferencias.validar(v2(medios={"preferidos": ["Perfil"], "excluidos": ["Perfil"]}))
        self.assertEqual(len(errores), 1)
        self.assertIn("Perfil", errores[0])
        self.assertIn("preferidos y los excluidos", errores[0])

    def test_topes_de_palabras_salen_de_config(self):
        muchas = [f"palabra{i}" for i in range(config.MAXIMO_PALABRAS_PREFERENCIA + 1)]
        _, errores = preferencias.validar(v2(palabras={"seguir": muchas, "evitar": []}))
        self.assertEqual(errores, [f"Podés cargar hasta {config.MAXIMO_PALABRAS_PREFERENCIA} palabras."])
        justas = muchas[:-1]
        self.assertEqual(preferencias.validar(v2(palabras={"seguir": justas, "evitar": justas}))[1], [])
        larga = "x" * (config.MAXIMO_CARACTERES_PALABRA + 1)
        _, errores = preferencias.validar(v2(palabras={"seguir": [], "evitar": [larga]}))
        self.assertEqual(errores, [f"Cada palabra puede tener hasta {config.MAXIMO_CARACTERES_PALABRA} caracteres."])
        self.assertEqual(preferencias.validar(v2(palabras={"seguir": ["x" * config.MAXIMO_CARACTERES_PALABRA], "evitar": []}))[1], [])

    def test_las_palabras_se_limpian_pero_se_guarda_lo_que_escribio_la_persona(self):
        prefs, errores = preferencias.validar(v2(palabras={"seguir": ["  Boca   Juniors ", "boca juniors", "", "   ", "BOCA JUNIORS", "Vélez", "velez"],
                                                           "evitar": ["Farándula", "farandula"]}))
        self.assertEqual(errores, [])
        self.assertEqual(prefs["palabras"], {"seguir": ["Boca Juniors", "Vélez"], "evitar": ["Farándula"]})

    def test_palabras_que_no_son_texto_dan_error(self):
        self.assertTrue(preferencias.validar(v2(palabras={"seguir": [5], "evitar": []}))[1])

    def test_subtemas_medios_e_indicadores_se_ordenan_y_sacan_repetidos(self):
        prefs, errores = preferencias.validar(v2(subtemas=["Tenis", "Fútbol argentino", "Tenis"],
                                                 medios={"preferidos": ["Perfil", "Infobae", "Infobae"], "excluidos": []},
                                                 indicadores=["acciones", "dolar", "dolar"]))
        self.assertEqual(errores, [])
        self.assertEqual(prefs["subtemas"], ["Fútbol argentino", "Tenis"])
        self.assertEqual(prefs["medios"]["preferidos"], ["Infobae", "Perfil"])
        self.assertEqual(prefs["indicadores"], ["dolar", "acciones"])

    def test_no_hay_campo_largo_aunque_lo_manden(self):
        prefs, errores = preferencias.validar(v2(largo="corto"))
        self.assertEqual(errores, [])
        self.assertNotIn("largo", prefs)

    def test_medios_disponibles_sin_repetidos_y_alfabeticos(self):
        medios = preferencias.medios_disponibles()
        self.assertEqual(len(medios), len(set(medios)))
        self.assertEqual(medios, sorted(medios, key=normalizar_texto))
        self.assertEqual(set(medios), {f["medio"] for f in config.FUENTES_RSS})

    def test_prioridades_de_temas_solo_las_que_no_son_normales(self):
        prefs, _ = preferencias.validar(v2(temas={"Deportes": {"activo": True, "prioridad": "alta"},
                                                  "Política": {"activo": True, "prioridad": "baja"},
                                                  "Economía": {"activo": True, "prioridad": "normal"}}))
        self.assertEqual(preferencias.prioridades_de_temas(prefs), {"Deportes": "alta", "Política": "baja"})
        self.assertEqual(preferencias.prioridades_de_temas({"temas": ["Deportes"]}), {})


if __name__ == "__main__":
    unittest.main()
