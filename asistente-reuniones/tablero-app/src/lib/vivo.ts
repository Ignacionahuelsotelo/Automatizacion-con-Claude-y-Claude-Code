import { watch, type FSWatcher } from "node:fs";
import path from "node:path";
import { LOGS, REUNIONES, TAREAS } from "./raiz";
import type { EstadoJob } from "./tipos";

type Evento = { tipo: "cambio" } | { tipo: "job"; job: EstadoJob | null };
type Oyente = (e: Evento) => void;

type Bus = { oyentes: Set<Oyente>; watchers: FSWatcher[]; timer: NodeJS.Timeout | null };

// globalThis: sobrevive a la recarga en caliente de Next en desarrollo.
const g = globalThis as unknown as { __tableroBus?: Bus };

function bus(): Bus {
  if (!g.__tableroBus) {
    const b: Bus = { oyentes: new Set(), watchers: [], timer: null };
    const avisar = () => {
      if (b.timer) clearTimeout(b.timer);
      b.timer = setTimeout(() => emitir({ tipo: "cambio" }), 250);
    };
    const mirar = (ruta: string, recursivo: boolean) => {
      try {
        b.watchers.push(watch(ruta, { recursive: recursivo }, avisar));
      } catch {
        // la carpeta puede no existir todavía; el tablero sigue funcionando sin ella
      }
    };
    mirar(path.dirname(TAREAS), false);
    mirar(REUNIONES, true);
    mirar(LOGS, false);
    g.__tableroBus = b;
  }
  return g.__tableroBus;
}

export function emitir(e: Evento) {
  for (const o of bus().oyentes) o(e);
}

export function suscribir(o: Oyente): () => void {
  const b = bus();
  b.oyentes.add(o);
  return () => b.oyentes.delete(o);
}
