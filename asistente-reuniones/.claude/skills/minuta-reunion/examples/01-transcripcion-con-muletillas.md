# Caso 01: transcripción con muletillas y responsables difusos

**Qué prueba:** pasar de una transcripción desordenada a una minuta limpia. Fechas relativas de varios días de la semana, una tarea sin responsable, una tarea asignada a alguien que no estuvo, y una propuesta sin acuerdo que no debe ser tarea.

## Entrada

Reunión (calendario): "Retro de octubre y plan de noviembre", 06/11/2026 10:00 a 11:00.
Invitados: Sofía Herrera, Pablo Ibáñez, Martín Ruiz, Valentina Ríos (opcional), Laura Gómez.
Asistieron (según la transcripción): Laura, Sofía, Pablo, Martín, Valentina.
`tareas/tareas.json` antes: `[]`

Notas:

```text
Laura: bueno, eh, arrancamos. O sea, lo de octubre, la caída del portal del 22, fue un tema de certificado vencido.
Sofía: sí, y la comunicación fue tarde, nos enteramos los últimos. Yo creo que tenemos que tener un canal de incidentes, no sé.
Pablo: a ver, lo del protocolo de comunicación, yo lo tengo, digamos, el borrador lo tengo el miércoles.
Martín: el certificado lo renueva el proveedor de hosting, alguien tiene que hablar con ellos, ¿no?  (silencio)
Valentina: yo le pido a Soporte la lista de los 12 tickets del 22 y te la mando el lunes.
Laura: perfecto. Y lo de noviembre: el CRM arranca solo si se aprueba el presupuesto, eso lo define Dirección el lunes.
Sofía: y lo de la persona nueva para Soporte, eso quedó en el aire.
Pablo: bueno, lo cierro yo y lo mando a todos antes del viernes 13.
Laura: Martín, ¿vos mandás el detalle de gastos de octubre?
Martín: sí, el martes lo tengo.
Laura: genial. Y que Diego de CloudCRM revise las fechas del plan de migración, que hoy no vino.
Laura: nos juntamos el 13 a las 10 para ver pendientes. Listo, cerramos.
```

## Salida esperada

```markdown
# Minuta: Retro de octubre y plan de noviembre

## Datos
- Fecha y hora: 06/11/2026 10:00 a 11:00
- Participantes: Laura Gómez (organizadora), Sofía Herrera, Pablo Ibáñez, Martín Ruiz, Valentina Ríos

## Resumen
- La caída del portal del 22/10 se debió a un certificado vencido, y la comunicación llegó tarde.
- Se habló de un protocolo de comunicación de incidentes, que Pablo redacta.
- El plan de noviembre depende del presupuesto que define Dirección el lunes 09/11.

## Decisiones
- Ninguna decisión cerrada en la reunión.

## Tareas
| id | descripción | responsable | fecha límite | estado |
|----|-------------|-------------|--------------|--------|
| T-001 | Armar el borrador del protocolo de comunicación de incidentes | Pablo Ibáñez | 11/11 (el miércoles) | abierta |
| T-002 | Cerrar y enviar a todos el protocolo de comunicación de incidentes | Pablo Ibáñez | 13/11 (antes del viernes 13) | abierta |
| T-003 | Enviar a Laura la lista de los 12 tickets de la caída del 22/10 | Valentina Ríos | 09/11 (para el lunes) | abierta |
| T-004 | Enviar el detalle de gastos de octubre | Martín Ruiz | 10/11 (el martes) | abierta |
| T-005 | Hablar con el proveedor de hosting para renovar el certificado | sin definir | sin definir | abierta |
| T-006 | Revisar las fechas del plan de migración del CRM | sin definir | sin definir | abierta |

## Temas abiertos
- Canal de incidentes: lo propuso Sofía, sin acuerdo ni responsable.
- Persona nueva para Soporte: quedó en el aire.
- Inicio del CRM en noviembre: depende del presupuesto que define Dirección el lunes 09/11.
- T-005 y T-006 sin responsable: T-006 estaba asignada a Diego Paz, que no estuvo en la reunión.

## Próxima reunión
- 13/11, 10:00 (ver pendientes). Confirmar si es el viernes 13/11 a las 10:00.
```

Tareas nuevas para `tareas/tareas.json` (6): T-001 a T-006 con `reunion: "retro-de-octubre-y-plan-de-noviembre"`.

## Criterios

- [ ] Las seis tareas están, con las fechas convertidas: el miércoles = 11/11, el martes = 10/11, para el lunes = 09/11, antes del viernes 13 = 13/11.
- [ ] Cada fecha relativa lleva la frase original entre paréntesis.
- [ ] T-006 queda con responsable `sin definir`, porque Diego no estuvo.
- [ ] "Canal de incidentes" queda en temas abiertos y no se convierte en tarea.
- [ ] "Yo creo que tenemos que tener un canal" no genera ninguna tarea.
- [ ] El silencio de Martín no se convierte en responsable de T-005.
- [ ] La próxima reunión se toma de la frase "nos juntamos el 13 a las 10".
