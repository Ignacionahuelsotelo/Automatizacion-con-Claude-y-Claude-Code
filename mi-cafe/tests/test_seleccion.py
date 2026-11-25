"""Tests de seleccion.py: términos del pedido, puntaje y elección de candidatas (spec 39)."""

import unittest

from micafe import config
from micafe.config import MAXIMO_CANDIDATAS_PARA_CLAUDE, MINIMO_POR_SECCION_ACTIVA, NOTAS_OBJETIVO, PESOS_PUNTAJE, TEMAS
from micafe.dominio import seleccion

TODOS = {"indicadores": [], "temas": list(TEMAS)}


def nota(titulo, fecha="17/11/2026 10:00", seccion="Deportes", medio="Medio A", link=None, bajada="", categorias=None):
    return {"titulo": titulo, "medio": medio, "seccion": seccion, "fecha": fecha,
            "link": link or f"https://x.test/{titulo.replace(' ', '-')}", "bajada": bajada,
            "categorias": categorias or []}


class Terminos(unittest.TestCase):
    def test_pedido_vacio_da_lista_vacia(self):
        for texto in (None, "", "   ", "quiero noticias sobre hoy"):
            self.assertEqual(seleccion.terminos_del_pedido(texto), [])

    def test_sin_tildes_ni_mayusculas_da_lo_mismo(self):
        self.assertEqual(seleccion.terminos_del_pedido("FUTBOL Argentino"),
                         seleccion.terminos_del_pedido("fútbol argentino"))

    def test_expande_sinonimos_y_no_repite(self):
        terminos = seleccion.terminos_del_pedido("fútbol argentino y River")
        self.assertEqual(terminos[0], "futbol argentino")
        for esperado in ("river", "boca", "afa", "copa argentina", "primera division"):
            self.assertIn(esperado, terminos)
        self.assertEqual(len(terminos), len(set(terminos)))

    def test_saca_palabras_vacias(self):
        self.assertEqual(seleccion.terminos_del_pedido("Quiero noticias sobre Messi, hoy!"), ["messi"])


class Puntaje(unittest.TestCase):
    def test_la_nota_vieja_con_river_gana_a_una_nueva_sin_relacion(self):
        vieja = nota("River goleó en el Monumental", fecha="17/11/2026 08:00")
        nueva = nota("Se juega el tenis en Australia", fecha="17/11/2026 22:00")
        sel = seleccion.elegir_candidatas([nueva, vieja], TODOS, seleccion.terminos_del_pedido("fútbol argentino"))
        self.assertEqual(sel["candidatas"][0], vieja)
        self.assertEqual(sel["encajan"], [vieja["link"]])
        self.assertIn("pedido: river (titulo)", sel["motivos"][vieja["link"]])
        self.assertFalse(sel["pedido_sin_notas"])

    def test_titulo_pesa_mas_que_bajada_y_bajada_mas_que_categoria(self):
        en_titulo = nota("River gana", link="https://x.test/t")
        en_bajada = nota("Gana otro", bajada="Fue River", link="https://x.test/b")
        en_categoria = nota("Gana alguien", categorias=["River"], link="https://x.test/c")
        puntos = {p["nota"]["link"]: p["puntaje"] for p in
                  seleccion.puntuar([en_categoria, en_bajada, en_titulo], TODOS, ["river"])}
        self.assertGreater(puntos["https://x.test/t"], puntos["https://x.test/b"])
        self.assertGreater(puntos["https://x.test/b"], puntos["https://x.test/c"])
        self.assertGreater(puntos["https://x.test/c"], 0)

    def test_encaja_por_palabra_y_no_por_pedazo(self):
        puntuada = seleccion.puntuar([nota("Riverside inaugura un hotel")], TODOS, ["river"])[0]
        self.assertFalse(puntuada["encaja"])

    def test_sin_pedido_solo_suma_frescura_y_la_mas_nueva_va_primero(self):
        vieja, nueva = nota("Vieja", fecha="17/11/2026 08:00"), nota("Nueva", fecha="17/11/2026 20:00")
        sel = seleccion.elegir_candidatas([vieja, nueva], TODOS, [])
        self.assertEqual([n["titulo"] for n in sel["candidatas"]], ["Nueva", "Vieja"])
        self.assertEqual(sel["motivos"], {nueva["link"]: ["frescura"]})
        self.assertEqual((sel["encajan"], sel["pedido_sin_notas"]), ([], False))


class Eleccion(unittest.TestCase):
    def test_tema_destildado_nunca_entra_aunque_el_pedido_lo_nombre(self):
        prefs = {"indicadores": [], "temas": ["Política"]}
        deporte = nota("River gana", seccion="Deportes")
        politica = nota("El Gobierno anunció", seccion="Política")
        sel = seleccion.elegir_candidatas([deporte, politica], prefs, seleccion.terminos_del_pedido("River"))
        self.assertEqual(sel["candidatas"], [politica])
        self.assertTrue(sel["pedido_sin_notas"])  # el pedido solo habla de un tema destildado

    def test_pedido_sin_notas_en_los_tres_casos(self):
        notas = [nota("River gana")]
        self.assertFalse(seleccion.elegir_candidatas(notas, TODOS, ["river"])["pedido_sin_notas"])
        self.assertTrue(seleccion.elegir_candidatas(notas, TODOS, ["tenis"])["pedido_sin_notas"])
        prefs = {"indicadores": [], "temas": ["Política"]}
        self.assertTrue(seleccion.elegir_candidatas(notas, prefs, ["river"])["pedido_sin_notas"])

    def test_tope_por_medio_y_seccion(self):
        notas = [nota(f"Nota {n}", fecha=f"17/11/2026 {10 + n:02d}:00") for n in range(6)]
        notas.append(nota("Otra seccion", seccion="Política"))
        sel = seleccion.elegir_candidatas(notas, TODOS, [], tope_por_medio_y_seccion=2)
        self.assertEqual(sorted(n["titulo"] for n in sel["candidatas"]), ["Nota 4", "Nota 5", "Otra seccion"])

    def test_maximo_de_40(self):
        notas = [nota(f"Nota {n}", fecha=f"17/11/2026 {n // 60:02d}:{n % 60:02d}", medio=f"M{n}") for n in range(60)]
        sel = seleccion.elegir_candidatas(notas, TODOS, [])
        self.assertEqual(len(sel["candidatas"]), MAXIMO_CANDIDATAS_PARA_CLAUDE)
        self.assertEqual(MAXIMO_CANDIDATAS_PARA_CLAUDE, 40)

    def test_desempate_estable_por_fecha_y_luego_link(self):
        a = nota("A", link="https://x.test/a")
        b = nota("B", link="https://x.test/b")
        c = nota("C", link="https://x.test/c", fecha="17/11/2026 11:00")
        orden = [n["link"] for n in seleccion.elegir_candidatas([c, b, a], TODOS, [])["candidatas"]]
        self.assertEqual(orden, ["https://x.test/c", "https://x.test/a", "https://x.test/b"])
        self.assertEqual(orden, [n["link"] for n in seleccion.elegir_candidatas([a, c, b], TODOS, [])["candidatas"]])

    def test_es_determinista(self):
        notas = [nota("River gana", fecha="17/11/2026 08:00"), nota("Boca pierde"), nota("Tenis")]
        terminos = seleccion.terminos_del_pedido("fútbol argentino")
        self.assertEqual(seleccion.elegir_candidatas(notas, TODOS, terminos),
                         seleccion.elegir_candidatas(notas, TODOS, terminos))


PERFIL = {"secciones": {}, "medios": {}, "terminos": {}, "votos_contados": 0}


def _perfil(**kw):
    return {**PERFIL, **kw}


class ConPerfil(unittest.TestCase):
    def test_el_medio_muy_votado_sube_frente_a_otro_con_igual_frescura(self):
        a = nota("Nota uno", medio="Medio A")
        b = nota("Nota dos", medio="Medio B", fecha=a["fecha"])
        perfil = _perfil(medios={"Medio B": 5.0})
        r = seleccion.elegir_candidatas([a, b], TODOS, [], perfil)
        self.assertEqual(r["candidatas"][0]["medio"], "Medio B")
        self.assertIn("medio que te gusta", r["motivos"][b["link"]])

    def test_sin_perfil_o_con_perfil_vacio_no_cambia_nada(self):
        notas = [nota("Nota uno"), nota("Nota dos", fecha="17/11/2026 11:00")]
        base = seleccion.puntuar(notas, TODOS, [])
        self.assertEqual(seleccion.puntuar(notas, TODOS, [], PERFIL), base)

    def test_un_termino_parecido_suma_con_su_motivo(self):
        n = nota("Messi vuelve a jugar")
        r = seleccion.puntuar([n], TODOS, [], _perfil(terminos={"messi": 2.5}))
        self.assertIn("te gustó algo parecido", r[0]["motivos"])
        self.assertGreater(r[0]["puntaje"], 0)

    def test_el_pedido_le_gana_al_perfil_maximo(self):
        encaja = nota("Algo de tenis", medio="Medio A", fecha="17/11/2026 08:00", categorias=["tenis"])
        favorita = nota("Otra cosa", medio="Medio B", fecha="17/11/2026 22:00")
        perfil = _perfil(medios={"Medio B": 5.0}, terminos={"otra": 5.0, "cosa": 5.0})
        r = seleccion.elegir_candidatas([favorita, encaja], TODOS, ["tenis"], perfil)
        self.assertEqual(r["candidatas"][0], encaja)

    def test_el_perfil_no_rehabilita_un_tema_destildado(self):
        n = nota("Boca", seccion="Deportes", medio="Medio B")
        prefs = {"indicadores": [], "temas": ["Política"]}
        r = seleccion.elegir_candidatas([n], prefs, [], _perfil(medios={"Medio B": 5.0}, secciones={"Deportes": 5.0}))
        self.assertEqual(r["candidatas"], [])
        self.assertEqual(_plan([n], temas=["Política"], pesos=seleccion.pesos_de_secciones(_perfil(secciones={"Deportes": 5.0}))), [])

    def test_pesos_de_secciones_del_perfil(self):
        pesos = seleccion.pesos_de_secciones(_perfil(secciones={"Deportes": 5.0, "Política": -5.0, "Otra": 3.0}))
        self.assertAlmostEqual(pesos["Deportes"], 2.0)
        self.assertGreater(pesos["Política"], 0)
        self.assertLess(pesos["Política"], 1.0)
        self.assertNotIn("Otra", pesos)
        self.assertEqual(seleccion.pesos_de_secciones(None), {})

    def test_el_plan_reparte_mas_al_tema_que_te_gusta_y_lo_explica(self):
        candidatas = [n for t in ("Deportes", "Política") for n in _muchas(t)]
        pesos = seleccion.pesos_de_secciones(_perfil(secciones={"Deportes": 5.0}))
        plan = _plan(candidatas, temas=["Deportes", "Política"], pesos=pesos)
        cupos = _cupos(plan)
        self.assertGreater(cupos["Deportes"], cupos["Política"])
        deportes = next(c for c in plan if c["seccion"] == "Deportes")
        self.assertIn("tema que te gusta", deportes["motivos"])

    def test_terminos_de_titulo(self):
        self.assertEqual(seleccion.terminos_de_titulo("El Boca de Riquelme: ¡Boca ganó!"), ["boca", "riquelme", "gano"])


def _plan(candidatas, temas=None, pesos=None, tope=3, **kwargs):
    return seleccion.plan_de_secciones(candidatas, list(TEMAS) if temas is None else temas, pesos, tope, **kwargs)


def _cupos(plan):
    return {c["seccion"]: c["cupo"] for c in plan}


def _muchas(seccion, medios=4, por_medio=3):
    return [nota(f"{seccion} {m} {i}", seccion=seccion, medio=f"Medio {m}") for m in range(medios) for i in range(por_medio)]


class PlanDeSecciones(unittest.TestCase):
    def test_solo_deportes_con_12_candidatas_de_4_medios_da_9(self):
        plan = _plan(_muchas("Deportes"), temas=["Deportes"])
        self.assertEqual(_cupos(plan), {"Deportes": 9})
        self.assertTrue(seleccion.plan_completo(plan))

    def test_secciones_destildadas_o_sin_candidatas_no_entran(self):
        candidatas = _muchas("Deportes") + _muchas("Economía")
        self.assertEqual(list(_cupos(_plan(candidatas, temas=["Deportes", "Política"]))), ["Deportes"])

    def test_con_cinco_temas_suma_el_objetivo_y_cada_uno_tiene_al_menos_uno(self):
        candidatas = [n for t in TEMAS for n in _muchas(t)]
        plan = _plan(candidatas)
        self.assertEqual(sum(_cupos(plan).values()), NOTAS_OBJETIVO)
        self.assertEqual(list(_cupos(plan)), list(TEMAS))  # en el orden de TEMAS
        self.assertTrue(all(c >= MINIMO_POR_SECCION_ACTIVA for c in _cupos(plan).values()))

    def test_una_seccion_con_notas_pedidas_recibe_mas_cupo(self):
        candidatas = [n for t in TEMAS for n in _muchas(t)]
        sin = _cupos(_plan(candidatas))
        pedidas = {n["link"] for n in candidatas if n["seccion"] == "Economía"}
        con_plan = _plan(candidatas, pedidas=pedidas)
        self.assertGreater(_cupos(con_plan)["Economía"], sin["Economía"])
        self.assertEqual(sum(_cupos(con_plan).values()), NOTAS_OBJETIVO)
        self.assertTrue(any("pedido" in m for m in next(c for c in con_plan if c["seccion"] == "Economía")["motivos"]))

    def test_con_pocas_candidatas_pide_como_mucho_las_que_hay_y_queda_incompleto(self):
        candidatas = [nota(f"n{i}", seccion=("Deportes" if i < 3 else "Economía"), medio=f"M{i}") for i in range(5)]
        plan = _plan(candidatas)
        self.assertEqual(sum(_cupos(plan).values()), 5)
        self.assertFalse(seleccion.plan_completo(plan))

    def test_un_medio_con_tope_3_no_pasa_de_3_en_total(self):
        candidatas = [nota(f"{t} {i}", seccion=t, medio="Unico") for t in ("Política", "Economía") for i in range(5)]
        plan = _plan(candidatas)
        self.assertEqual(sum(_cupos(plan).values()), 3)
        self.assertFalse(seleccion.plan_completo(plan))

    def test_el_lunes_el_tope_es_5(self):
        candidatas = [nota(f"{t} {i}", seccion=t, medio="Unico") for t in ("Política", "Economía") for i in range(5)]
        self.assertEqual(sum(_cupos(_plan(candidatas, tope=5)).values()), 5)

    def test_es_determinista(self):
        candidatas = [n for t in TEMAS for n in _muchas(t)]
        self.assertEqual(_plan(candidatas), _plan(list(reversed(candidatas))))
        self.assertEqual(_plan(candidatas), _plan(candidatas))

    def test_sin_candidatas_el_plan_es_vacio_e_incompleto(self):
        self.assertEqual(_plan([]), [])
        self.assertFalse(seleccion.plan_completo([]))

    def test_orden_de_recorte_va_de_menor_a_mayor_prioridad(self):
        plan = [{"seccion": "Política", "cupo": 2, "pedidas": 0, "motivos": []},
                {"seccion": "Economía", "cupo": 3, "pedidas": 2, "motivos": []},
                {"seccion": "Deportes", "cupo": 2, "pedidas": 0, "motivos": []},
                {"seccion": "Tecnología", "cupo": 1, "pedidas": 0, "motivos": []}]
        self.assertEqual(seleccion.orden_de_recorte(plan), ["Tecnología", "Deportes", "Política", "Economía"])


class OrdenParaLaPagina(unittest.TestCase):
    """Spec 42: la lista "Noticias de ayer" va en el orden del servidor, con motivos y sin puntaje."""

    def test_ordena_por_puntaje_y_agrega_motivos_sin_descartar_nada(self):
        otra = nota("Tenis en Australia", fecha="17/11/2026 22:00")
        river = nota("River goleó", fecha="17/11/2026 08:00")
        vieja = nota("Nada que ver", fecha="17/11/2026 07:00")
        salida = seleccion.ordenar_por_puntaje([otra, vieja, river], seleccion.terminos_del_pedido("river"))
        self.assertEqual([n["titulo"] for n in salida], ["River goleó", "Tenis en Australia", "Nada que ver"])
        self.assertTrue(salida[0]["motivos"][0].startswith("pedido:"))
        self.assertEqual(salida[2]["motivos"], [])
        self.assertNotIn("puntaje", salida[0])
        self.assertNotIn("motivos", river)  # no toca las notas originales

    def test_lista_vacia(self):
        self.assertEqual(seleccion.ordenar_por_puntaje([], []), [])


class TemasDestildados(unittest.TestCase):
    def test_nombra_el_tema_o_su_clave_y_solo_si_esta_destildado(self):
        sin_tecnologia = [t for t in TEMAS if t != "Tecnología"]
        self.assertEqual(seleccion.temas_destildados_nombrados("TECNOLOGIA hoy", sin_tecnologia), ["Tecnología"])
        self.assertEqual(seleccion.temas_destildados_nombrados("tecnología", list(TEMAS)), [])
        self.assertEqual(seleccion.temas_destildados_nombrados("fútbol argentino", ["Política"]), ["Deportes"])
        self.assertEqual(seleccion.temas_destildados_nombrados("Internacional", ["Política"]), ["Internacional"])

    def test_sin_pedido_o_sin_tema_da_vacio(self):
        self.assertEqual(seleccion.temas_destildados_nombrados(None, []), [])
        self.assertEqual(seleccion.temas_destildados_nombrados("messi", []), [])


class PlanConTemasNuevos(unittest.TestCase):
    def test_con_todos_los_temas_tildados_suma_el_objetivo_y_respeta_el_minimo(self):
        candidatas = [n for t in TEMAS for n in _muchas(t)]
        plan = _plan(candidatas)
        self.assertEqual(sum(_cupos(plan).values()), NOTAS_OBJETIVO)
        self.assertEqual(list(_cupos(plan)), list(TEMAS))
        self.assertTrue(all(c >= MINIMO_POR_SECCION_ACTIVA for c in _cupos(plan).values()))

    def test_temas_nuevos_sin_candidatas_no_entran(self):
        candidatas = _muchas("Política") + _muchas("Sociedad")
        self.assertEqual(list(_cupos(_plan(candidatas))), ["Política", "Sociedad"])

    def test_si_el_minimo_no_alcanza_se_quedan_las_secciones_de_mas_peso(self):
        # Con un objetivo de 2 notas y 4 secciones activas, entran las dos de más peso.
        candidatas = [n for t in ("Política", "Sociedad", "Deportes", "Tecnología") for n in _muchas(t)]
        pesos = {"Tecnología": 3.0, "Deportes": 2.0}
        plan = _plan(candidatas, pesos=pesos, total=2)
        self.assertEqual(_cupos(plan), {"Deportes": 1, "Tecnología": 1})

    def test_pedido_con_sinonimos_de_los_temas_nuevos(self):
        self.assertIn("policia", seleccion.terminos_del_pedido("policiales"))
        self.assertIn("conicet", seleccion.terminos_del_pedido("ciencia"))
        self.assertIn("museo", seleccion.terminos_del_pedido("cultura"))

    def test_aviso_de_tema_nuevo_destildado(self):
        base = ["Política"]
        self.assertEqual(seleccion.temas_destildados_nombrados("ciencia", base), ["Salud y Ciencia"])
        self.assertEqual(seleccion.temas_destildados_nombrados("salud", base), ["Salud y Ciencia"])
        self.assertEqual(seleccion.temas_destildados_nombrados("espectáculos", base), ["Espectáculos y Cultura"])
        self.assertEqual(seleccion.temas_destildados_nombrados("Sociedad", base), ["Sociedad"])
        self.assertEqual(seleccion.temas_destildados_nombrados("ciencia", ["Salud y Ciencia"]), [])


class PorSubtema(unittest.TestCase):
    """Spec 45: el pedido suma por el subtema de la nota."""

    def test_pedido_de_subtema_suma_y_deja_el_motivo(self):
        con = {**nota("Se definió la fecha"), "subtema": "Fútbol argentino"}
        sin = nota("Se definió otra cosa", fecha="17/11/2026 12:00")
        puntuadas = seleccion.puntuar([con, sin], None, seleccion.terminos_del_pedido("fútbol argentino"))
        self.assertIn("pedido: futbol argentino (subtema)", puntuadas[0]["motivos"])
        self.assertTrue(puntuadas[0]["encaja"])
        self.assertFalse(any("subtema" in m for m in puntuadas[1]["motivos"]))
        self.assertGreaterEqual(puntuadas[0]["puntaje"], PESOS_PUNTAJE["subtema"])

    def test_subtema_y_titulo_suman_ambos(self):
        solo = {**nota("Gran nota"), "subtema": "Tenis"}
        ambos = {**nota("Final de tenis"), "subtema": "Tenis"}
        p = seleccion.puntuar([solo, ambos], None, ["tenis"])
        self.assertEqual(p[1]["puntaje"] - p[0]["puntaje"], PESOS_PUNTAJE["titulo"])

    def test_el_pedido_por_subtema_le_gana_al_perfil(self):
        self.assertGreater(PESOS_PUNTAJE["subtema"], 0)
        self.assertEqual(seleccion.temas_destildados_nombrados("tenis", ["Política"]), ["Deportes"])


# --- Preferencias v2 (spec 49) ---------------------------------------------------

def _prefs(temas=None, prioridades=None, subtemas=None, preferidos=(), excluidos=(), seguir=(), evitar=()):
    activos = list(TEMAS) if temas is None else temas
    return {"version": 2, "indicadores": [], "subtemas": list(subtemas or []),
            "temas": {t: {"activo": t in activos, "prioridad": (prioridades or {}).get(t, "normal")} for t in TEMAS},
            "medios": {"preferidos": list(preferidos), "excluidos": list(excluidos)},
            "palabras": {"seguir": list(seguir), "evitar": list(evitar)}}


def _puntos(notas, prefs, terminos=()):
    return {p["nota"]["link"]: p for p in seleccion.puntuar(notas, prefs, list(terminos))}


class PreferenciasEnLaSeleccion(unittest.TestCase):
    def test_medio_excluido_nunca_entra_ni_a_las_candidatas_ni_a_la_lista(self):
        malo = nota("River gana", medio="Perfil", link="https://x.test/p")
        bueno = nota("Boca gana", medio="Infobae", link="https://x.test/i")
        prefs = _prefs(excluidos=["Perfil"])
        sel = seleccion.elegir_candidatas([malo, bueno], prefs, seleccion.terminos_del_pedido("river"))
        self.assertEqual(sel["candidatas"], [bueno])
        self.assertTrue(sel["pedido_sin_notas"])  # el pedido solo encajaba con un medio excluido
        lista = seleccion.ordenar_por_puntaje([malo, bueno], [], None, prefs)
        self.assertEqual([n["link"] for n in lista], [bueno["link"]])

    def test_medio_preferido_suma_con_su_motivo(self):
        a, b = nota("Una", medio="Infobae", link="https://x.test/a"), nota("Otra", medio="Perfil", link="https://x.test/b")
        puntos = _puntos([a, b], _prefs(preferidos=["Infobae"]))
        self.assertEqual(puntos[a["link"]]["puntaje"] - puntos[b["link"]]["puntaje"], config.PESO_MEDIO_PREFERIDO)
        self.assertIn("medio preferido", puntos[a["link"]]["motivos"])
        self.assertNotIn("medio preferido", puntos[b["link"]]["motivos"])

    def test_palabras_a_seguir_y_a_evitar_sin_tildes_ni_mayusculas_y_en_titulo_bajada_o_categoria(self):
        sigue = nota("BOCA ganó", link="https://x.test/s")
        sigue_bajada = nota("Gana otro", bajada="Fue Boca", link="https://x.test/sb")
        evita = nota("Farandula total", link="https://x.test/e")
        evita_categoria = nota("Algo", categorias=["Farándula"], link="https://x.test/ec")
        neutra = nota("Riverside inaugura", link="https://x.test/n")
        puntos = _puntos([sigue, sigue_bajada, evita, evita_categoria, neutra], _prefs(seguir=["boca"], evitar=["FARÁNDULA"]))
        self.assertIn("palabra a seguir", puntos[sigue["link"]]["motivos"])
        self.assertIn("palabra a seguir", puntos[sigue_bajada["link"]]["motivos"])
        self.assertIn("palabra a evitar", puntos[evita["link"]]["motivos"])
        self.assertIn("palabra a evitar", puntos[evita_categoria["link"]]["motivos"])
        self.assertEqual(puntos[neutra["link"]]["motivos"], [])
        self.assertGreater(puntos[sigue["link"]]["puntaje"], 0)
        self.assertLess(puntos[evita["link"]]["puntaje"], 0)
        sel = seleccion.elegir_candidatas([evita, sigue, neutra], _prefs(seguir=["boca"], evitar=["farandula"]), [])
        self.assertEqual(sel["candidatas"], [sigue, neutra, evita])  # la que se evita baja pero no se descarta

    def test_palabra_a_seguir_es_una_palabra_y_no_un_pedazo(self):
        puntos = _puntos([nota("Riverside inaugura")], _prefs(seguir=["river"]))
        self.assertEqual(list(puntos.values())[0]["motivos"], [])

    def test_subtemas_elegidos_suman_y_no_elegidos_restan_solo_en_deportes(self):
        tenis = {**nota("A", link="https://x.test/t"), "subtema": "Tenis"}
        futbol = {**nota("B", link="https://x.test/f"), "subtema": "Fútbol argentino"}
        sin_subtema = nota("C", link="https://x.test/o")  # sin el campo cuenta como "Otros"
        politica = nota("D", seccion="Política", link="https://x.test/p")
        puntos = _puntos([tenis, futbol, sin_subtema, politica], _prefs(subtemas=["Tenis"]))
        self.assertIn("subtema elegido", puntos[tenis["link"]]["motivos"])
        self.assertIn("subtema no elegido", puntos[futbol["link"]]["motivos"])
        self.assertIn("subtema no elegido", puntos[sin_subtema["link"]]["motivos"])
        self.assertEqual(puntos[politica["link"]]["motivos"], [])
        otros = _puntos([sin_subtema], _prefs(subtemas=["Otros"]))
        self.assertIn("subtema elegido", otros[sin_subtema["link"]]["motivos"])
        self.assertEqual(_puntos([tenis], _prefs())[tenis["link"]]["motivos"], [])  # sin subtemas elegidos, no hay efecto

    def test_el_aporte_de_las_preferencias_esta_acotado(self):
        n = {**nota("Boca farandula", medio="Infobae"), "subtema": "Tenis"}
        todo_a_favor = _puntos([nota("Boca gana", medio="Infobae")],
                               _prefs(preferidos=["Infobae"], seguir=["boca", "gana"], subtemas=["Otros"]))
        self.assertLessEqual(list(todo_a_favor.values())[0]["puntaje"], config.MAXIMO_PUNTAJE_PREFERENCIAS)
        todo_en_contra = _puntos([n], _prefs(evitar=["boca"], subtemas=["Fútbol argentino"]))
        self.assertGreaterEqual(list(todo_en_contra.values())[0]["puntaje"], -config.MAXIMO_PUNTAJE_PREFERENCIAS)

    def test_el_pedido_sigue_primero_aunque_otra_nota_tenga_todas_las_preferencias_a_favor(self):
        encaja = nota("River gana", fecha="17/11/2026 08:00", medio="Perfil", link="https://x.test/pedido",
                      categorias=["River"])
        encaja = {**encaja, "titulo": "Se juega algo", "bajada": ""}  # solo encaja por categoría: el peso mínimo del pedido
        favorita = nota("Boca y Messi", fecha="17/11/2026 22:00", medio="Infobae", link="https://x.test/fav")
        prefs = _prefs(preferidos=["Infobae"], seguir=["Boca", "Messi"], excluidos=[])
        perfil = {"medios": {"Infobae": 5.0}, "terminos": {"boca": 5.0, "messi": 5.0}, "secciones": {}, "votos_contados": 3}
        sel = seleccion.elegir_candidatas([favorita, encaja], prefs, ["river"], perfil)
        self.assertEqual(sel["candidatas"][0], encaja)
        lista = seleccion.ordenar_por_puntaje([favorita, encaja], ["river"], perfil, prefs)
        self.assertEqual(lista[0]["link"], encaja["link"])

    def test_el_perfil_sigue_sumando_encima_de_las_preferencias(self):
        a, b = nota("Una nota", link="https://x.test/a", medio="Infobae"), nota("Una nota", link="https://x.test/b", medio="Infobae")
        perfil = {"medios": {"Infobae": 5.0}, "terminos": {}, "secciones": {}, "votos_contados": 1}
        sin = _puntos([a], _prefs(preferidos=["Infobae"]))[a["link"]]["puntaje"]
        con = {p["nota"]["link"]: p for p in seleccion.puntuar([b], _prefs(preferidos=["Infobae"]), [], perfil)}[b["link"]]
        self.assertGreater(con["puntaje"], sin)
        self.assertIn("medio que te gusta", con["motivos"])

    def test_un_tema_destildado_no_se_rehabilita_por_medio_preferido_ni_palabra_a_seguir(self):
        politica = nota("Boca en el Congreso", seccion="Política", medio="Infobae")
        sel = seleccion.elegir_candidatas([politica], _prefs(temas=["Deportes"], preferidos=["Infobae"], seguir=["Boca"]),
                                          seleccion.terminos_del_pedido("Boca"))
        self.assertEqual(sel["candidatas"], [])
        self.assertTrue(sel["pedido_sin_notas"])

    def test_con_el_formato_viejo_en_las_prefs_no_suma_nada(self):
        puntos = _puntos([nota("Boca gana")], TODOS)
        self.assertEqual(list(puntos.values())[0]["motivos"], [])


class PrioridadDeTemaEnElPlan(unittest.TestCase):
    CANDIDATAS = _muchas("Deportes") + _muchas("Política")

    def test_alta_da_mas_notas_que_normal_y_baja_menos(self):
        base = _cupos(_plan(self.CANDIDATAS, temas=["Deportes", "Política"]))
        alta = _cupos(_plan(self.CANDIDATAS, temas=["Deportes", "Política"], prioridades={"Deportes": "alta"}))
        baja = _cupos(_plan(self.CANDIDATAS, temas=["Deportes", "Política"], prioridades={"Deportes": "baja"}))
        self.assertGreater(alta["Deportes"], base["Deportes"])
        self.assertLess(baja["Deportes"], base["Deportes"])
        self.assertEqual(sum(alta.values()), sum(base.values()))

    def test_el_plan_anota_la_prioridad_y_el_recorte_empieza_por_la_baja(self):
        plan = _plan(self.CANDIDATAS, temas=["Deportes", "Política"], prioridades={"Política": "baja"})
        por_tema = {c["seccion"]: c for c in plan}
        self.assertEqual(por_tema["Política"]["prioridad"], "baja")
        self.assertNotIn("prioridad", por_tema["Deportes"])
        self.assertIn("prioridad baja", por_tema["Política"]["motivos"])
        self.assertEqual(seleccion.orden_de_recorte(plan)[0], "Política")

    def test_a_igual_cupo_la_baja_se_recorta_antes_que_la_normal_y_la_alta_al_final(self):
        plan = [{"seccion": "Política", "cupo": 3, "pedidas": 0, "motivos": [], "prioridad": "alta"},
                {"seccion": "Economía", "cupo": 3, "pedidas": 0, "motivos": []},
                {"seccion": "Deportes", "cupo": 3, "pedidas": 0, "motivos": [], "prioridad": "baja"}]
        self.assertEqual(seleccion.orden_de_recorte(plan), ["Deportes", "Economía", "Política"])

    def test_se_combina_con_el_perfil(self):
        pesos = {"Deportes": 2.0}
        base = _cupos(_plan(self.CANDIDATAS, temas=["Deportes", "Política"], pesos=pesos))
        con_baja = _cupos(_plan(self.CANDIDATAS, temas=["Deportes", "Política"], pesos=pesos, prioridades={"Deportes": "baja"}))
        self.assertLess(con_baja["Deportes"], base["Deportes"])


if __name__ == "__main__":
    unittest.main()
