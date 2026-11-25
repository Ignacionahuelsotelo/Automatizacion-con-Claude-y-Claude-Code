"""Tests de servicio.py sin HTTP: fuentes y `claude` simulados, carpetas temporales."""

import json
import os
import tempfile
import threading
import time
import unittest
from unittest import mock

from micafe.config import ETAPAS_RESUMEN
from micafe.dominio import servicio
from micafe.dominio.progreso import Progreso
from micafe.errores import ErrorAlmacenamiento, ErrorResumen
from tests import utiles
from tests.test_corrector import NOTAS, _texto

INDICADORES = {"indicadores": [{"clave": "reservas", "nombre": "Reservas", "fuente": "BCRA", "valor": None}], "generado_en": "x", "avisos": ["aviso ind"]}
ACCIONES = {"indicadores": [{"clave": "accion_ggal", "nombre": "GGAL", "fuente": "data912", "valor": None}], "avisos": ["aviso acc"]}


def _noticias():
    return {"notas": NOTAS, "fallas": ["falla rss"], "ventana": {}, "tope_por_medio": 3, "generado_en": "x"}


CLAUDE_OK = {"disponible": True, "estado": "ok", "mensaje": "Claude: listo"}


class ServicioDePrueba(unittest.TestCase):
    def setUp(self):
        utiles.silenciar(self)
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.datos = carpeta.name
        self.resumenes = os.path.join(self.datos, "resumenes")
        for nombre, valor in {
            "ARCHIVO_PREFERENCIAS": os.path.join(self.datos, "preferencias.json"),
            "ARCHIVO_INDICADORES": os.path.join(self.datos, "indicadores.json"),
            "ARCHIVO_GUSTOS": os.path.join(self.datos, "gustos.json"),
            "ARCHIVO_ACCIONES": os.path.join(self.datos, "acciones.json"),
            "CARPETA_RESUMENES": self.resumenes,
        }.items():
            parche = mock.patch.object(servicio, nombre, valor)
            parche.start()
            self.addCleanup(parche.stop)
        self.acciones_mock = {}
        for objeto, nombre, kwargs in [
            (servicio.noticias, "obtener", {"side_effect": lambda temas: _noticias()}),
            (servicio.indicadores, "obtener", {"side_effect": lambda archivo, claves: dict(INDICADORES)}),
            (servicio.acciones, "obtener_todo", {"return_value": ACCIONES}),
            (servicio.corrector, "verificar_con_modelo", {"return_value": []}),
            (servicio.resumen, "comprobar_claude", {"return_value": CLAUDE_OK}),
        ]:
            parche = mock.patch.object(objeto, nombre, **kwargs)
            self.acciones_mock[nombre] = parche.start()
            self.addCleanup(parche.stop)

    def elegir(self, indicadores):
        servicio.guardar_preferencias({"indicadores": indicadores, "temas": ["Deportes"]})


class PrepararResumen(ServicioDePrueba):
    def test_ultimo_resumen_suma_notas_calculadas_sin_cambiar_el_archivo(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            servicio.preparar_resumen(utiles.MIERCOLES)
        ruta = os.path.join(self.resumenes, "2026-11-18.json")
        with open(ruta, encoding="utf-8") as archivo:
            guardado = json.load(archivo)
        self.assertNotIn("notas", guardado)
        notas = servicio.ultimo_resumen()["notas"]
        self.assertEqual([n["link"] for n in notas], [n["link"] for n in NOTAS[:3]])
        self.assertTrue(all(n["titulo"] and n["seccion"] == "Política" for n in notas))

    def test_las_prioridades_aprendidas_van_a_claude_sin_titulos_ni_votos_en_el_log(self):
        votado = "Medio votado"
        with open(os.path.join(self.datos, "gustos.json"), "w", encoding="utf-8") as archivo:
            json.dump({"votos": [{"tipo": "nota", "clave": "https://x.test/v", "voto": "me_gusta",
                                  "titulo": "Titulo secreto", "medio": votado, "seccion": "Política",
                                  "votado_en": "2026-11-17T10:00:00-03:00"}]}, archivo)
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar, \
                self.assertLogs("micafe", level="INFO") as registro:
            servicio.preparar_resumen(utiles.MIERCOLES)
        lineas = generar.call_args.kwargs["prioridades"]
        self.assertIn(f"- Te interesan las notas de {votado}.", lineas)
        self.assertNotIn("gustos", generar.call_args.kwargs)
        salida = "\n".join(registro.output)
        for privado in ("Titulo secreto", votado, "secreto"):
            self.assertNotIn(privado, salida)

    def test_sin_votos_no_hay_prioridades(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar:
            servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(generar.call_args.kwargs["prioridades"], [])

    def test_de_punta_a_punta_guarda_y_devuelve_avisos_e_indicadores_con_acciones(self):
        self.elegir(["dolar", "acciones"])
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            salida = servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(salida["avisos"], {"indicadores": ["aviso ind", "aviso acc"], "noticias": ["falla rss"]})
        registro = salida["resumen"]
        self.assertEqual(registro["fecha"], "2026-11-18")
        self.assertTrue(registro["chequeo"]["aprobado"])
        self.assertEqual([i["clave"] for i in registro["indicadores"]], ["reservas", "accion_ggal"])
        self.assertEqual(servicio.ultimo_resumen()["texto"], registro["texto"])
        self.assertTrue(os.path.exists(os.path.join(self.resumenes, "2026-11-18.json")))

    def test_sin_acciones_en_preferencias_no_se_consultan(self):
        self.elegir(["dolar"])
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            salida = servicio.preparar_resumen(utiles.MIERCOLES)
        self.acciones_mock["obtener_todo"].assert_not_called()
        self.assertEqual([i["clave"] for i in salida["resumen"]["indicadores"]], ["reservas"])
        self.assertEqual(salida["avisos"]["indicadores"], ["aviso ind"])

    def test_el_corrector_reintenta_con_las_correcciones_y_el_borrador(self):
        self.elegir(["dolar"])
        malo = _texto(palabras=100)
        with mock.patch.object(servicio.resumen, "generar", side_effect=[malo, _texto()]) as generar:
            salida = servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(generar.call_count, 2)
        self.assertIsNone(generar.call_args_list[0].kwargs["correcciones"])
        self.assertTrue(generar.call_args_list[1].kwargs["correcciones"])
        self.assertEqual(generar.call_args_list[1].kwargs["borrador"], malo)
        self.assertEqual(salida["resumen"]["chequeo"]["intentos"], 2)

    def test_si_claude_falla_el_error_lleva_los_avisos(self):
        self.elegir(["dolar"])
        with mock.patch.object(servicio.resumen, "generar", side_effect=ErrorResumen("Claude falló.")):
            with self.assertRaises(ErrorResumen) as contexto:
                servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(contexto.exception.extras["avisos"]["noticias"], ["falla rss"])

    def test_si_no_puede_guardar_levanta_error_de_almacenamiento_con_avisos(self):
        self.elegir(["dolar"])
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()), \
                mock.patch.object(servicio.resumenes, "guardar", side_effect=PermissionError("sin permiso")):
            with self.assertRaises(ErrorAlmacenamiento) as contexto:
                servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertIn("carpeta datos/", contexto.exception.mensaje)
        self.assertIn("avisos", contexto.exception.extras)


class PedidoDeNoticias(ServicioDePrueba):
    def setUp(self):
        super().setUp()
        self.elegir(["dolar"])

    def test_el_pedido_va_a_cada_redaccion_incluidos_los_reintentos_y_no_al_corrector(self):
        malo = _texto(palabras=100)
        bueno = _texto(notas=[NOTAS[1], NOTAS[4], NOTAS[2]])  # incluye las 2 notas que encajan con el pedido
        with mock.patch.object(servicio.resumen, "generar", side_effect=[malo, bueno]) as generar:
            servicio.preparar_resumen(utiles.MIERCOLES, pedido="más economía")
        self.assertEqual([c.kwargs["pedido"] for c in generar.call_args_list], ["más economía"] * 2)
        verificar = self.acciones_mock["verificar_con_modelo"]
        self.assertTrue(verificar.called)
        for llamada in verificar.call_args_list:
            self.assertNotIn("más economía", repr(llamada))

    def test_el_pedido_llega_a_la_seleccion_y_pedido_sin_notas_queda_en_el_resumen(self):
        # NOTAS del corrector: "Los bancos ajustan sus tasas de interés" encaja con "tasas".
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar:
            con = servicio.preparar_resumen(utiles.MIERCOLES, pedido="tasas")
        self.assertFalse(con["resumen"]["pedido_sin_notas"])
        self.assertEqual(servicio.ultimo_resumen()["pedido_sin_notas"], False)
        self.assertEqual(list(generar.call_args.kwargs["pedidas"]), ["https://ambito.test/2"])
        self.assertEqual(generar.call_args.args[0][0]["link"], "https://ambito.test/2")  # primera
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            sin = servicio.preparar_resumen(utiles.MIERCOLES, pedido="ajedrez")
        self.assertTrue(sin["resumen"]["pedido_sin_notas"])
        self.assertTrue(servicio.ultimo_resumen()["pedido_sin_notas"])

    def test_sin_pedido_pedido_sin_notas_es_false(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar:
            salida = servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertFalse(salida["resumen"]["pedido_sin_notas"])
        self.assertEqual(generar.call_args.kwargs["pedidas"], {})

    def test_el_log_no_trae_el_pedido_ni_sus_terminos_ni_sinonimos(self):
        with self.assertLogs("micafe", level="DEBUG") as registro, \
                mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            servicio.preparar_resumen(utiles.MIERCOLES, pedido="fútbol argentino ZORROPLATEADO")
        salida = "\n".join(registro.output).lower()
        for prohibido in ("zorroplateado", "futbol", "fútbol", "river", "boca"):
            self.assertNotIn(prohibido, salida)
        self.assertIn("encajaron 0 notas", salida)

    def test_el_corrector_no_recibe_el_pedido(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()), \
                mock.patch.object(servicio.corrector, "revisar", wraps=servicio.corrector.revisar) as revisar:
            servicio.preparar_resumen(utiles.MIERCOLES, pedido="SECRETO-PEDIDO")
        self.assertNotIn("SECRETO-PEDIDO", repr(revisar.call_args))

    def test_se_guarda_dentro_del_resumen_solo_si_hubo(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            con = servicio.preparar_resumen(utiles.MIERCOLES, pedido="más economía")
            self.assertEqual(con["resumen"]["pedido"], "más economía")
            self.assertEqual(servicio.ultimo_resumen()["pedido"], "más economía")
            sin = servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertNotIn("pedido", sin["resumen"])
        self.assertNotIn("pedido", servicio.ultimo_resumen())

    def test_el_log_dice_cuantos_caracteres_y_nunca_el_texto(self):
        with self.assertLogs("micafe", level="DEBUG") as registro, \
                mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            servicio.preparar_resumen(utiles.MIERCOLES, pedido="SECRETO-PEDIDO")
        salida = "\n".join(registro.output)
        self.assertIn("Pedido de la persona: sí (14 caracteres)", salida)
        self.assertNotIn("SECRETO", salida)

    def test_iniciar_valida_y_no_inicia_si_el_pedido_no_sirve(self):
        for datos, mensaje in (({"pedido": 5}, "El pedido tiene que ser un texto."),
                               ({"pedido": "a" * 501}, "El pedido es muy largo (máximo 500 caracteres)."),
                               (["x"], None)):
            with mock.patch.object(servicio, "preparar_resumen") as preparar:
                estado, errores = servicio.iniciar_resumen(datos)
            self.assertIsNone(estado)
            self.assertTrue(errores)
            if mensaje:
                self.assertEqual(errores, [mensaje])
            preparar.assert_not_called()
            self.assertEqual(servicio.estado_del_resumen()["estado"], "libre")

    def test_iniciar_pasa_el_pedido_normalizado_y_el_estado_no_lo_contiene(self):
        parche = mock.patch.object(servicio, "progreso_resumen", Progreso())
        parche.start()
        self.addCleanup(parche.stop)
        recibido = {}

        def falso(avisar=None, pedido=None):
            recibido["pedido"] = pedido
            return {"resumen": {"fecha": "2026-11-18", "texto": "t"}, "avisos": {}}

        with mock.patch.object(servicio, "preparar_resumen", side_effect=falso):
            estado, errores = servicio.iniciar_resumen({"pedido": " más\neconomía "})
            fin = esperar_fin(self)
        self.assertEqual(errores, [])
        self.assertEqual(recibido["pedido"], "más economía")
        self.assertNotIn("economía", json.dumps(estado) + json.dumps({k: v for k, v in fin.items() if k != "resultado"}))

    def test_cuerpo_none_vacio_o_sin_pedido_anda_como_antes(self):
        for datos in (None, {}, {"pedido": ""}, {"pedido": None}, {"pedido": "  "}):
            parche = mock.patch.object(servicio, "progreso_resumen", Progreso())
            parche.start()
            recibido = {}

            def falso(avisar=None, pedido=None, recibido=recibido):
                recibido["pedido"] = pedido
                return {"resumen": {"fecha": "2026-11-18", "texto": "t"}, "avisos": {}}

            with mock.patch.object(servicio, "preparar_resumen", side_effect=falso):
                estado, errores = servicio.iniciar_resumen(datos)
                esperar_fin(self)
            parche.stop()
            self.assertEqual(errores, [])
            self.assertIsNone(recibido["pedido"])


class EtapasDelResumen(ServicioDePrueba):
    def test_avisar_recibe_las_etapas_en_orden_con_el_intento_de_la_redaccion(self):
        self.elegir(["dolar"])
        marcas = []
        malo = _texto(palabras=100)
        with mock.patch.object(servicio.resumen, "generar", side_effect=[malo, _texto()]):
            servicio.preparar_resumen(utiles.MIERCOLES, avisar=lambda etapa, intento=None: marcas.append((etapa, intento)))
        self.assertEqual(marcas, [
            ("claude", None), ("noticias", None), ("indicadores", None),
            ("redactando", 1), ("corrigiendo", None), ("redactando", 2), ("corrigiendo", None),
            ("guardando", None),
        ])
        self.assertEqual([c for c, _ in ETAPAS_RESUMEN], ["claude", "noticias", "indicadores", "redactando", "corrigiendo", "guardando"])


def esperar_fin(prueba, plazo=5):
    limite = time.time() + plazo
    while time.time() < limite:
        estado = servicio.estado_del_resumen()
        if estado["estado"] in ("listo", "fallo"):
            return estado
        time.sleep(0.01)
    prueba.fail("el armado no terminó")


class ArmadoEnSegundoPlano(ServicioDePrueba):
    def setUp(self):
        super().setUp()
        parche = mock.patch.object(servicio, "progreso_resumen", Progreso())
        parche.start()
        self.addCleanup(parche.stop)
        self.elegir(["dolar"])

    def test_inicia_responde_en_curso_y_termina_en_listo_con_el_resumen_guardado(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            inicial, _ = servicio.iniciar_resumen()
            self.assertEqual(inicial["estado"], "en_curso")
            estado = esperar_fin(self)
        self.assertEqual(estado["estado"], "listo")
        self.assertEqual(set(e["situacion"] for e in estado["etapas"]), {"hecha"})
        self.assertEqual(servicio.ultimo_resumen()["texto"], estado["resultado"]["resumen"]["texto"])

    def test_un_segundo_inicio_con_uno_en_curso_da_409(self):
        liberar = threading.Event()

        def lento(*args, **kwargs):
            liberar.wait(5)
            return _texto()

        with mock.patch.object(servicio.resumen, "generar", side_effect=lento):
            servicio.iniciar_resumen()
            with self.assertRaises(ErrorResumen) as contexto:
                servicio.iniciar_resumen()
            self.assertEqual(contexto.exception.codigo, 409)
            self.assertEqual(contexto.exception.mensaje, "Ya se está preparando un resumen. Esperá a que termine.")
            limite = time.time() + 5
            while servicio.estado_del_resumen()["etapa"] != "redactando" and time.time() < limite:
                time.sleep(0.01)
            self.assertEqual(servicio.estado_del_resumen()["etapa"], "redactando")
            liberar.set()
            esperar_fin(self)

    def test_el_estado_muestra_los_intentos_del_corrector(self):
        vistos = []
        textos = [_texto(palabras=100), _texto(palabras=100), _texto()]

        def generar(*args, **kwargs):
            vistos.append(servicio.estado_del_resumen()["intento"])
            return textos.pop(0)

        with mock.patch.object(servicio.resumen, "generar", side_effect=generar):
            servicio.iniciar_resumen()
            esperar_fin(self)
        self.assertEqual(vistos, [1, 2, 3])

    def test_un_error_previsto_deja_fallo_con_mensaje_y_avisos_y_permite_otro_armado(self):
        with mock.patch.object(servicio.resumen, "generar", side_effect=ErrorResumen("Claude falló.")):
            servicio.iniciar_resumen()
            estado = esperar_fin(self)
        self.assertEqual(estado["estado"], "fallo")
        self.assertEqual(estado["errores"], ["Claude falló."])
        self.assertEqual(estado["avisos"]["noticias"], ["falla rss"])
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            servicio.iniciar_resumen()
            self.assertEqual(esperar_fin(self)["estado"], "listo")

    def test_fallo_al_guardar_deja_fallo_con_avisos(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()), \
                mock.patch.object(servicio.resumenes, "guardar", side_effect=PermissionError("sin permiso")):
            servicio.iniciar_resumen()
            estado = esperar_fin(self)
        self.assertEqual(estado["estado"], "fallo")
        self.assertIn("carpeta datos/", estado["errores"][0])
        self.assertIn("noticias", estado["avisos"])

    def test_un_error_inesperado_deja_fallo_y_queda_en_el_log(self):
        with mock.patch.object(servicio.noticias, "obtener", side_effect=RuntimeError("secreto técnico")), \
                self.assertLogs("micafe.dominio.servicio", level="ERROR") as registro:
            servicio.iniciar_resumen()
            estado = esperar_fin(self)
        self.assertEqual(estado["estado"], "fallo")
        self.assertEqual(estado["errores"], [servicio.MENSAJE_ERROR_INESPERADO])
        self.assertNotIn("secreto", " ".join(estado["errores"]))
        self.assertIn("error inesperado", registro.output[0])

    def test_sin_claude_falla_en_la_primera_etapa_con_el_mensaje_en_espanol(self):
        no_esta = {"disponible": False, "estado": "no_instalado", "mensaje": "No se encontró el comando `claude`."}
        with mock.patch.object(servicio.resumen, "comprobar_claude", return_value=no_esta):
            servicio.iniciar_resumen()
            estado = esperar_fin(self)
        self.assertEqual(estado["estado"], "fallo")
        self.assertEqual(estado["errores"], [no_esta["mensaje"]])
        self.assertEqual(estado["etapa"], "claude")

    def test_el_estado_no_lleva_el_texto_del_resumen_mientras_corre(self):
        liberar = threading.Event()

        def lento(*args, **kwargs):
            liberar.wait(5)
            return _texto()

        with mock.patch.object(servicio.resumen, "generar", side_effect=lento):
            servicio.iniciar_resumen()
            en_curso = json.dumps(servicio.estado_del_resumen(), ensure_ascii=False)
            liberar.set()
            esperar_fin(self)
        self.assertNotIn("Lo más importante", en_curso)
        self.assertNotIn("resultado", en_curso)


class ChequeoDeClaude(ServicioDePrueba):
    def test_preparar_resumen_sin_claude_falla_con_503_antes_de_llamar_a_las_fuentes(self):
        self.elegir(["dolar", "acciones"])
        no_esta = {"disponible": False, "estado": "no_instalado", "mensaje": "No se encontró el comando `claude`."}
        falla = AssertionError("no se debía consultar")
        with mock.patch.object(servicio.resumen, "comprobar_claude", return_value=no_esta), \
                mock.patch.object(servicio.noticias, "obtener", side_effect=falla) as noticias, \
                mock.patch.object(servicio.indicadores, "obtener", side_effect=falla) as indicadores, \
                mock.patch.object(servicio.resumen, "generar") as generar:
            with self.assertRaises(ErrorResumen) as contexto:
                servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(contexto.exception.codigo, 503)
        self.assertEqual(contexto.exception.mensaje, no_esta["mensaje"])
        generar.assert_not_called()
        noticias.assert_not_called()
        indicadores.assert_not_called()

    def test_estado_de_claude_devuelve_el_chequeo(self):
        self.assertEqual(servicio.estado_de_claude(), CLAUDE_OK)


class OtrasOperaciones(ServicioDePrueba):
    def test_preferencias_invalidas_devuelven_errores_y_no_guardan(self):
        _, errores = servicio.guardar_preferencias({"indicadores": ["bitcoin"], "temas": []})
        self.assertTrue(errores)

    def test_voto_valido_se_guarda_y_error_de_escritura_levanta(self):
        voto = {"tipo": "tema", "clave": "Deportes", "voto": "me_gusta"}
        votos, errores = servicio.guardar_voto(voto)
        self.assertEqual(errores, [])
        self.assertTrue(votos)
        with mock.patch.object(servicio.gustos, "guardar", side_effect=PermissionError("x")):
            with self.assertRaises(ErrorAlmacenamiento):
                servicio.guardar_voto(voto)

    def test_obtener_indicadores_y_noticias_usan_las_preferencias(self):
        self.elegir(["dolar", "acciones"])
        self.assertEqual(len(servicio.obtener_indicadores()["indicadores"]), 2)
        self.assertEqual(servicio.obtener_noticias()["tope_por_medio"], 3)

    def test_responder_pregunta_delega_en_la_caja(self):
        with mock.patch.object(servicio.caja, "responder", return_value={"respuesta": "hola"}) as caja:
            self.assertEqual(servicio.responder_pregunta({"a": 1}), {"respuesta": "hola"})
        caja.assert_called_once_with({"a": 1})


if __name__ == "__main__":
    unittest.main()


class PlanDeSecciones(ServicioDePrueba):
    def setUp(self):
        super().setUp()
        self.elegir(["dolar"])
        servicio.guardar_preferencias({"indicadores": ["dolar"], "temas": ["Política"]})
        notas = [dict(n, seccion="Política") for n in NOTAS[:3]]
        parche = mock.patch.object(servicio.noticias, "obtener", side_effect=lambda temas: {**_noticias(), "notas": notas})
        parche.start()
        self.addCleanup(parche.stop)

    def test_el_plan_va_al_prompt_y_se_guarda_en_el_resumen(self):
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar:
            salida = servicio.preparar_resumen(utiles.MIERCOLES)
        self.assertEqual(generar.call_args.kwargs["plan"][0]["seccion"], "Política")
        plan = salida["resumen"]["plan"]
        self.assertEqual(plan["secciones"][0]["cupo"], 3)
        self.assertFalse(plan["completo"])  # 3 notas posibles, menos que el objetivo
        with open(os.path.join(self.resumenes, "2026-11-18.json"), encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo)["plan"], plan)

    def test_un_resumen_viejo_sin_plan_se_abre(self):
        os.makedirs(self.resumenes)
        with open(os.path.join(self.resumenes, "2026-11-10.json"), "w", encoding="utf-8") as archivo:
            json.dump({"fecha": "2026-11-10", "generado_en": "x", "indicadores": [], "texto": "Un texto", "chequeo": {}}, archivo)
        self.assertNotIn("plan", servicio.ultimo_resumen())


class PreferenciasV2EnElServicio(ServicioDePrueba):
    def setUp(self):
        super().setUp()
        self.notas = [dict(NOTAS[0], titulo="Boca gana", seccion="Deportes", medio="Perfil", link="https://perfil.test/1"),
                      dict(NOTAS[1], titulo="Racing gana", seccion="Deportes", medio="Infobae", link="https://infobae.test/2"),
                      dict(NOTAS[2], titulo="Se juega la fecha", seccion="Deportes", medio="Olé", link="https://ole.test/3")]
        parche = mock.patch.object(servicio.noticias, "obtener", side_effect=lambda temas: {**_noticias(), "notas": self.notas})
        self.obtener = parche.start()
        self.addCleanup(parche.stop)

    def guardar(self, **cambios):
        cuerpo = {"version": 2, "temas": {"Deportes": {"activo": True, "prioridad": "normal"}}, "indicadores": ["dolar"],
                  "medios": {"preferidos": [], "excluidos": []}, "palabras": {"seguir": [], "evitar": []}}
        cuerpo.update(cambios)
        _, errores = servicio.guardar_preferencias(cuerpo)
        self.assertEqual(errores, [])

    def test_noticias_de_ayer_recibe_los_temas_activos_y_no_trae_medios_excluidos(self):
        self.guardar(medios={"preferidos": ["Olé"], "excluidos": ["Perfil"]})
        notas = servicio.obtener_noticias()["notas"]
        self.assertEqual([n["link"] for n in notas][0], "https://ole.test/3")  # medio preferido primero
        self.assertNotIn("https://perfil.test/1", [n["link"] for n in notas])
        self.assertIn("medio preferido", notas[0]["motivos"])
        self.assertEqual(self.obtener.call_args.args[0], ["Deportes"])

    def test_el_armado_usa_las_preferencias_sin_perder_el_pedido_ni_loguear_palabras(self):
        self.guardar(medios={"preferidos": [], "excluidos": ["Perfil"]}, palabras={"seguir": ["Racing"], "evitar": ["SecretoEvitar"]},
                     temas={"Deportes": {"activo": True, "prioridad": "alta"}})
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()) as generar, \
                self.assertLogs("micafe", level="INFO") as registro:
            servicio.preparar_resumen(utiles.MIERCOLES)
        enviadas = [n["link"] for n in generar.call_args.args[0]]
        self.assertEqual(enviadas, ["https://infobae.test/2", "https://ole.test/3"])
        self.assertEqual(generar.call_args.kwargs["preferencias"]["palabras"]["seguir"], ["Racing"])
        self.assertEqual(generar.call_args.kwargs["plan"][0]["prioridad"], "alta")
        salida = "\n".join(registro.output)
        for privado in ("Racing", "SecretoEvitar", "perfil.test"):
            self.assertNotIn(privado, salida)
        self.assertIn("1 palabras a seguir", salida)  # solo cantidades

    def test_un_pedido_que_solo_encaja_con_un_medio_excluido_queda_sin_notas(self):
        self.guardar(medios={"preferidos": [], "excluidos": ["Perfil"]})
        with mock.patch.object(servicio.resumen, "generar", return_value=_texto()):
            salida = servicio.preparar_resumen(utiles.MIERCOLES, pedido="Boca")
        self.assertTrue(salida["resumen"]["pedido_sin_notas"])

    def test_opciones_completas(self):
        opciones = servicio.opciones_de_preferencias()
        self.assertEqual(opciones["prioridades"], ["alta", "normal", "baja"])
        self.assertEqual(opciones["secciones"], list(servicio.TEMAS))
        self.assertIn("Tenis", opciones["subtemas"])
        self.assertNotIn("temas", opciones)
