"""Tests de corrector.py: enlaces, repetidas, largo, nombres vigentes y reintentos."""

import json
import os
import tempfile
import unittest
from unittest import mock

from micafe.dominio import corrector
from micafe.dominio import resumen
from tests import utiles

NOTAS = [
    {"titulo": "El Gobierno anunció una nueva medida económica", "medio": "Infobae", "link": "https://infobae.test/1"},
    {"titulo": "Los bancos ajustan sus tasas de interés", "medio": "Ámbito", "link": "https://ambito.test/2"},
    {"titulo": "Se juega la final del torneo de verano", "medio": "Olé", "link": "https://ole.test/3"},
    {"titulo": "Cambios en el gabinete nacional", "medio": "Infobae", "link": "https://infobae.test/4"},
    {"titulo": "Récord de exportaciones del agro", "medio": "Infobae", "link": "https://infobae.test/5"},
    {"titulo": "Nueva ley de alquileres en debate", "medio": "Infobae", "link": "https://infobae.test/6"},
]


def _bloque(nota, seccion="Política", sin_link=False):
    cuerpo = f"{seccion}\n{nota['titulo']}\nUn párrafo que cuenta de qué trata la nota."
    return cuerpo if sin_link else cuerpo + f"\n{nota['link']}"


def _texto(notas=NOTAS[:3], palabras=600, extra=""):
    """Arma un resumen con apertura, una nota por bloque y `palabras` palabras en total."""
    def armar(relleno):
        bloques = [f"Lo más importante de hoy: {extra} " + ("palabra " * relleno).strip()]
        bloques += [_bloque(n) for n in notas]
        bloques.append("Lo que viene hoy: nada especial.")
        return "\n\n".join(bloques)

    texto = armar(0)
    return armar(max(palabras - len(texto.split()), 0))


def _revisar(texto, notas=NOTAS, tope=3, previos=None, **kwargs):
    return corrector.revisar(lambda c, b: texto, notas, tope, previos=previos, **kwargs)


def _errores(resultado):
    return resultado["chequeo"]["no_cumple"]


class ResumenValido(unittest.TestCase):
    def test_texto_correcto_pasa_al_primer_intento(self):
        resultado = _revisar(_texto())
        self.assertTrue(resultado["chequeo"]["aprobado"], _errores(resultado))
        self.assertEqual(resultado["chequeo"]["intentos"], 1)
        self.assertEqual(resultado["chequeo"]["no_cumple"], [])

    def test_sin_resumenes_previos_el_chequeo_de_repetidas_queda_omitido(self):
        resultado = _revisar(_texto())
        self.assertTrue(any("todavía no hay resúmenes guardados" in o for o in resultado["chequeo"]["omitido"]))


class Largo(unittest.TestCase):
    def test_550_y_650_palabras_pasan(self):
        for palabras in (550, 650):
            with self.subTest(palabras=palabras):
                self.assertTrue(_revisar(_texto(palabras=palabras))["chequeo"]["aprobado"])

    def test_549_y_651_no_pasan(self):
        for palabras in (549, 651):
            with self.subTest(palabras=palabras):
                resultado = _revisar(_texto(palabras=palabras), reintentos=0)
                self.assertFalse(resultado["chequeo"]["aprobado"])
                self.assertTrue(any(e.startswith("Largo:") for e in _errores(resultado)))

    def test_el_largo_cuenta_solo_el_texto_y_el_mensaje_no_menciona_indicadores(self):
        self.assertTrue(_revisar(_texto(palabras=560))["chequeo"]["aprobado"])
        resultado = _revisar(_texto(palabras=660), reintentos=0)
        self.assertFalse(resultado["chequeo"]["aprobado"])
        error = [e for e in _errores(resultado) if e.startswith("Largo:")][0]
        self.assertNotIn("indicadores con", error)
        self.assertNotIn("sin indicadores", error)
        self.assertIn("660 palabras", error)

    def test_si_se_pasa_sugiere_recortar_desde_las_secciones_de_menor_prioridad(self):
        resultado = _revisar(_texto(palabras=700), reintentos=0)
        self.assertTrue(any("menor prioridad" in e for e in _errores(resultado)))


class Enlaces(unittest.TestCase):
    def test_falta_el_enlace_en_una_nota(self):
        texto = "\n\n".join([_bloque(NOTAS[0]), _bloque(NOTAS[1], sin_link=True), _bloque(NOTAS[2])])
        resultado = _revisar(texto, minimo=0, reintentos=0)
        self.assertFalse(resultado["chequeo"]["aprobado"])
        self.assertTrue(any("Falta el enlace" in e and NOTAS[1]["titulo"] in e for e in _errores(resultado)))

    def test_enlace_que_no_es_de_las_notas_de_ayer(self):
        texto = _texto().replace("https://ole.test/3", "https://inventado.test/x")
        resultado = _revisar(texto, reintentos=0)
        self.assertTrue(any("no es de las notas de ayer" in e for e in _errores(resultado)))


class TopePorMedio(unittest.TestCase):
    def test_mas_notas_que_el_tope_de_un_medio(self):
        infobae = [n for n in NOTAS if n["medio"] == "Infobae"]  # 4 notas
        resultado = _revisar(_texto(notas=infobae), tope=3, reintentos=0)
        self.assertTrue(any("Hay 4 notas de Infobae" in e for e in _errores(resultado)))

    def test_el_lunes_el_tope_es_5(self):
        infobae = [n for n in NOTAS if n["medio"] == "Infobae"]
        self.assertTrue(_revisar(_texto(notas=infobae), tope=5)["chequeo"]["aprobado"])


class Repetidas(unittest.TestCase):
    def test_misma_nota_dos_veces_en_el_resumen(self):
        resultado = _revisar(_texto(notas=[NOTAS[0], NOTAS[1], NOTAS[0]]), reintentos=0)
        self.assertTrue(any("dos veces" in e for e in _errores(resultado)))

    def test_titulo_casi_igual_con_otro_enlace(self):
        parecida = dict(NOTAS[1], titulo="Los bancos ajustan sus tasas de interes!", link="https://ambito.test/9")
        notas = NOTAS + [parecida]
        resultado = _revisar(_texto(notas=[NOTAS[1], parecida]), notas=notas, reintentos=0)
        self.assertTrue(any("dos veces" in e for e in _errores(resultado)))

    def test_repetida_de_un_resumen_anterior_por_enlace(self):
        previo = _texto(notas=[NOTAS[0]])
        resultado = _revisar(_texto(), previos=[previo], reintentos=0)
        self.assertTrue(any("resumen anterior (mismo enlace)" in e for e in _errores(resultado)))

    def test_repetida_de_un_resumen_anterior_por_titulo(self):
        otra_url = dict(NOTAS[0], link="https://viejo.test/otra-url")
        resultado = _revisar(_texto(), previos=[_texto(notas=[otra_url])], reintentos=0)
        self.assertTrue(any("resumen anterior (título casi igual)" in e for e in _errores(resultado)))

    def test_sin_coincidencias_con_los_anteriores_pasa(self):
        previo = _texto(notas=NOTAS[3:5])
        resultado = _revisar(_texto(notas=NOTAS[:3]), previos=[previo])
        self.assertTrue(resultado["chequeo"]["aprobado"], _errores(resultado))

    def test_titulos_parecidos_ignora_tildes_mayusculas_y_puntuacion(self):
        self.assertTrue(corrector.titulos_parecidos("Récord de Exportaciones!", "record de exportaciones"))
        self.assertFalse(corrector.titulos_parecidos("Récord de exportaciones", "Cambios en el gabinete"))
        self.assertFalse(corrector.titulos_parecidos("", "algo"))


class NombresVigentes(unittest.TestCase):
    def test_sp_merval_no_pasa(self):
        resultado = _revisar(_texto(extra="El S&P Merval subió."), reintentos=0)
        self.assertTrue(any("MSCI Merval" in e for e in _errores(resultado)))

    def test_msci_merval_pasa(self):
        resultado = _revisar(_texto(extra="El MSCI Merval subió."))
        self.assertTrue(resultado["chequeo"]["aprobado"], _errores(resultado))

    def test_telam_como_agencia_no_pasa_pero_ex_telam_si(self):
        malo = _revisar(_texto(extra="Según Télam, hubo cambios."), reintentos=0)
        self.assertTrue(any("Télam" in e for e in _errores(malo)))
        bueno = _revisar(_texto(extra="Lo contó un periodista de la ex Télam."))
        self.assertTrue(bueno["chequeo"]["aprobado"], _errores(bueno))


class Reintentos(unittest.TestCase):
    def test_siempre_mal_hace_como_mucho_2_reintentos_y_deja_aviso(self):
        llamadas = []

        def redactar(correcciones, borrador):
            llamadas.append((correcciones, borrador))
            return _texto(palabras=100)

        resultado = corrector.revisar(redactar, NOTAS, 3, 0)
        self.assertEqual(len(llamadas), 3)  # el intento original más 2 reintentos
        self.assertEqual(resultado["chequeo"]["intentos"], 3)
        self.assertFalse(resultado["chequeo"]["aprobado"])
        self.assertTrue(resultado["chequeo"]["no_cumple"])  # aviso visible con lo que falló
        self.assertTrue(resultado["texto"])  # igual devuelve el último texto

    def test_el_reintento_recibe_las_correcciones_y_el_borrador(self):
        llamadas = []

        def redactar(correcciones, borrador):
            llamadas.append((correcciones, borrador))
            return _texto(palabras=100) if len(llamadas) == 1 else _texto(palabras=600)

        resultado = corrector.revisar(redactar, NOTAS, 3, 0)
        self.assertEqual(llamadas[0], (None, None))
        self.assertTrue(any(e.startswith("Largo:") for e in llamadas[1][0]))
        self.assertIn("Lo más importante de hoy:", llamadas[1][1])
        self.assertTrue(resultado["chequeo"]["aprobado"])
        self.assertEqual(resultado["chequeo"]["intentos"], 2)

    def test_error_de_redaccion_se_propaga(self):
        def redactar(correcciones, borrador):
            raise resumen.ErrorResumen("claude no anda")
        with self.assertRaises(resumen.ErrorResumen):
            corrector.revisar(redactar, NOTAS, 3, 0)


class ChequeoConModelo(unittest.TestCase):
    def test_veredicto_ok_aprueba(self):
        resultado = _revisar(_texto(), verificar_modelo=lambda texto: [])
        self.assertTrue(resultado["chequeo"]["aprobado"])

    def test_problemas_del_modelo_provocan_reintento(self):
        respuestas = [["La nota 2 no está respaldada."], []]
        resultado = _revisar(_texto(), verificar_modelo=lambda texto: respuestas.pop(0))
        self.assertTrue(resultado["chequeo"]["aprobado"])
        self.assertEqual(resultado["chequeo"]["intentos"], 2)

    def test_si_claude_falla_no_reintenta_y_avisa_que_no_se_pudo_revisar(self):
        def falla(texto):
            raise resumen.ErrorResumen("Claude tardó más de 5 minutos")
        resultado = _revisar(_texto(), verificar_modelo=falla)
        self.assertFalse(resultado["chequeo"]["aprobado"])
        self.assertEqual(resultado["chequeo"]["intentos"], 1)
        self.assertTrue(any("No se pudo revisar el contenido" in e for e in _errores(resultado)))

    def test_el_prompt_del_corrector_incluye_la_bajada(self):
        notas = [{"titulo": "Con bajada", "medio": "Infobae", "seccion": "Política", "fecha": "17/11/2026 09:00",
                  "link": "https://a.test/1", "bajada": "Esta es la bajada."},
                 {"titulo": "Sin bajada", "medio": "Ámbito", "seccion": "Economía", "fecha": "17/11/2026 09:00",
                  "link": "https://a.test/2"}]
        with mock.patch("micafe.dominio.corrector.resumen.ejecutar_claude", return_value="OK") as claude:
            self.assertEqual(corrector.verificar_con_modelo("Texto", notas), [])
        pedido = claude.call_args.args[0]
        self.assertIn("Con bajada (Infobae). Link: https://a.test/1\n  Bajada: Esta es la bajada.", pedido)
        self.assertEqual(pedido.count("Bajada:"), 1)

    def test_la_skill_del_corrector_habla_de_titulo_y_bajada(self):
        with open(corrector.ARCHIVO_SKILL, encoding="utf-8") as archivo:
            self.assertIn("título y bajada", archivo.read())

    def test_interpretar_veredicto(self):
        self.assertEqual(corrector.interpretar_veredicto("OK"), [])
        self.assertEqual(corrector.interpretar_veredicto("ok."), [])
        self.assertEqual(corrector.interpretar_veredicto("- Uno\n- Dos"), ["Uno", "Dos"])
        self.assertEqual(len(corrector.interpretar_veredicto("no sé qué decir")), 1)
        self.assertEqual(len(corrector.interpretar_veredicto("")), 1)


class NotasVotables(unittest.TestCase):
    """Spec 31: leer las notas del resumen como {titulo, medio, seccion, link}."""

    TEXTO = (
        "Lo más importante de hoy: pasó algo grande.\n\n"
        "Política\nTítulo uno\nCuerpo de la nota uno.\nPor qué importa: porque sí.\n"
        "Infobae, 17/11/2026\nhttps://infobae.test/1\n\n"
        "Título dos\nCuerpo de la dos.\nPor qué importa: también.\nPágina/12, Buenos Aires, 17/11/2026\n"
        "https://pagina12.test/2\n\n"
        "Economía\nTítulo tres sin link\nCuerpo.\nPor qué importa: no tiene link.\nÁmbito, 17/11/2026\n\n"
        "Título cuatro\nCuerpo.\nPor qué importa: dos fuentes.\nClarín, 17/11/2026\nhttps://clarin.test/4\n"
        "La Nación, 17/11/2026\nhttps://lanacion.test/4b\n\n"
        "Deportes\nTítulo cinco\nhttps://ole.test/5\n\n"
        "Lo que viene hoy: una votación. https://infobae.test/9"
    )

    def test_una_nota_por_bloque_con_titulo_medio_seccion_y_link(self):
        self.assertEqual(corrector.notas_votables(self.TEXTO), [
            {"titulo": "Título uno", "medio": "Infobae", "seccion": "Política", "link": "https://infobae.test/1"},
            {"titulo": "Título dos", "medio": "Página/12, Buenos Aires", "seccion": "Política",
             "link": "https://pagina12.test/2"},
            {"titulo": "Título cuatro", "medio": "Clarín", "seccion": "Economía", "link": "https://clarin.test/4"},
            {"titulo": "Título cinco", "medio": "", "seccion": "Deportes", "link": "https://ole.test/5"},
        ])

    def test_con_dos_links_se_toma_el_primero(self):
        links = [n["link"] for n in corrector.notas_votables(self.TEXTO)]
        self.assertIn("https://clarin.test/4", links)
        self.assertNotIn("https://lanacion.test/4b", links)

    def test_texto_vacio_o_none_no_da_notas(self):
        self.assertEqual(corrector.notas_votables(""), [])
        self.assertEqual(corrector.notas_votables(None), [])


class EncabezadosDeVariasPalabras(unittest.TestCase):
    def test_salud_y_ciencia_y_espectaculos_y_cultura_son_secciones(self):
        texto = _texto_en_secciones([("Salud y Ciencia", NOTAS[:1]), ("Espectáculos y Cultura", NOTAS[1:2])])
        votables = corrector.notas_votables(texto)
        self.assertEqual([(n["seccion"], n["link"]) for n in votables],
                         [("Salud y Ciencia", "https://infobae.test/1"),
                          ("Espectáculos y Cultura", "https://ambito.test/2")])
        resultado = _revisar(texto, plan=_plan(**{"Salud y Ciencia": 1, "Espectáculos y Cultura": 1}), reintentos=0)
        self.assertFalse(any("no está en el plan" in e for e in _errores(resultado)))


if __name__ == "__main__":
    unittest.main()


def _plan(**cupos):
    return [{"seccion": s, "cupo": c, "pedidas": 0, "motivos": []} for s, c in cupos.items()]


def _texto_en_secciones(notas_por_seccion, palabras=600):
    """Resumen con encabezados de sección propios (una línea sola) y una nota por bloque."""
    bloques = ["Lo más importante de hoy: " + "palabra " * max(palabras - 60, 0)]
    for seccion, notas in notas_por_seccion:
        bloques.append(seccion)
        bloques += [f"{n['titulo']}\nUn párrafo que cuenta de qué trata la nota.\n{n['link']}" for n in notas]
    return "\n\n".join(bloques)


class SeccionesDelPlan(unittest.TestCase):
    def test_cumple_el_plan_pasa(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2]), ("Deportes", NOTAS[2:3])])
        resultado = _revisar(texto, plan=_plan(Política=2, Deportes=1), reintentos=0)
        self.assertTrue(resultado["chequeo"]["aprobado"], _errores(resultado))

    def test_seccion_fuera_del_plan_no_pasa(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2]), ("Deportes", NOTAS[2:3])])
        resultado = _revisar(texto, plan=_plan(Política=2), reintentos=0)
        self.assertFalse(resultado["chequeo"]["aprobado"])
        self.assertTrue(any("Deportes no está en el plan" in e for e in _errores(resultado)))

    def test_mas_notas_que_la_cuota_no_pasa(self):
        texto = _texto_en_secciones([("Política", NOTAS[:3])])
        resultado = _revisar(texto, plan=_plan(Política=2), reintentos=0)
        self.assertTrue(any("tiene 3 notas y su cuota de hoy es 2" in e for e in _errores(resultado)))

    def test_sin_plan_no_se_chequea(self):
        texto = _texto_en_secciones([("Política", NOTAS[:3])])
        self.assertTrue(_revisar(texto, reintentos=0)["chequeo"]["aprobado"])


class PedidoDelPlan(unittest.TestCase):
    def test_con_dos_pedidas_y_ninguna_en_el_resumen_no_pasa(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2])])
        pedidas = [NOTAS[4]["link"], NOTAS[5]["link"]]
        resultado = _revisar(texto, pedidas=pedidas, reintentos=0)
        self.assertTrue(any(e.startswith("Pedido:") for e in _errores(resultado)))

    def test_con_dos_pedidas_hacen_falta_dos(self):
        pedidas = [NOTAS[0]["link"], NOTAS[5]["link"]]
        una = _texto_en_secciones([("Política", NOTAS[:2])])
        dos = _texto_en_secciones([("Política", [NOTAS[0], NOTAS[5]])])
        self.assertFalse(_revisar(una, pedidas=pedidas, reintentos=0)["chequeo"]["aprobado"])
        self.assertTrue(_revisar(dos, pedidas=pedidas, reintentos=0)["chequeo"]["aprobado"])

    def test_con_una_sola_pedida_alcanza_con_una(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2])])
        self.assertTrue(_revisar(texto, pedidas=[NOTAS[1]["link"]], reintentos=0)["chequeo"]["aprobado"])
        self.assertFalse(_revisar(texto, pedidas=[NOTAS[5]["link"]], reintentos=0)["chequeo"]["aprobado"])


class LargoSegunElPlan(unittest.TestCase):
    def test_plan_incompleto_acepta_menos_de_550_y_lo_deja_registrado(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2])], palabras=300)
        resultado = _revisar(texto, plan=_plan(Política=2), plan_completo=False, reintentos=0)
        self.assertTrue(resultado["chequeo"]["aprobado"], _errores(resultado))
        self.assertTrue(any("Largo mínimo no exigido" in o for o in resultado["chequeo"]["omitido"]))

    def test_plan_completo_exige_550(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2])], palabras=300)
        resultado = _revisar(texto, plan=_plan(Política=2), plan_completo=True, reintentos=0)
        self.assertFalse(resultado["chequeo"]["aprobado"])

    def test_el_maximo_vale_aunque_el_plan_sea_incompleto_y_nombra_el_orden_de_recorte(self):
        texto = _texto_en_secciones([("Política", NOTAS[:2])], palabras=700)
        plan = _plan(Política=2, Deportes=1)
        resultado = _revisar(texto, plan=plan, plan_completo=False, reintentos=0)
        self.assertTrue(any("menor prioridad" in e and "Orden para recortar" in e for e in _errores(resultado)))
