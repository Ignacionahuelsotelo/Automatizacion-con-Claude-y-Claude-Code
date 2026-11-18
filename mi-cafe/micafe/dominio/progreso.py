"""Progreso del armado del resumen, en memoria (spec 30).

Guarda en qué etapa va el armado para que la página lo consulte. No sabe nada de HTTP.
Un solo armado a la vez. Si se reinicia el servidor, el estado se pierde (decisión de la spec).
Solo guarda etapas fijas y los datos que le pasan al terminar; nunca escribe contenido en el log.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from micafe.config import ETAPAS_RESUMEN, REINTENTOS_CORRECTOR, ZONA


class Progreso:
    """Estado del armado actual, protegido con un candado para usarlo desde varios hilos."""

    def __init__(self) -> None:
        """Arranca en "libre": todavía no se armó nada."""
        self._candado = threading.Lock()
        self._estado = "libre"
        self._etapa: str | None = None
        self._intento: int | None = None
        self._inicio: str | None = None
        self._resultado: dict[str, Any] | None = None
        self._errores: list[str] = []
        self._avisos: dict[str, Any] | None = None

    def iniciar(self, ahora: datetime | None = None) -> bool:
        """Empieza un armado. Devuelve False (sin tocar nada) si ya hay uno en curso."""
        with self._candado:
            if self._estado == "en_curso":
                return False
            ahora = ahora or datetime.now(ZONA)
            self._estado = "en_curso"
            self._etapa = None
            self._intento = None
            self._inicio = ahora.astimezone(ZONA).strftime("%d/%m/%Y %H:%M")
            self._resultado = None
            self._errores = []
            self._avisos = None
            return True

    def avanzar(self, etapa: str, intento: int | None = None) -> None:
        """Marca la etapa actual (una clave de ETAPAS_RESUMEN) y, si corresponde, el número de intento."""
        with self._candado:
            if self._estado != "en_curso":
                return
            self._etapa = etapa
            self._intento = intento

    def terminar(self, resultado: dict[str, Any]) -> None:
        """Deja el estado en "listo" con `{"resumen", "avisos"}`."""
        with self._candado:
            self._estado = "listo"
            self._intento = None
            self._resultado = resultado

    def fallar(self, errores: list[str], extras: dict[str, Any] | None = None) -> None:
        """Deja el estado en "fallo" con los mensajes en español y los avisos de fuentes (en `extras`)."""
        with self._candado:
            self._estado = "fallo"
            self._intento = None
            self._errores = list(errores)
            self._avisos = (extras or {}).get("avisos")

    def instantanea(self) -> dict[str, Any]:
        """Copia del estado para responder: no se modifica desde afuera."""
        with self._candado:
            claves = [clave for clave, _ in ETAPAS_RESUMEN]
            actual = claves.index(self._etapa) if self._etapa in claves else None
            etapas = []
            for posicion, (clave, texto) in enumerate(ETAPAS_RESUMEN):
                if self._estado == "listo":
                    situacion = "hecha"
                elif actual is None or posicion > actual:
                    situacion = "pendiente"
                elif posicion == actual:
                    situacion = "en_curso"
                else:
                    situacion = "hecha"
                etapas.append({"clave": clave, "texto": texto, "situacion": situacion})
            datos: dict[str, Any] = {
                "estado": self._estado,
                "etapa": self._etapa,
                "etapas": etapas,
                "intento": self._intento,
                "intentos_max": REINTENTOS_CORRECTOR + 1,
                "inicio": self._inicio,
            }
            if self._estado == "listo":
                datos["resultado"] = dict(self._resultado or {})
            elif self._estado == "fallo":
                datos["errores"] = list(self._errores)
                datos["avisos"] = self._avisos
            return datos
