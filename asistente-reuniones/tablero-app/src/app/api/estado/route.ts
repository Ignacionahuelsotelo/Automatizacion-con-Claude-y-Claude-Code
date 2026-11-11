import { leerEstado } from "@/lib/datos";
import { jobActual } from "@/lib/comandos";
import { hostPermitido } from "@/lib/seguridad";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  if (!hostPermitido(req)) return new Response("Prohibido", { status: 403 });
  return Response.json({ estado: await leerEstado(), job: jobActual() });
}
