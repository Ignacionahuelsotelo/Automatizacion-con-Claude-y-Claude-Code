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


CASOS = [caso_carga, caso_indicadores_con_fecha_y_fuente, caso_sin_dato_visible, caso_nota_con_enlace,
         caso_voto, caso_caja_de_preguntas, caso_aviso_de_fuente_caida, caso_aviso_del_corrector,
         caso_pedido_contador_y_error_del_servidor, caso_pedido_en_cabecera_escapado,
         # Los dos últimos reemplazan el resumen guardado (el armado simulado): van al final.
         caso_pedido_sin_texto_no_manda_el_campo, caso_pedido_se_manda_se_guarda_y_se_vacia]


def correr(navegador, caso):
    """Cada caso en una página limpia; además falla por errores de consola o pedidos fuera de localhost."""
    page = navegador.new_page()
    page.set_default_timeout(5000)
    problemas = []
    # El 400 del pedido demasiado largo es esperado: el navegador lo registra como error de recurso.
    esperado = "status of 400" if caso is caso_pedido_contador_y_error_del_servidor else None
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
