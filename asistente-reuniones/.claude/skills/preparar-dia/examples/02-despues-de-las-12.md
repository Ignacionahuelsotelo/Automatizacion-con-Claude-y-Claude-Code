# Caso 02: se corre pasado el mediodía

**Qué prueba:** a partir de las 12:00 solo se preparan las reuniones que todavía no empezaron. Las que ya pasaron quedan afuera de la agenda pero cuentan en el log.

## Entrada

Comando: `/preparar-dia`. Hoy es 04/11/2026, son las 13:15. No hay briefs previos.

Calendario del 04/11:

| Hora | Título | Invitados |
|------|--------|-----------|
| 10:00 | Daily de soporte | Camila Torres, Martín Ruiz |
| 12:30 | Almuerzo con Pablo (en curso, empezó hace 45 minutos) | Pablo Ibáñez |
| 15:00 | Revisión de presupuesto Q1 | Laura Gómez, Martín Ruiz |
| 17:00 | Cierre de proveedores | Pablo Ibáñez, Camila Torres |

Lo que devuelven los investigadores:

- Revisión de presupuesto Q1: hay que validar el monto de licencias. Sin alertas.
- Cierre de proveedores: falta la firma del contrato del proveedor B. Requiere atención.

## Salida esperada

`reuniones/2026-11-04/resumen-dia.md`:

```markdown
# Resumen del día: 04/11/2026

## Agenda
- 15:00 Revisión de presupuesto Q1: hay que validar el monto de licencias.
- 17:00 Cierre de proveedores: falta la firma del contrato del proveedor B.

## Las 3 cosas que no me puedo olvidar hoy
1. Firma del contrato del proveedor B (Cierre de proveedores).
2. Validar el monto de licencias del presupuesto Q1 (Revisión de presupuesto Q1).

## Errores
- ninguno
```

`logs/2026-11-04.md`:

```
- 13:15 preparar-dia: 2 reuniones (2 nuevas, 0 con brief existente, 2 ya pasadas) | errores: ninguno
```

## Criterios

- [ ] Solo se lanzan 2 investigadores: el de las 15:00 y el de las 17:00.
- [ ] El daily de las 10:00 y el almuerzo en curso no se investigan: ya empezaron.
- [ ] Las reuniones pasadas no aparecen en la agenda, pero sí en el conteo "ya pasadas" del log (2).
- [ ] Hay solo 2 cosas en la lista, sin rellenar una tercera inventada.
- [ ] La hora del log es la de la corrida (13:15), no la de ninguna reunión.
