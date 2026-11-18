"""Tests de corrector.py: enlaces, repetidas, largo, nombres vigentes y reintentos."""

import json
import os
import tempfile
import unittest

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


def _revisar(texto, notas=NOTAS, tope=3, palabras_indicadores=0, previos=None, **kwargs):
    return corrector.revisar(lambda c, b: texto, notas, tope, palabras_indicadores, previos=previos, **kwargs)


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

    def test_las_palabras_de_los_indicadores_cuentan_para_el_largo(self):
        self.assertFalse(_revisar(_texto(palabras=600), palabras_indicadores=100, reintentos=0)["chequeo"]["aprobado"])
        self.assertTrue(_revisar(_texto(palabras=500), palabras_indicadores=100)["chequeo"]["aprobado"])

    def test_si_se_pasa_sugiere_recortar_desde_deportes_y_tecnologia(self):
        resultado = _revisar(_texto(palabras=700), reintentos=0)
        self.assertTrue(any("Deportes y Tecnología" in e for e in _errores(resultado)))


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


if __name__ == "__main__":
    unittest.main()
