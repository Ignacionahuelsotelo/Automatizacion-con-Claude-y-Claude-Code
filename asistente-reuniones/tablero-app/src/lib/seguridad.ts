// Este servidor solo debe responder a la propia computadora.
// - Host: evita "DNS rebinding" (una web externa que apunta a 127.0.0.1).
// - Origin + cabecera propia: evita que otra pestaña mande POST en tu nombre.

const HOSTS = new Set(["127.0.0.1:3210", "localhost:3210"]);

export function hostPermitido(req: Request): boolean {
  const host = req.headers.get("host") ?? "";
  return HOSTS.has(host);
}

export function origenPermitido(req: Request): boolean {
  const origen = req.headers.get("origin");
  if (!origen) return false;
  try {
    return HOSTS.has(new URL(origen).host);
  } catch {
    return false;
  }
}

export function pedidoDeEscrituraValido(req: Request): boolean {
  return (
    hostPermitido(req) &&
    origenPermitido(req) &&
    req.headers.get("x-tablero") === "1" &&
    (req.headers.get("content-type") ?? "").startsWith("application/json")
  );
}
