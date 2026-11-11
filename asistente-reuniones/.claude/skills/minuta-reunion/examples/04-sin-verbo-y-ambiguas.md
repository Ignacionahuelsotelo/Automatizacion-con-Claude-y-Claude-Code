# Caso 04: frases sin acción, "yo" sin identificar y decisiones pendientes

**Qué prueba:** separar tareas de temas abiertos. Una preocupación sin acción no es tarea. "Hay que decidir X" sí es tarea, pero sin responsable. "Yo" en una reunión de dos personas no se puede asignar sin saber quién habla. "Lo vemos la semana que viene" no tiene entregable, así que es tema abierto.

## Entrada

Reunión (calendario): "1:1 con Laura", 04/11/2026 09:30 a 10:00.
Invitados: Laura Gómez.
Asistieron: Laura Gómez y quien tomó las notas (rotulado como "Yo").
`tareas/tareas.json` antes: `[]`

Notas:

```text
Laura: el tema de los duplicados de clientes me preocupa bastante.
Laura: yo reviso el contrato de licencias antes del jueves.
Yo: mirar los accesos del CRM, que hace rato está pendiente.
Laura: hay que decidir si pagamos el plan anual o el mensual.
Laura: lo de Zoom lo vemos la semana que viene.
Yo: ok, no cambiamos de proveedor de correo este trimestre, eso lo cerramos.
```

## Salida esperada

```markdown
# Minuta: 1:1 con Laura

## Datos
- Fecha y hora: 04/11/2026 09:30 a 10:00
- Participantes: Laura Gómez, y quien tomó las notas ("Yo" en el texto, sin nombre)

## Resumen
- Se habló de los duplicados de clientes, la renovación de licencias y el acceso al CRM.
- Quedó una decisión cerrada sobre el proveedor de correo.
- La elección del plan anual o mensual sigue sin responsable.

## Decisiones
- No cambiar de proveedor de correo este trimestre.

## Tareas
| id | descripción | responsable | fecha límite | estado |
|----|-------------|-------------|--------------|--------|
| T-001 | Revisar el contrato de licencias | Laura Gómez | 05/11 (el jueves) | abierta |
| T-002 | Mirar los accesos del CRM | sin definir | sin definir | abierta |
| T-003 | Decidir si se paga el plan anual o el mensual | sin definir | sin definir | abierta |

## Temas abiertos
- Duplicados de clientes: preocupación de Laura, sin acción definida.
- Zoom: "lo vemos la semana que viene", sin fecha ni responsable.
- T-002: la frase "Yo: mirar los accesos" no dice quién es "yo" en las notas. Confirmar quién la tiene.

## Próxima reunión
- sin datos
```

Tareas nuevas para `tareas/tareas.json` (3): T-001 a T-003 con `reunion: "1-1-con-laura"`.

## Criterios

- [ ] "El tema de los duplicados me preocupa" no genera tarea: no tiene acción concreta. Va a temas abiertos.
- [ ] "Yo: mirar los accesos" no se asigna a Laura ni a nadie sin confirmar: responsable `sin definir`, y se anota el motivo en temas abiertos.
- [ ] "Hay que decidir si pagamos..." es tarea, con responsable y fecha `sin definir`.
- [ ] "Lo vemos la semana que viene" no es tarea: no hay entregable.
- [ ] "El jueves" desde el 04/11 da 05/11.
- [ ] La decisión de no cambiar de proveedor de correo aparece en decisiones, no en tareas.
