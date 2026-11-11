"use client";

import { useEffect, useRef, useState } from "react";

export type Abierto = { fecha: string; slug: string; titulo: string; tipo: "brief" | "minuta" };

// Markdown mínimo (títulos, listas, párrafos) armado con elementos de React:
// nunca se inserta HTML crudo, así un documento no puede inyectar código.
function Texto({ md }: { md: string }) {
  const bloques: React.ReactNode[] = [];
  let lista: string[] = [];
  const cerrarLista = () => {
    if (lista.length) {
      bloques.push(<ul key={`u${bloques.length}`}>{lista.map((l, i) => <li key={i}>{l}</li>)}</ul>);
      lista = [];
    }
  };
  md.split("\n").forEach((linea, i) => {
    const h = /^(#{1,4})\s+(.*)$/.exec(linea);
    const li = /^\s*(?:[-*]|\d+\.)\s+(.*)$/.exec(linea);
    if (li) return void lista.push(li[1]);
    cerrarLista();
    if (h) bloques.push(h[1].length <= 2 ? <h3 key={i}>{h[2]}</h3> : <h4 key={i}>{h[2]}</h4>);
    else if (linea.trim()) bloques.push(<p key={i}>{linea}</p>);
  });
  cerrarLista();
  return <div className="doc">{bloques}</div>;
}

export function Documento({ abierto, onCerrar }: { abierto: Abierto | null; onCerrar: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [texto, setTexto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (!abierto) {
      if (d.open) d.close();
      return;
    }
    setTexto(null);
    setError(null);
    if (!d.open) d.showModal();
    const q = new URLSearchParams({ fecha: abierto.fecha, slug: abierto.slug, tipo: abierto.tipo });
    fetch(`/api/documento?${q}`)
      .then((r) => r.json().then((j) => (r.ok ? setTexto(j.texto) : setError(j.error ?? "No se pudo abrir."))))
      .catch(() => setError("No se pudo abrir."));
  }, [abierto]);

  return (
    <dialog ref={ref} className="hoja" onClose={onCerrar} aria-label={abierto?.titulo ?? "Documento"}>
      <header className="hoja-cab">
        <div>
          <p className="etiqueta">{abierto?.tipo === "minuta" ? "Minuta" : "Brief"}</p>
          <h2>{abierto?.titulo}</h2>
        </div>
        <button className="btn-texto" onClick={() => ref.current?.close()}>Cerrar</button>
      </header>
      {error ? <p className="vacio">{error}</p> : texto === null ? <p className="vacio">Abriendo…</p> : <Texto md={texto} />}
    </dialog>
  );
}
