// Utilidades de fecha sin dependencias. Todo en UTC sobre cadenas AAAA-MM-DD,
// así la zona horaria del navegador no mueve los días.
const DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

const aDate = (f: string) => new Date(`${f}T00:00:00Z`);
const aTexto = (d: Date) => d.toISOString().slice(0, 10);

export const esFecha = (f: string) => /^\d{4}-\d{2}-\d{2}$/.test(f);

export function sumarDias(f: string, n: number): string {
  const d = aDate(f);
  d.setUTCDate(d.getUTCDate() + n);
  return aTexto(d);
}

export function lunesDe(f: string): string {
  const dow = aDate(f).getUTCDay(); // 0 = domingo
  return sumarDias(f, dow === 0 ? -6 : 1 - dow);
}

export function semanaHabil(hoy: string, offset: number): string[] {
  const lunes = sumarDias(lunesDe(hoy), offset * 7);
  return [0, 1, 2, 3, 4].map((i) => sumarDias(lunes, i));
}

export const diaCorto = (f: string) => DIAS[aDate(f).getUTCDay()];
export const diaNumero = (f: string) => f.slice(8, 10);
export const ddmm = (f: string) => `${f.slice(8, 10)}/${f.slice(5, 7)}`;

export function rangoSemana(dias: string[]): string {
  const a = aDate(dias[0]);
  const b = aDate(dias[dias.length - 1]);
  const ma = MESES[a.getUTCMonth()];
  const mb = MESES[b.getUTCMonth()];
  return ma === mb
    ? `${a.getUTCDate()} al ${b.getUTCDate()} de ${mb}`
    : `${a.getUTCDate()} de ${ma} al ${b.getUTCDate()} de ${mb}`;
}

export function diasEntre(desde: string, hasta: string): number {
  return Math.round((aDate(hasta).getTime() - aDate(desde).getTime()) / 86_400_000);
}

export function relativo(fecha: string, hoy: string): string {
  const n = diasEntre(hoy, fecha);
  if (n === 0) return "hoy";
  if (n === 1) return "mañana";
  if (n === -1) return "ayer";
  return n < 0 ? `hace ${-n} días` : `en ${n} días`;
}
