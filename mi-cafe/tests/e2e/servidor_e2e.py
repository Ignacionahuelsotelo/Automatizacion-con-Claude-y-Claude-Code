"""Servidor de Mi Café para las pruebas e2e (spec 26). Solo para desarrollo.

Es el servidor real con las fuentes simuladas: no llama a internet ni a `claude`, y guarda todo
en la carpeta de MICAFE_DATOS (obligatoria, y nunca la `datos/` real del proyecto).

Uso: MICAFE_DATOS=/carpeta/temporal python3 tests/e2e/servidor_e2e.py PUERTO
La app no importa nada de acá.
"""

import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

from micafe import config  # noqa: E402

LINK_1 = "https://www.ejemplo-diario.com.ar/politica/nota-uno"
LINK_2 = "https://www.ejemplo-diario.com.ar/economia/nota-dos"

TEXTO_RESUMEN = f"""Lo más importante de hoy: el Congreso debatió y se movieron las tasas.

Política

Debate en el Congreso por el presupuesto
Diario Ejemplo, 17/11/2026
{LINK_1}
Por qué importa: define el gasto del año próximo.

Economía

El Banco Central ajustó la tasa de referencia
Diario Ejemplo, 17/11/2026
{LINK_2}
Por qué importa: cambia el costo del crédito.
"""

RESUMEN = {
    "fecha": "2026-11-18",
    "generado_en": "18/11/2026 08:00",
    "indicadores": [],
    "texto": TEXTO_RESUMEN,
    "chequeo": {"aprobado": False, "intentos": 2, "verificado": [],
                "no_cumple": ["Una nota repite un tema de ayer."], "omitido": []},
}

INDICADORES = {
    "indicadores": [
        {"clave": "dolar_oficial", "grupo": "dolar", "nombre": "Dólar oficial", "valor": "$ 1.234,50",
         "fecha": "17/11/2026", "fuente": "DolarApi", "desactualizado": False},
        {"clave": "riesgo_pais", "grupo": "riesgo", "nombre": "Riesgo país", "valor": None,
         "fecha": None, "fuente": "ArgentinaDatos", "desactualizado": False},
    ],
    "generado_en": "18/11/2026 08:00",
    "avisos": ["No se pudo consultar ArgentinaDatos: el riesgo país queda sin dato."],
}

NOTICIAS = {
    "notas": [
        {"titulo": "Debate en el Congreso por el presupuesto", "medio": "Diario Ejemplo",
         "seccion": "Política", "fecha": "17/11/2026 10:00", "link": LINK_1},
        {"titulo": "El Banco Central ajustó la tasa de referencia", "medio": "Diario Ejemplo",
         "seccion": "Economía", "fecha": "17/11/2026 11:30", "link": LINK_2},
    ],
    "fallas": [{"medio": "Medio Caído", "seccion": "Deportes", "motivo": "no respondió a tiempo"}],
    "ventana": {"desde": "17/11/2026", "hasta": "17/11/2026"},
    "tope_por_medio": 3,
    "generado_en": "18/11/2026 08:00",
}

RESPUESTA_SIMULADA = "Según la nota, el debate trata sobre el gasto del año próximo."


def _sin_internet(*args, **kwargs):
    raise OSError("Las pruebas e2e no usan internet.")


def preparar() -> int:
    datos = os.environ.get("MICAFE_DATOS")
    if not datos:
        sys.exit("Falta MICAFE_DATOS (carpeta temporal para las pruebas).")
    if os.path.realpath(datos) == os.path.realpath(os.path.join(RAIZ, "datos")):
        sys.exit("MICAFE_DATOS no puede ser la carpeta datos/ real.")
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) in (8000, 8001):
        sys.exit("Uso: servidor_e2e.py PUERTO (distinto de 8000 y 8001).")
    os.makedirs(os.path.join(datos, "resumenes"), exist_ok=True)
    with open(os.path.join(datos, "resumenes", "2026-11-18.json"), "w", encoding="utf-8") as archivo:
        json.dump(RESUMEN, archivo, ensure_ascii=False)

    # Fuentes simuladas (se reemplazan antes de arrancar; el servicio las busca por módulo).
    from micafe.dominio import resumen
    from micafe.fuentes import acciones, indicadores, noticias

    indicadores.obtener = lambda *a, **k: json.loads(json.dumps(INDICADORES))
    noticias.obtener = lambda *a, **k: json.loads(json.dumps(NOTICIAS))
    acciones.obtener_todo = lambda *a, **k: {"indicadores": [], "avisos": []}
    resumen.ejecutar_claude = lambda *a, **k: RESPUESTA_SIMULADA
    urllib.request.urlopen = _sin_internet  # cualquier fuente sin simular falla en vez de salir a internet
    return int(sys.argv[1])


if __name__ == "__main__":
    puerto = preparar()
    from micafe.web import servidor

    servidor.PUERTO = puerto
    servidor.main()
