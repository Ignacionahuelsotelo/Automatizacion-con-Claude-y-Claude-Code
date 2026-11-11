#!/usr/bin/env python3
"""Cierre semanal del tablero.

1. Marca como "vencida" cada tarea abierta con fecha anterior a hoy.
2. Regenera tablero/index.html (tablero/generar.py).
3. Imprime cuántas tareas hay en cada estado y las 3 personas con más pendientes.

Uso: python3 tablero/semanal.py [--dry-run]
Con --dry-run solo informa: no escribe tareas.json ni el tablero.
"""
import json
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from generar import ENTRADA, ZONA, main as generar_tablero

PENDIENTES = {"abierta", "vencida"}


def sin_definir(valor):
    return str(valor or "").strip().lower() in ("", "sin definir")


def fecha_de(tarea):
    try:
        return date.fromisoformat(str(tarea.get("fecha", "")).strip())
    except ValueError:
        return None


def main():
    simular = "--dry-run" in sys.argv[1:]
    hoy = datetime.now(ZONA).date()
    tareas = json.loads(Path(ENTRADA).read_text(encoding="utf-8"))

    # 1. Abiertas con fecha pasada -> vencida
    marcadas = []
    for t in tareas:
        f = fecha_de(t)
        if str(t.get("estado", "")).strip().lower() == "abierta" and f and f < hoy:
            t["estado"] = "vencida"
            marcadas.append(t["id"])

    if not simular:
        Path(ENTRADA).write_text(json.dumps(tareas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # 2. Regenerar el tablero
        generar_tablero()

    # 3. Resumen
    print(f"Hoy: {hoy.strftime('%d/%m/%Y')}" + (" (simulación: no se escribió nada)" if simular else ""))
    if marcadas:
        print(f"Marcadas como vencidas ahora ({len(marcadas)}): {', '.join(marcadas)}")
    else:
        print("No hubo tareas nuevas para marcar como vencidas.")

    print("\nTareas por estado:")
    for estado, n in Counter(str(t.get("estado", "sin estado")).strip() or "sin estado" for t in tareas).most_common():
        print(f"  {estado}: {n}")
    print(f"  total: {len(tareas)}")

    pendientes = [t for t in tareas if str(t.get("estado", "")).strip().lower() in PENDIENTES]
    por_persona = {}
    for t in pendientes:
        if sin_definir(t.get("responsable")):
            continue
        d = por_persona.setdefault(t["responsable"], [0, 0])
        d[0] += 1
        d[1] += str(t.get("estado", "")).strip().lower() == "vencida"
    top = sorted(por_persona.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0]))[:3]

    print("\nPersonas con más pendientes:")
    if top:
        for i, (nombre, (total, vencidas)) in enumerate(top, 1):
            print(f"  {i}. {nombre}: {total} pendientes ({vencidas} vencidas)")
    else:
        print("  ninguna: no hay pendientes con responsable.")
    sin_resp = sum(1 for t in pendientes if sin_definir(t.get("responsable")))
    if sin_resp:
        print(f"  (aparte, {sin_resp} pendientes sin responsable)")


if __name__ == "__main__":
    main()
