import { leerDocumento } from "@/lib/datos";
import { hostPermitido } from "@/lib/seguridad";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  if (!hostPermitido(req)) return new Response("Prohibido", { status: 403 });
  const p = new URL(req.url).searchParams;
  const tipo = p.get("tipo");
  if (tipo !== "brief" && tipo !== "minuta") return Response.json({ error: "Tipo inválido." }, { status: 400 });
  const texto = await leerDocumento(p.get("fecha") ?? "", p.get("slug") ?? "", tipo);
  return texto === null ? Response.json({ error: "No existe." }, { status: 404 }) : Response.json({ texto });
}
