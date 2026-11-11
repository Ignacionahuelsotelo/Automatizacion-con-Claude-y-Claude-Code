# Caso 03: fechas relativas en todas sus variantes

**Qué prueba:** convertir cada fecha relativa a una fecha real tomando como base la fecha de la reunión, y conservar la frase original. Incluye "la semana que viene", "en diez días", "antes de fin de mes", "el jueves que viene" (no es el jueves más cercano) y responsables que no estuvieron.

## Entrada

Reunión (calendario): "Kickoff migración CRM con CloudCRM", 03/11/2026 11:00 a 12:00.
Invitados: Sofía Herrera, Diego Paz (CloudCRM), Valentina Ríos (opcional), Laura Gómez.
Asistieron (según las notas): Sofía, Diego, Laura. Valentina no vino.
`tareas/tareas.json` antes: `[]`

Notas:

```text
- Sofía: el viernes mando la lista de procesos actuales a Diego.
- Diego: la semana que viene te paso el usuario de prueba de CloudCRM, Sofía.
- Laura: antes de fin de mes tengo que cerrar el presupuesto de la fase 2.
- Sofía: en diez días tengo que armar el listado de clientes duplicados.
- Laura: Valentina tiene que pasar la lista de usuarios de Soporte mañana.
- Diego: el primero de diciembre hay que firmar la addenda.
- Decidimos arrancar la fase 1 hoy.
- Pendiente: si migramos el historial completo de tickets o solo 12 meses.
- Sofía: nos vemos el jueves que viene, a la misma hora.
```

## Salida esperada

```markdown
# Minuta: Kickoff migración CRM con CloudCRM

## Datos
- Fecha y hora: 03/11/2026 11:00 a 12:00
- Participantes: Sofía Herrera, Diego Paz (CloudCRM), Laura Gómez. Valentina Ríos figuraba en la invitación, pero no asistió.

## Resumen
- Se arrancó la fase 1 (kickoff y relevamiento) del plan de migración.
- Quedaron tareas con fechas en la semana siguiente y a fin de mes, y dos pendientes sin responsable.
- Sigue abierta la decisión sobre el historial de tickets.

## Decisiones
- Arrancar la fase 1 hoy, 03/11.

## Tareas
| id | descripción | responsable | fecha límite | estado |
|----|-------------|-------------|--------------|--------|
| T-001 | Enviar a Diego la lista de procesos actuales | Sofía Herrera | 06/11 (el viernes) | abierta |
| T-002 | Pasarle a Sofía el usuario de prueba de CloudCRM | Diego Paz | 09/11 (la semana que viene) | abierta |
| T-003 | Cerrar el presupuesto de la fase 2 | Laura Gómez | 30/11 (antes de fin de mes) | abierta |
| T-004 | Armar el listado de clientes duplicados | Sofía Herrera | 13/11 (en diez días) | abierta |
| T-005 | Pasar la lista de usuarios de Soporte | sin definir | 04/11 (mañana) | abierta |
| T-006 | Firmar la addenda | sin definir | 01/12 (el primero de diciembre) | abierta |

## Temas abiertos
- Historial de tickets: migrar todo o solo 12 meses. Sigue sin decidirse.
- T-005: Laura la asignó a Valentina Ríos, que no vino, así que queda sin responsable.
- T-006: "hay que firmar" sin nombre de quien firma.

## Próxima reunión
- 12/11/2026 (el jueves que viene), misma hora que hoy: 11:00.
```

Tareas nuevas para `tareas/tareas.json` (6): T-001 a T-006 con `reunion: "kickoff-migracion-crm-con-cloudcrm"`.

## Criterios

- [ ] Cada fecha relativa tiene su fecha real y su frase original: el viernes = 06/11, la semana que viene = 09/11, en diez días = 13/11, antes de fin de mes = 30/11, el primero de diciembre = 01/12.
- [ ] "El jueves que viene" da 12/11, no 05/11. El jueves más cercano sería 05/11, y ese no es el pedido.
- [ ] Valentina no figura como responsable: estaba en la invitación, pero no asistió.
- [ ] T-006 queda sin responsable, porque "hay que firmar" no nombra a nadie.
- [ ] "Decidimos arrancar la fase 1 hoy" entra en decisiones; "pendiente: historial de tickets" entra en temas abiertos.
- [ ] La hora de la próxima reunión se toma de "a la misma hora" (11:00). No se inventa.
