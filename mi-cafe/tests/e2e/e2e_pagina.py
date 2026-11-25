"""Pruebas de punta a punta de la página de Mi Café (spec 26). Solo para desarrollo.

Necesita Playwright (ver README.md) y el servidor de pruebas andando: usar tests/e2e/correr_e2e.sh,
que lo levanta con with_server.py, datos temporales y fuentes simuladas.
No lo recoge `unittest discover` (el nombre no empieza con "test").

Falla si la consola del navegador muestra errores o si la página pide algo fuera de localhost.
"""

import os
import sys
import traceback
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("MICAFE_E2E_URL", "http://127.0.0.1:8765")
LINK_1 = "https://www.ejemplo-diario.com.ar/politica/nota-uno"


def caso_carga(page):
    expect(page).to_have_title("Mi Café")
    expect(page.locator("h1")).to_have_text("Mi Café")
    expect(page.locator("#lista-indicadores li")).to_have_count(2)
    expect(page.locator("#resumen h3").first).to_have_text("Política")


def caso_indicadores_con_fecha_y_fuente(page):
    fila = page.locator("#lista-indicadores li", has_text="Dólar oficial")
    expect(fila.locator(".ind-valor")).to_have_text("$ 1.234,50")
    expect(fila.locator(".ind-meta")).to_have_text("17/11/2026 · DolarApi")


def caso_sin_dato_visible(page):
    fila = page.locator("#lista-indicadores li", has_text="Riesgo país")
    expect(fila.locator(".ind-valor")).to_have_text("sin dato")
    expect(fila.locator(".ind-meta")).to_have_text("ArgentinaDatos")


def caso_nota_con_enlace(page):
    enlace = page.locator("#lista-noticias a", has_text="Debate en el Congreso")
    expect(enlace).to_have_attribute("href", LINK_1)
    expect(page.locator("#resumen a.enlace").first).to_have_attribute("href", LINK_1)


def caso_voto(page):
    boton = page.locator(f'#lista-noticias button[data-clave="{LINK_1}"][data-voto="me_gusta"]')
    expect(boton).to_have_attribute("aria-pressed", "false")
    boton.click()
    expect(page.locator("#estado-gustos")).to_have_text("Voto guardado.")
    expect(boton).to_have_attribute("aria-pressed", "true")
    no_me_gusta = page.locator(f'#lista-noticias button[data-clave="{LINK_1}"][data-voto="no_me_gusta"]')
    no_me_gusta.click()
    expect(no_me_gusta).to_have_attribute("aria-pressed", "true")
    expect(boton).to_have_attribute("aria-pressed", "false")
    no_me_gusta.click()  # repetir lo quita (y deja los datos temporales como estaban)
    expect(page.locator("#estado-gustos")).to_have_text("Voto quitado.")


def caso_caja_de_preguntas(page):
    expect(page.locator("#caja-preguntas")).to_be_hidden()
    page.locator("button.titulo-nota", has_text="Debate en el Congreso").click()
    expect(page.locator("#nota-elegida")).to_contain_text("Debate en el Congreso por el presupuesto")
    page.locator("#pregunta").fill("¿De qué trata?")
    page.locator("#boton-pregunta").click()
    expect(page.locator("#respuesta-pregunta")).to_contain_text(
        "Según la nota, el debate trata sobre el gasto del año próximo.")
    expect(page.locator("#respuesta-pregunta a")).to_have_attribute("href", LINK_1)


def caso_aviso_de_fuente_caida(page):
    expect(page.locator("#avisos-indicadores")).to_contain_text("No se pudo consultar ArgentinaDatos")
    expect(page.locator("#avisos-noticias")).to_contain_text("No se pudo leer el feed de Medio Caído (Deportes)")


def caso_aviso_del_corrector(page):
    expect(page.locator("#aviso-corrector")).to_be_visible()
    expect(page.locator("#aviso-corrector")).to_contain_text(
        "Aviso del corrector: el resumen no cumple estas reglas: Una nota repite un tema de ayer.")


def caso_pedido_contador_y_error_del_servidor(page):
    cuadro = page.locator("#pedido-noticias")
    expect(page.locator("label[for=pedido-noticias]")).to_contain_text("¿Qué noticias querés ver hoy?")
    cuadro.fill("a" * 600)  # maxlength corta en 500
    expect(page.locator("#contador-pedido")).to_have_text("500/500")
    cuadro.evaluate("(el) => { el.value = 'a'.repeat(501); }")  # saltea maxlength, como un pegado de afuera
    page.locator("#boton-resumen").click()
    expect(page.locator("#estado-resumen")).to_contain_text("El pedido es muy largo (máximo 500 caracteres).")
    expect(cuadro).to_be_enabled()
    expect(page.locator("#boton-resumen")).to_be_enabled()
    assert len(cuadro.input_value()) == 501  # el texto se conserva


def caso_pedido_se_manda_se_guarda_y_se_vacia(page):
    """Corre al final: el armado simulado reemplaza el resumen guardado."""
    cuadro = page.locator("#pedido-noticias")
    cuadro.fill("  <b>más economía</b>  ")
    with page.expect_request(lambda r: r.url.endswith("/api/resumen") and r.method == "POST") as pedido:
        page.locator("#boton-resumen").click()
    assert pedido.value.post_data_json == {"pedido": "<b>más economía</b>"}
    expect(cuadro).to_be_disabled()
    expect(page.locator("#boton-resumen")).to_be_disabled()
    expect(page.locator("#cabecera-resumen")).to_contain_text('Pedido de hoy: "<b>más economía</b>"', timeout=15000)
    expect(page.locator("#cabecera-resumen b")).to_have_count(0)
    expect(cuadro).to_be_enabled()
    expect(cuadro).to_have_value("")


def caso_pedido_sin_texto_no_manda_el_campo(page):
    with page.expect_request(lambda r: r.url.endswith("/api/resumen") and r.method == "POST") as pedido:
        page.locator("#boton-resumen").click()
    assert pedido.value.post_data in (None, "")


def caso_pedido_en_cabecera_escapado(page):
    resumen = {"fecha": "2026-11-18", "generado_en": "18/11/2026 08:00", "texto": "Política\n",
               "indicadores": [], "chequeo": {"aprobado": True, "no_cumple": []},
               "pedido": "<b>hola</b>", "notas": []}
    page.route("**/api/resumen", lambda ruta: ruta.fulfill(
        json={"resumen": resumen}) if ruta.request.method == "GET" else ruta.continue_())
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#cabecera-resumen")).to_contain_text('Pedido de hoy: "<b>hola</b>"')
    expect(page.locator("#cabecera-resumen b")).to_have_count(0)


RESUMEN_CON_PLAN = {
    "fecha": "2026-11-18", "generado_en": "18/11/2026 08:00", "texto": "Política\n", "indicadores": [],
    "chequeo": {"aprobado": True, "no_cumple": []}, "notas": [], "pedido": "<b>fútbol</b>",
    "pedido_sin_notas": True, "temas_destildados_pedido": ["Deportes"],
    "plan": {"secciones": [{"seccion": "Política", "cupo": 4, "pedidas": 0, "motivos": []},
                           {"seccion": "Economía", "cupo": 1, "pedidas": 0, "motivos": []}], "completo": False},
}


def _recargar_con_resumen(page, resumen):
    page.route("**/api/resumen", lambda ruta: ruta.fulfill(
        json={"resumen": resumen}) if ruta.request.method == "GET" else ruta.continue_())
    page.reload()
    page.wait_for_load_state("networkidle")


def caso_aviso_de_pedido_sin_notas_y_tema_destildado(page):
    _recargar_con_resumen(page, RESUMEN_CON_PLAN)
    aviso = page.locator("#aviso-pedido")
    expect(aviso).to_contain_text("Tu pedido no encontró notas de ayer.")
    expect(aviso).to_contain_text("Ese tema está destildado en tus preferencias.")
    assert aviso.get_attribute("role") == "status"
    aviso.get_by_role("button", name="Ir a preferencias").click()
    expect(page.locator("#preferencias")).to_be_visible()
    assert page.url.endswith("#preferencias")
    expect(page.locator("#pref-temas .fila-tema", has_text="Deportes").locator("input[type=checkbox]")).to_be_focused()
    expect(page.locator("#cabecera-resumen b")).to_have_count(0)


def caso_como_se_armo_con_teclado(page):
    _recargar_con_resumen(page, RESUMEN_CON_PLAN)
    resumen = page.locator("#como-se-armo summary")
    expect(resumen).to_have_text("Cómo se armó hoy")
    resumen.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#como-se-armo")).to_have_attribute("open", "")
    expect(page.locator("#como-se-armo-contenido")).to_contain_text("Política: 4 notas")
    expect(page.locator("#como-se-armo-contenido")).to_contain_text("Economía: 1 nota")
    expect(page.locator("#como-se-armo-contenido")).to_contain_text("El plan quedó incompleto")
    page.keyboard.press("Space")
    expect(page.locator("#como-se-armo")).not_to_have_attribute("open", "")


def caso_resumen_viejo_sin_plan_no_muestra_el_bloque(page):
    viejo = {k: v for k, v in RESUMEN_CON_PLAN.items() if k not in ("plan", "pedido_sin_notas", "temas_destildados_pedido")}
    _recargar_con_resumen(page, viejo)
    expect(page.locator("#como-se-armo")).to_be_hidden()
    expect(page.locator("#aviso-pedido")).to_be_hidden()


def caso_etiquetas_y_secciones_del_servidor(page):
    nota = {"titulo": "<i>River</i> gana", "medio": "<b>Medio</b>", "seccion": "Deportes",
            "fecha": "17/11/2026 10:00", "link": LINK_1, "motivos": ["pedido: river (titulo)", "medio que te gusta", "palabra a evitar", "subtema no elegido"]}
    page.route("**/api/noticias", lambda ruta: ruta.fulfill(json={"notas": [nota], "fallas": []}))
    page.reload()
    page.wait_for_load_state("networkidle")
    etiquetas = page.locator("#lista-noticias .etiqueta")
    expect(etiquetas).to_have_text(
        ["Por tu pedido", "Medio que te gusta", "Palabra que evitás", "Subtema que no elegiste"])
    expect(page.locator("#lista-noticias i, #lista-noticias b")).to_have_count(0)
    secciones = page.request.get(URL + "/api/preferencias").json()["opciones"]["secciones"]
    expect(page.locator("#pref-temas .fila-tema")).to_have_count(len(secciones))
    expect(page.locator("#pref-temas .fila-tema", has_text="Internacional")).to_have_count(1)


# --- Spec 50: pantalla de Preferencias ---------------------------------------------

def _abrir_preferencias(page):
    page.get_by_role("link", name="Preferencias").click()
    expect(page.locator("#preferencias")).to_be_visible()
    expect(page.locator("#pref-temas .fila-tema").first).to_be_visible()


def _fila(page, tema):
    return page.locator("#pref-temas .fila-tema", has_text=tema)


def caso_prefs_abre_con_boton_vuelve_y_atras(page):
    expect(page.locator("#preferencias")).to_be_hidden()
    expect(page.locator("#resumen-prefs")).to_contain_text("Temas: Política")
    boton = page.get_by_role("link", name="Preferencias")
    boton.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#preferencias")).to_be_visible()
    expect(page.locator("#vista-resumen")).to_be_hidden()
    assert page.url.endswith("#preferencias")
    expect(page.locator("#titulo-preferencias")).to_be_focused()
    page.get_by_role("button", name="Volver al resumen").click()
    expect(page.locator("#vista-resumen")).to_be_visible()
    expect(page.locator("#resumen h3").first).to_have_text("Política")
    expect(boton).to_be_focused()
    page.go_back()
    expect(page.locator("#preferencias")).to_be_visible()
    page.go_forward()
    expect(page.locator("#preferencias")).to_be_hidden()
    page.get_by_role("link", name="Cambiar").click()
    expect(page.locator("#preferencias")).to_be_visible()


def caso_prefs_abre_directo_con_hash(page):
    page.goto(URL + "/#preferencias")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#preferencias")).to_be_visible()
    expect(page.locator("#vista-resumen")).to_be_hidden()
    opciones = page.request.get(URL + "/api/preferencias").json()["opciones"]
    expect(page.locator("#pref-temas .fila-tema")).to_have_count(len(opciones["secciones"]))
    expect(page.locator("#pref-subtemas input")).to_have_count(len(opciones["subtemas"]))
    expect(page.locator("#pref-medios-preferidos input")).to_have_count(len(opciones["medios"]))
    expect(page.locator("#pref-medios-excluidos input")).to_have_count(len(opciones["medios"]))
    expect(page.locator("#pref-indicadores input")).to_have_count(len(opciones["indicadores"]))
    expect(page.locator("#pref-palabras legend")).to_have_text(["Palabras que quiero seguir", "Palabras que quiero evitar"])
    expect(page.locator("#titulo-perfil")).to_be_visible()
    expect(page.locator("#perfil-contenido")).to_contain_text("Todavía no aprendí nada de tus 👍/👎.")
    expect(page.locator("#pref-temas .fila-tema input[type=checkbox]").first).to_have_attribute("role", "switch")


def caso_prefs_apagar_tema_prioridad_y_subtemas(page):
    _abrir_preferencias(page)
    deportes = _fila(page, "Deportes")
    selector = deportes.locator("select")
    expect(selector).to_be_enabled()
    expect(page.locator("#pref-subtemas-bloque")).to_be_visible()
    deportes.locator("input[type=checkbox]").uncheck()
    expect(selector).to_be_disabled()
    expect(deportes.locator(".estado-tema")).to_have_text("Apagado")
    expect(page.locator("#pref-subtemas-bloque")).to_be_hidden()
    deportes.locator("input[type=checkbox]").check()
    expect(page.locator("#pref-subtemas-bloque")).to_be_visible()
    selector.select_option("alta")
    expect(selector).to_have_value("alta")


def caso_prefs_medio_no_queda_en_las_dos_listas(page):
    _abrir_preferencias(page)
    preferido = page.locator("#pref-medios-preferidos label", has_text="Perfil").locator("input")
    excluido = page.locator("#pref-medios-excluidos label", has_text="Perfil").locator("input")
    preferido.check()
    excluido.check()
    expect(preferido).not_to_be_checked()
    expect(page.locator("#estado-medios")).to_contain_text("Perfil ya no está en los medios que preferís.")
    preferido.check()
    expect(excluido).not_to_be_checked()
    expect(page.locator("#estado-medios")).to_contain_text("ya no está en los medios que no querés ver")


def caso_prefs_palabras_agregar_quitar_topes_y_html(page):
    _abrir_preferencias(page)
    opciones = page.request.get(URL + "/api/preferencias").json()["opciones"]
    campo = page.locator("#pref-palabras fieldset").first
    entrada = campo.locator("input[type=text]")
    entrada.fill("<b>x</b>")
    entrada.press("Enter")
    expect(campo.locator(".lista-palabras li")).to_have_text(["<b>x</b>Quitar"])
    expect(campo.locator("b")).to_have_count(0)
    expect(entrada).to_be_focused()
    entrada.fill("Boca")
    campo.get_by_role("button", name="Agregar").click()
    expect(campo.locator(".lista-palabras li")).to_have_count(2)
    entrada.fill("a" * (opciones["maximo_caracteres"] + 1))
    entrada.press("Enter")
    expect(campo.get_by_role("status")).to_have_text(
        f"Cada palabra puede tener hasta {opciones['maximo_caracteres']} caracteres.")
    expect(campo.locator(".lista-palabras li")).to_have_count(2)
    for i in range(opciones["maximo_palabras"]):
        entrada.fill(f"palabra{i}")
        entrada.press("Enter")
    expect(campo.locator(".lista-palabras li")).to_have_count(opciones["maximo_palabras"])
    expect(campo.get_by_role("status")).to_contain_text(f"hasta {opciones['maximo_palabras']} palabras")
    campo.get_by_role("button", name="Quitar <b>x</b>").click()
    expect(campo.locator(".lista-palabras li")).to_have_count(opciones["maximo_palabras"] - 1)
    expect(entrada).to_be_focused()


def caso_prefs_guardar_recargar_y_restaurar(page):
    _abrir_preferencias(page)
    _fila(page, "Deportes").locator("select").select_option("alta")
    page.locator("#pref-medios-excluidos label", has_text="Perfil").locator("input").check()
    campo = page.locator("#pref-palabras fieldset").first
    campo.locator("input[type=text]").fill("Boca")
    campo.get_by_role("button", name="Agregar").click()
    page.get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator("#estado-guardado")).to_have_text("Guardado.")
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#preferencias")).to_be_visible()
    expect(_fila(page, "Deportes").locator("select")).to_have_value("alta")
    expect(page.locator("#pref-medios-excluidos label", has_text="Perfil").locator("input")).to_be_checked()
    expect(page.locator("#pref-palabras fieldset").first.locator(".lista-palabras li")).to_have_text(["BocaQuitar"])
    # Deja los datos temporales como estaban.
    _fila(page, "Deportes").locator("select").select_option("normal")
    page.locator("#pref-medios-excluidos label", has_text="Perfil").locator("input").uncheck()
    page.locator("#pref-palabras fieldset").first.get_by_role("button", name="Quitar Boca").click()
    page.get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator("#estado-guardado")).to_have_text("Guardado.")
    # Un cambio posterior borra el "Guardado.".
    _fila(page, "Deportes").locator("select").select_option("baja")
    expect(page.locator("#estado-guardado")).to_have_text("")
    _fila(page, "Deportes").locator("select").select_option("normal")


def caso_prefs_error_400_en_espanol_y_conserva_lo_escrito(page):
    _abrir_preferencias(page)
    for fila in page.locator("#pref-temas .fila-tema").all():
        fila.locator("input[type=checkbox]").uncheck()
    expect(page.locator("#aviso-temas")).to_have_text("Elegí al menos un tema.")
    page.get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator("#errores-prefs")).to_contain_text("Elegí al menos un tema.")
    assert page.locator("#errores-prefs").get_attribute("role") == "alert"
    expect(page.locator("#estado-guardado")).to_have_text("")
    expect(page.locator("#pref-temas .fila-tema input[type=checkbox]").first).not_to_be_checked()
    # Un 400 con otros errores también se ve, uno por línea.
    page.route("**/api/preferencias", lambda ruta: ruta.fulfill(status=400, json={
        "ok": False, "errores": ["Primer error.", "Segundo error."]}) if ruta.request.method == "POST" else ruta.continue_())
    page.get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator("#errores-prefs p")).to_have_text(["No se guardó:", "Primer error.", "Segundo error."])


def caso_prefs_aviso_de_cambios_sin_guardar(page):
    _abrir_preferencias(page)
    _fila(page, "Deportes").locator("select").select_option("alta")
    page.get_by_role("button", name="Volver al resumen").click()
    expect(page.locator("#aviso-cambios")).to_be_visible()
    expect(page.locator("#aviso-cambios")).to_contain_text("Tenés cambios sin guardar.")
    expect(page.locator("#preferencias")).to_be_visible()
    page.get_by_role("button", name="Seguir editando").click()
    expect(page.locator("#aviso-cambios")).to_be_hidden()
    page.get_by_role("button", name="Volver al resumen").click()
    page.get_by_role("button", name="Descartar y salir").click()
    expect(page.locator("#vista-resumen")).to_be_visible()
    _abrir_preferencias(page)
    expect(_fila(page, "Deportes").locator("select")).to_have_value("normal")
    page.go_back()  # sin cambios: sale sin avisos
    expect(page.locator("#vista-resumen")).to_be_visible()


def caso_prefs_reiniciar_lo_aprendido(page):
    for i in range(3):  # votos de tema con hora distinta del reinicio
        page.request.post(URL + "/api/gustos", data={"tipo": "tema", "clave": "Deportes", "voto": "me_gusta"})
    _abrir_preferencias(page)
    expect(page.locator("#perfil-contenido li").first).to_contain_text("Deportes")
    expect(page.locator("#perfil-contenido")).to_contain_text("Votos que cuentan: 1.")
    page.once("dialog", lambda d: d.dismiss())
    page.get_by_role("button", name="Reiniciar lo aprendido").click()
    expect(page.locator("#perfil-contenido li").first).to_contain_text("Deportes")
    page.wait_for_timeout(1100)
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Reiniciar lo aprendido").click()
    expect(page.locator("#estado-reinicio-vista")).to_contain_text("Listo")
    expect(page.locator("#perfil-contenido")).to_contain_text("Todavía no aprendí nada de tus 👍/👎.")
    expect(page.locator("#perfil-contenido")).to_contain_text("Último reinicio:")
    page.request.post(URL + "/api/gustos", data={"tipo": "tema", "clave": "Deportes", "voto": None})


def caso_prefs_teclado_recorre_todo_y_guarda(page):
    _abrir_preferencias(page)
    page.locator("#titulo-preferencias").focus()
    page.keyboard.press("Tab")
    # Primer control de la vista tras el título: el interruptor del primer tema.
    primero = page.locator("#pref-temas input[type=checkbox]").first
    expect(primero).to_be_focused()
    page.keyboard.press("Space")
    expect(primero).not_to_be_checked()
    page.keyboard.press("Space")
    expect(primero).to_be_checked()
    esperados = page.evaluate("""() => Array.from(document.querySelectorAll(
        '#preferencias button, #preferencias input, #preferencias select'))
        .filter((e) => e.offsetParent !== null && !e.disabled && e.id !== 'cambios-guardar'
          && !e.closest('#aviso-cambios')).length""")
    recorridos = set()
    for _ in range(esperados + 5):
        recorridos.add(page.evaluate("document.activeElement.id || document.activeElement.textContent"))
        if page.evaluate("document.activeElement.id") == "guardar-prefs":
            break
        page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "guardar-prefs", recorridos
    page.keyboard.press("Enter")
    expect(page.locator("#estado-guardado")).to_have_text("Guardado.")
    for etiqueta in page.locator("#preferencias label").all():
        assert etiqueta.inner_text().strip() or etiqueta.get_attribute("for") or etiqueta.locator("input").count()
    assert page.locator("#preferencias fieldset legend").count() >= 6


CASOS = [caso_carga, caso_indicadores_con_fecha_y_fuente, caso_sin_dato_visible, caso_nota_con_enlace,
         caso_voto, caso_caja_de_preguntas, caso_aviso_de_fuente_caida, caso_aviso_del_corrector,
         caso_pedido_contador_y_error_del_servidor, caso_pedido_en_cabecera_escapado,
         caso_aviso_de_pedido_sin_notas_y_tema_destildado, caso_como_se_armo_con_teclado,
         caso_resumen_viejo_sin_plan_no_muestra_el_bloque, caso_etiquetas_y_secciones_del_servidor,
         caso_prefs_abre_con_boton_vuelve_y_atras, caso_prefs_abre_directo_con_hash,
         caso_prefs_apagar_tema_prioridad_y_subtemas, caso_prefs_medio_no_queda_en_las_dos_listas,
         caso_prefs_palabras_agregar_quitar_topes_y_html, caso_prefs_guardar_recargar_y_restaurar,
         caso_prefs_error_400_en_espanol_y_conserva_lo_escrito, caso_prefs_aviso_de_cambios_sin_guardar,
         caso_prefs_reiniciar_lo_aprendido, caso_prefs_teclado_recorre_todo_y_guarda,
         # Los dos últimos reemplazan el resumen guardado (el armado simulado): van al final.
         caso_pedido_sin_texto_no_manda_el_campo, caso_pedido_se_manda_se_guarda_y_se_vacia]


def correr(navegador, caso):
    """Cada caso en una página limpia; además falla por errores de consola o pedidos fuera de localhost."""
    page = navegador.new_page()
    page.set_default_timeout(5000)
    problemas = []
    # El 400 del pedido demasiado largo es esperado: el navegador lo registra como error de recurso.
    esperado = "status of 400" if caso in (caso_pedido_contador_y_error_del_servidor,
                                           caso_prefs_error_400_en_espanol_y_conserva_lo_escrito) else None
    page.on("console", lambda m: problemas.append(f"consola ({m.type}): {m.text}")
            if m.type == "error" and not (esperado and esperado in m.text) else None)
    page.on("pageerror", lambda e: problemas.append(f"error de la página: {e}"))
    page.on("request", lambda r: problemas.append(f"pedido fuera de localhost: {r.url}")
            if urlparse(r.url).hostname not in ("localhost", "127.0.0.1") else None)
    try:
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        expect(page.locator("#estado-indicadores")).to_have_text("")
        caso(page)
        page.wait_for_load_state("networkidle")
    finally:
        page.close()
    if problemas:
        raise AssertionError("; ".join(problemas))


def main():
    fallaron = 0
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        for caso in CASOS:
            try:
                correr(navegador, caso)
                print(f"OK    {caso.__name__}")
            except Exception:
                fallaron += 1
                print(f"FALLA {caso.__name__}")
                traceback.print_exc(limit=0)
        navegador.close()
    print(f"{len(CASOS) - fallaron} de {len(CASOS)} casos pasaron.")
    sys.exit(1 if fallaron else 0)


if __name__ == "__main__":
    main()
