# Automatización con Claude y Claude Code

Material de referencia del curso. Cubre qué es Claude, sus modelos y productos, cómo funciona Claude Code, y las piezas para automatizar trabajo: MCP, skills, agentes, hooks, comandos y más.

> **Nota sobre vigencia:** los productos de IA cambian rápido. Los nombres de modelos, planes y funciones de este documento corresponden a octubre de 2026. Antes de la clase conviene confirmar los detalles finos en la documentación oficial: https://docs.claude.com y https://support.claude.com

---

## Índice

1. [Conceptos base](#1-conceptos-base)
2. [Qué es Claude](#2-qué-es-claude)
3. [Los modelos](#3-los-modelos)
4. [Modelo vs. API vs. producto](#4-modelo-vs-api-vs-producto)
5. [Los productos de Claude](#5-los-productos-de-claude)
6. [Claude en el día a día: qué se puede hacer](#6-claude-en-el-día-a-día-qué-se-puede-hacer)
7. [Claude Code a fondo](#7-claude-code-a-fondo)
8. [MCP: conectar Claude con el mundo](#8-mcp-conectar-claude-con-el-mundo)
9. [Skills](#9-skills)
10. [Agentes y subagentes](#10-agentes-y-subagentes)
11. [Hooks](#11-hooks)
12. [Comandos personalizados y CLAUDE.md](#12-comandos-personalizados-y-claudemd)
13. [Plugins](#13-plugins)
14. [Automatización: de lo manual a lo autónomo](#14-automatización-de-lo-manual-a-lo-autónomo)
15. [Cuándo usar cada pieza](#15-cuándo-usar-cada-pieza)
16. [Buenas prácticas de prompting](#16-buenas-prácticas-de-prompting)
17. [Seguridad, permisos y buen criterio](#17-seguridad-permisos-y-buen-criterio)
18. [Limitaciones y errores comunes](#18-limitaciones-y-errores-comunes)


---

## 1. Conceptos base

| Concepto | Definición corta |
|---|---|
| **IA generativa** | Sistemas que producen texto, código, imágenes u otros contenidos a partir de una instrucción. |
| **LLM** (modelo de lenguaje grande) | Modelo entrenado con enormes cantidades de texto para predecir y generar lenguaje. Claude es un LLM. |
| **Prompt** | La instrucción o contexto que le das al modelo. |
| **Contexto / ventana de contexto** | Todo lo que el modelo "ve" en una conversación: instrucciones, historial, archivos adjuntos, resultados de herramientas. Tiene un límite. |
| **Token** | Unidad en la que el modelo procesa texto (aproximadamente una sílaba o parte de palabra). Los límites y costos se miden en tokens. |
| **Herramienta (tool)** | Capacidad que el modelo puede invocar: buscar en la web, leer un archivo, ejecutar un comando, consultar una app. |
| **Agente** | Sistema que, dado un objetivo, planifica y ejecuta varios pasos usando herramientas, y decide qué hacer según los resultados. |
| **Automatización** | Hacer que una tarea se ejecute sin repetir los pasos a mano, ya sea por un disparador, un horario o un flujo definido. |
| **Alucinación** | Cuando el modelo afirma algo falso con aparente seguridad. Por eso siempre se revisa el resultado. |

**Idea central del curso:** un chat responde; un agente *hace*. Automatizar con Claude es pasar de "le pido cosas una por una" a "defino un flujo que se ejecuta solo y yo superviso".

---

## 2. Qué es Claude

Claude es una familia de modelos de IA creada por **Anthropic**, una empresa enfocada en la investigación de seguridad de la IA. La palabra "Claude" puede referirse a:

- **La familia de modelos** (el "cerebro").
- **La app Claude** (web, escritorio y móvil), donde se conversa y se encargan tareas.
- **Los productos construidos sobre los modelos** (Claude Code, Claude in Chrome, etc.).

Es una herramienta de uso general: escribe, analiza, resume, programa, investiga, traduce, razona sobre datos y puede actuar sobre archivos y aplicaciones cuando tiene herramientas conectadas.

---

## 3. Los modelos

Claude se ofrece en varios modelos con distintos equilibrios entre capacidad, velocidad y costo. Los más recientes de acceso público:

| Modelo | Perfil | Cuándo conviene |
|---|---|---|
| **Claude Haiku 5.5** | El más rápido y liviano | Tareas simples y de alto volumen, clasificación, respuestas rápidas, subagentes baratos. |
| **Claude Sonnet 5.5** | Inteligente y eficiente para uso diario | El caballito de batalla: la mayoría de las tareas cotidianas y de programación. |
| **Claude Opus 5.5** | Más capaz | Tareas complejas, razonamiento largo, trabajo que justifica más costo y tiempo. |
| **Claude Fable 5.1** | Nivel superior (tier Mythos, con medidas de seguridad adicionales en biología, ciberseguridad e I+D de LLM) | Los trabajos más exigentes. |

Notas:

- **Mythos** es el nivel por encima de Opus. Claude Mythos Preview no es público y se usa en un grupo reducido de organizaciones (Project Glasswing). Las versiones actuales del nivel son Claude Mythos 5.1 y Claude Fable 5.1, que comparten el mismo modelo base.
- **Regla práctica:** empezar con Sonnet; subir a Opus o Fable si el resultado no alcanza; bajar a Haiku cuando la tarea es simple y se repite mucho.
- En la app se puede **cambiar de modelo a mitad de una conversación**.
- Identificadores para la API: `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`.
- El conocimiento propio de cada modelo tiene una **fecha de corte**. Para información posterior se usa búsqueda web.

---

## 4. Modelo vs. API vs. producto

Es una de las confusiones más comunes, así que conviene dejarla clara.

| Capa | Qué es | Quién la usa |
|---|---|---|
| **Modelo** | El "cerebro" de IA (Haiku, Sonnet, Opus, Fable). | Es lo que hay por debajo de todo. |
| **API** | La vía de acceso al modelo desde código. Se envía un pedido y se recibe una respuesta. | Desarrolladores que integran Claude en sus propios sistemas. |
| **Producto** | Aplicaciones listas para usar que ya integran el modelo: la app de Claude, Claude Code, Claude in Chrome. | Cualquier persona, sin programar. |

Analogía: el modelo es el motor, la API es la conexión al motor para que otros construyan vehículos, y los productos son los vehículos ya armados.

Para desarrolladores: Claude Console y la API (documentación en https://docs.claude.com). Incluye uso de herramientas (*tool use*), procesamiento por lotes, streaming y un SDK de agentes (**Claude Agent SDK**) para construir agentes propios.

---

## 5. Los productos de Claude

| Producto | Qué es | Para quién |
|---|---|---|
| **Claude (app)** | Web, escritorio y móvil. Conversación, análisis, documentos, investigación y tareas largas que entregan un trabajo terminado. | Todo el mundo. |
| **Claude Code** | Programación agéntica desde terminal, web, escritorio y móvil. | Ingeniería y personas técnicas. |
| **Claude in Chrome** | Extensión de navegador: Claude actúa en tu Chrome real, con tus sesiones iniciadas. | Tareas en sitios web. |
| **Claude for M365** | Claude dentro de las herramientas de Microsoft 365. | Equipos que trabajan en Office. |
| **Claude Tag** | Agente proactivo para equipos que vive en herramientas de colaboración (hoy, Slack). | Equipos. |
| **Claude Science** | Banco de trabajo para investigación científica, corre en las máquinas del laboratorio. | Científicos. |
| **Claude Security** | Encuentra y corrige vulnerabilidades en un código base. | Equipos de seguridad. |
| **Claude Console / API** | Plataforma para desarrolladores. | Desarrolladores. |

Además hay empaquetados por industria (Claude para Legal, para Servicios Financieros, etc.). No son productos distintos, sino la forma en que Anthropic adapta Claude a una función o sector.

**Capacidades dentro de la app** (no son productos aparte): proyectos, artefactos, skills, documentos, diseño y plugins.

> **Sobre Cowork:** las capacidades que antes se conocían como "Cowork" (que Claude trabaje de forma autónoma sobre tareas largas, archivos y apps) hoy forman parte de Claude. Si tus alumnos conocen el nombre, se aclara en voz alta.

---

## 6. Claude en el día a día: qué se puede hacer

### Tareas de conversación
- Redactar, resumir, traducir, reescribir con otro tono.
- Explicar temas, estudiar, hacer cuestionarios.
- Analizar documentos, PDF, imágenes y planillas adjuntas.
- Lluvia de ideas y planificación.

### Chat vs. trabajo autónomo

| | **Chat simple** | **Tarea larga / trabajo autónomo** |
|---|---|---|
| Interacción | Pregunta y respuesta | Le encargás un objetivo y lo ejecuta en varios pasos |
| Herramientas | Pocas o ninguna | Búsqueda, archivos, código, apps conectadas, navegador |
| Resultado | Texto en la conversación | Un entregable: documento, planilla, presentación, página |
| Tu rol | Dirigir cada paso | Definir el objetivo y revisar |
| Ejemplo | "Reescribime este mail" | "Ordená estas 200 facturas, armá una planilla y un resumen" |

### Modo Research (investigación)
Claude investiga un tema en muchas fuentes, tarda varios minutos y entrega un **informe con citas**. Sirve para comparar opciones, analizar un mercado, revisar literatura o entender una tendencia. Se revisan siempre las fuentes citadas.

### Entregables que puede producir
- **Documentos** (editables, exportables a Word, PDF, Markdown).
- **Planillas** con fórmulas.
- **Presentaciones.**
- **Diseños y mockups.**
- **Tableros (dashboards).**
- **Diagramas y pizarras.**
- **Páginas y mini herramientas web** (calculadoras, explicadores interactivos).

### Conexión con tus apps
Mediante **conectores** (basados en MCP) Claude puede leer y trabajar con tus apps: correo, calendario, almacenamiento, gestores de proyectos, etc. Si no hay conector, puede operar un navegador.

### Memoria y chats anteriores
- Se puede activar la **memoria** a partir del historial.
- Se puede permitir que Claude **busque y consulte chats anteriores**.
- Ambas opciones se activan o desactivan en Configuración.

### Escritura con tu estilo
Claude puede aprender cómo escribís y redactar mensajes que suenen como vos.

### Tareas programadas
Se puede pedir que algo corra más tarde o en un horario fijo (por ejemplo, un resumen cada lunes).

---

## 7. Claude Code a fondo

### Qué es
Una herramienta de **programación agéntica**. Trabaja directamente sobre tu proyecto: lee archivos, entiende la estructura, edita código, ejecuta comandos, corre pruebas y usa git. No es solo para programar: como puede leer, escribir y ejecutar, sirve para **automatizar tareas con archivos y datos** (renombrar, convertir, limpiar datos, generar reportes, etc.).

### Dónde se usa
Terminal, web, escritorio y móvil, además de integraciones con editores (VS Code, JetBrains).

### Chat de Claude vs. Claude Code para programar

| | Chat | Claude Code |
|---|---|---|
| Acceso al proyecto | Lo que pegues o adjuntes | Lee y modifica tu proyecto directamente |
| Ejecución | No ejecuta en tu máquina | Corre comandos, pruebas y scripts |
| Iteración | Vos copiás y pegás | Prueba, ve el error y corrige solo |
| Ideal para | Preguntas, fragmentos, explicaciones | Cambios reales en un proyecto, tareas repetitivas |

### Herramientas internas que usa
Leer archivos, buscar por nombre y contenido, editar, escribir, ejecutar comandos en la terminal, buscar en la web, descargar páginas, lanzar subagentes y llevar una lista de tareas.

### Conceptos y funciones clave

| Función | Para qué sirve |
|---|---|
| **Permisos** | Claude Code te pide autorización antes de ejecutar comandos o editar archivos. Se configuran qué acciones se permiten, se preguntan o se bloquean. |
| **Modos de permiso** | Normal (pregunta), aceptar ediciones automáticamente, **modo plan** (solo planifica, no modifica nada) y modos más permisivos para entornos controlados. |
| **Modo plan** | Claude investiga y propone un plan; vos lo aprobás antes de que toque algo. Muy útil para cambios grandes. |
| **CLAUDE.md** | Archivo de instrucciones persistentes del proyecto (convenciones, comandos, reglas). Claude lo lee al empezar. |
| **Comandos slash** | Atajos que empiezan con `/` (`/help`, `/clear`, `/compact`, `/init`, `/model`, `/mcp`, `/agents`, `/permissions`, `/memory`). Se pueden crear propios. |
| **Compactar contexto** | `/compact` resume la conversación para liberar espacio; `/clear` empieza de cero. |
| **Checkpoints / deshacer** | Permite volver atrás cambios hechos por Claude. |
| **Modo no interactivo** | `claude -p "tu pedido"` ejecuta una tarea y devuelve el resultado, ideal para scripts y automatización. |
| **Salida estructurada** | Se puede pedir la salida en JSON para encadenar con otros programas. |
| **Integración con git/GitHub** | Crea commits, ramas y pull requests; puede correr en GitHub Actions para revisar código o responder issues. |
| **Claude Agent SDK** | Permite construir tus propios agentes con las mismas capacidades que Claude Code. |
| **Tareas programadas** | Ejecutar tareas de Claude en un horario o ante un evento. |

### Ejemplo de uso rápido
```bash
# Instalar y abrir en una carpeta de proyecto
cd mi-proyecto
claude

# Pedidos de ejemplo dentro de la sesión
> Explicame la estructura de este proyecto
> Renombrá todos los .jpeg a .jpg y generá un listado en CSV
> Escribí pruebas para la función calcular_total y corrélas

# Uso no interactivo (para automatizar)
claude -p "Resumí los cambios del último commit en 3 puntos"
```

> La instalación y los requisitos cambian con las versiones. Confirmar el procedimiento actual en la documentación oficial antes de la clase.

---

## 8. MCP: conectar Claude con el mundo

**MCP (Model Context Protocol)** es un **estándar abierto** para conectar modelos de IA con herramientas y fuentes de datos externas. Sin MCP, Claude solo sabe lo que hay en la conversación. Con MCP puede leer tu calendario, consultar una base de datos, crear un ticket o mandar un mensaje.

**Analogía:** MCP es como un puerto USB universal. Cada herramienta (Slack, Drive, una base de datos) expone un "enchufe" estándar, y cualquier aplicación compatible, como Claude o Claude Code, se conecta de la misma forma.

### Qué NO es MCP
- No es un protocolo de cifrado ni de seguridad.
- No guarda tu historial ni la memoria de Claude: **conecta**.
- No es un modelo ni una API propia de Anthropic para generar texto.

### Piezas
- **Servidor MCP:** programa que expone herramientas, datos o plantillas (por ejemplo, un servidor de GitHub).
- **Cliente MCP:** la aplicación que se conecta (Claude, Claude Code).
- **Qué expone un servidor:** *tools* (acciones), *resources* (datos) y *prompts* (plantillas).

### En Claude Code
```bash
# Agregar un servidor MCP remoto
claude mcp add --transport http nombre https://url-del-servidor

# Agregar un servidor local (se ejecuta en tu máquina)
claude mcp add nombre -- comando-del-servidor

# Listar y administrar
claude mcp list
```
Dentro de una sesión, `/mcp` muestra el estado de las conexiones.

**Alcances de configuración:** local (solo vos, en ese proyecto), de proyecto (compartido con el equipo mediante un archivo `.mcp.json`) y de usuario (disponible en todos tus proyectos).

### En la app de Claude
Se llaman **conectores**. Se conectan desde la configuración y permiten trabajar con tus apps sin salir de Claude.

### Ejemplos de automatización con MCP
- "Revisá mis correos sin leer y armá una lista de pendientes en mi gestor de tareas."
- "Leé este ticket, buscá el código relacionado y proponé un arreglo."
- "Consultá la base de datos y generá el reporte semanal."

### Precauciones
- Conectá solo servidores de fuentes confiables.
- Revisá qué permisos le das a cada conector.
- El contenido que llega por una herramienta (un mail, una página) puede traer instrucciones maliciosas escondidas: es el riesgo de la **inyección de prompts** (ver sección 17).

---

## 9. Skills

Una **skill** es una **carpeta de instrucciones** (más archivos y scripts opcionales) que enseña a Claude a hacer una tarea específica de forma consistente. Claude las carga **solo cuando las necesita**, por lo que no ocupan contexto todo el tiempo.

### Estructura
```
mi-skill/
├── SKILL.md        ← obligatorio: nombre, descripción e instrucciones
├── plantilla.docx  ← opcional: recursos
└── scripts/        ← opcional: código auxiliar
```

### Ejemplo de SKILL.md
```markdown
---
name: informe-semanal
description: Genera el informe semanal de ventas a partir de la planilla del equipo. Usar cuando se pida el reporte semanal o el resumen de ventas.
---

# Informe semanal de ventas

1. Leé la planilla de ventas de la última semana.
2. Calculá total por vendedor y variación contra la semana anterior.
3. Redactá un resumen de máximo 5 líneas con lo más relevante.
4. Entregá el resultado en el formato de la plantilla adjunta.
```

### Puntos clave
- La **descripción** es lo más importante: Claude la usa para decidir cuándo activar la skill.
- Se cargan por niveles: primero solo nombre y descripción, y el resto únicamente si hace falta.
- Dónde viven: en tu usuario (disponibles siempre) o dentro del proyecto (compartidas con el equipo).
- Existen skills integradas para crear archivos (Word, Excel, PowerPoint, PDF) y se pueden crear propias.
- Se puede usar una skill por nombre, a menudo con un comando slash.

### Skill vs. otras piezas
- **Skill:** sabe *cómo* hacer algo (procedimiento).
- **MCP:** da *acceso* a algo (herramientas y datos).
- **CLAUDE.md:** reglas siempre presentes del proyecto.

---

## 10. Agentes y subagentes

### Agente
Un agente recibe un **objetivo**, **planifica**, **usa herramientas**, **observa resultados** y **decide el siguiente paso**, repitiendo hasta terminar. La diferencia con un chat es que no necesita que le indiques cada paso.

```
Objetivo → Planificar → Usar herramienta → Observar resultado → ¿Terminó? → (no) volver a planificar
                                                                    ↓ (sí)
                                                                Entregar
```

Claude Code **es** un agente. La app de Claude, cuando trabaja en tareas largas, también.

### Subagentes
Son agentes especializados a los que el agente principal les delega tareas. Cada uno trabaja con **su propio contexto**, así no se llena el contexto principal.

**Por qué usarlos:**
- Dividir una tarea grande en partes que avanzan en paralelo.
- Mantener limpio el contexto principal (el subagente devuelve solo el resumen).
- Especializar: un revisor de código, un investigador, un redactor de pruebas.
- Usar un modelo más barato para tareas simples.

### Cómo se definen en Claude Code
Archivos Markdown en la carpeta de agentes del proyecto (`.claude/agents/`) o del usuario:

```markdown
---
name: revisor-de-codigo
description: Revisa cambios de código buscando errores, problemas de seguridad y de estilo. Usar después de modificar código.
tools: Read, Grep, Glob
model: sonnet
---

Sos un revisor de código cuidadoso. Revisá los cambios recientes y devolvé:
1. Errores probables
2. Problemas de seguridad
3. Sugerencias de mejora, ordenadas por importancia
Sé concreto y citá archivo y línea.
```
Con `/agents` se administran desde la propia sesión.

### Patrones de trabajo con agentes
- **Orquestador y trabajadores:** un agente reparte y junta resultados.
- **Escritor y revisor:** uno produce, otro verifica (sin haber visto cómo se produjo).
- **Investigación en paralelo:** varios subagentes investigan temas distintos y se sintetiza.

### Cuidado
Más agentes significa más costo y más complejidad. Conviene empezar simple y delegar solo cuando aporta valor.

---

## 11. Hooks

Un **hook** es un comando que se ejecuta **automáticamente en un momento determinado** del ciclo de trabajo de Claude Code. A diferencia de pedirle algo a Claude (que puede olvidarse), un hook **siempre se ejecuta**: es determinista.

### Momentos (eventos) más usados

| Evento | Cuándo ocurre | Uso típico |
|---|---|---|
| `PreToolUse` | Antes de que Claude use una herramienta | Bloquear comandos peligrosos, validar. |
| `PostToolUse` | Después de usar una herramienta | Formatear código tras cada edición, correr un linter. |
| `UserPromptSubmit` | Cuando enviás un mensaje | Agregar contexto automático, registrar. |
| `Notification` | Cuando Claude necesita tu atención | Enviar una alerta al celular o al escritorio. |
| `Stop` | Cuando Claude termina de responder | Correr pruebas, avisar que terminó. |
| `SubagentStop` | Cuando termina un subagente | Registrar o validar su resultado. |
| `SessionStart` / `SessionEnd` | Al abrir o cerrar la sesión | Cargar contexto, limpiar. |
| `PreCompact` | Antes de compactar el contexto | Guardar información importante. |

### Ejemplo: formatear automáticamente después de editar
En el archivo de configuración (`.claude/settings.json`):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_FILE_PATHS\""
          }
        ]
      }
    ]
  }
}
```

### Ejemplo: bloquear un comando peligroso
Un hook `PreToolUse` sobre la herramienta de terminal puede revisar el comando y rechazarlo (por ejemplo, borrados masivos) antes de que se ejecute.

### Hook vs. skill vs. CLAUDE.md
- **CLAUDE.md** y **skills**: *le sugieren* a Claude qué hacer (puede fallar o ignorarlo).
- **Hooks**: *garantizan* que algo ocurra, porque lo ejecuta el sistema, no el modelo.

> El formato exacto de la configuración puede variar entre versiones. Confirmar en la documentación de hooks.

---

## 12. Comandos personalizados y CLAUDE.md

### CLAUDE.md
Archivo que Claude Code lee al comenzar. Ahí se guarda lo que querés que sepa **siempre** del proyecto. Se genera un primer borrador con `/init`.

```markdown
# Proyecto: Reportes de ventas

## Comandos
- `python generar_reporte.py` genera el reporte semanal
- `pytest` corre las pruebas

## Convenciones
- Fechas en formato DD/MM/AAAA
- Los montos siempre en pesos argentinos, sin decimales
- No modificar la carpeta /datos_originales

## Importante
- Antes de cambiar una función, buscá dónde se usa
```

Buenas prácticas: corto, concreto, actualizado. Si crece demasiado, parte del contenido pasa mejor a una skill.

### Comandos slash propios
Archivos Markdown en `.claude/commands/` que se convierten en atajos reutilizables.

```markdown
<!-- .claude/commands/resumen-diario.md -->
Revisá los cambios de hoy en el repositorio y escribí un resumen de 5 líneas
para el equipo, con lo hecho, lo pendiente y los riesgos.
```
Se usa escribiendo `/resumen-diario`.

---

## 13. Plugins

Un **plugin** empaqueta varias piezas para instalarlas juntas: comandos, skills, agentes, hooks y servidores MCP. Sirven para **compartir un flujo de trabajo completo** con un equipo o una organización (por ejemplo, un "paquete de ventas" o un "paquete de legales"). Se pueden instalar desde un catálogo o crear propios.

---

## 14. Automatización: de lo manual a lo autónomo

### Escalera de automatización

| Nivel | Qué hacés | Herramienta |
|---|---|---|
| **1. Asistido** | Pedís cosas una por una en el chat | App de Claude |
| **2. Repetible** | Guardás el procedimiento para reutilizarlo | Proyectos, skills, comandos propios |
| **3. Conectado** | Claude accede a tus apps y datos | Conectores / MCP |
| **4. Autónomo** | Claude ejecuta una tarea larga de punta a punta | Tareas largas, Claude Code, agentes |
| **5. Programado / disparado** | Corre solo según un horario o un evento | Tareas programadas, modo `-p`, GitHub Actions, SDK |

### Qué tareas conviene automatizar
**Buenas candidatas:**
- Repetitivas, con pasos definidos (reporte semanal, renombrar archivos, clasificar mails).
- De alto volumen y bajo riesgo.
- Que combinan varias herramientas.

**Malas candidatas (o que requieren supervisión humana):**
- Decisiones estratégicas o con impacto legal, financiero o médico.
- Comunicaciones delicadas (reclamos, despidos).
- Tareas creativas donde el criterio personal es el valor.
- Acciones irreversibles sin revisión previa.

### Receta para diseñar una automatización
1. **Definir** el objetivo y cómo se ve "terminado".
2. **Listar** los pasos que hoy hacés a mano.
3. **Identificar** qué herramientas y datos necesita (¿hace falta MCP?).
4. **Probar** manualmente con un caso real.
5. **Empaquetar** el procedimiento (skill, comando o agente).
6. **Agregar controles** (hooks, permisos, revisión humana).
7. **Programar** o disparar la ejecución.
8. **Medir y revisar** periódicamente.

### Ejemplos concretos
| Caso | Piezas |
|---|---|
| Reporte semanal de ventas por mail | Skill + conector de planillas y correo + tarea programada |
| Revisión automática de pull requests | Claude Code en GitHub Actions + subagente revisor |
| Clasificar y responder consultas frecuentes | Agente + conector + revisión humana antes de enviar |
| Limpieza y conversión de archivos | Claude Code con `claude -p` en un script |
| Investigación de mercado mensual | Modo Research + tarea programada + documento |
| Formateo y pruebas automáticas al programar | Hooks `PostToolUse` y `Stop` |

---

## 15. Cuándo usar cada pieza

| Quiero... | Uso |
|---|---|
| Que Claude **sepa cómo** hacer algo siempre igual | **Skill** |
| Que Claude **acceda a** una app, base de datos o servicio | **MCP / conector** |
| Que Claude **conozca reglas del proyecto** siempre | **CLAUDE.md** |
| Un **atajo** para un pedido que repito | **Comando slash propio** |
| Que algo **ocurra sí o sí** en cierto momento | **Hook** |
| **Dividir** el trabajo o aislar contexto | **Subagente** |
| Un paquete completo para **compartir** con el equipo | **Plugin** |
| Que se ejecute **sin que yo esté** | **Tarea programada / modo `-p` / SDK** |
| Investigar un tema con **fuentes citadas** | **Modo Research** |

---

## 16. Buenas prácticas de prompting

Un buen prompt tiene, en lo posible:

- **Objetivo claro:** qué querés lograr y para qué.
- **Contexto:** quién sos, a quién va dirigido, qué ya existe.
- **Formato de salida:** tabla, lista, longitud, tono, idioma.
- **Ejemplos:** uno bueno (y, si ayuda, uno malo) de lo que esperás.
- **Restricciones:** qué NO hacer.
- **Criterio de "terminado":** cómo sabés que está bien.

### Prácticas que ayudan
- Ser específico en lugar de vago.
- Dar el motivo de una instrucción: el modelo generaliza mejor.
- Dividir tareas grandes en etapas.
- Pedir que **explique su razonamiento** o que **pregunte** si le falta información.
- Iterar: el primer resultado es un borrador.

### Prácticas que NO ayudan
- Escribir todo en mayúsculas o con insistencia exagerada.
- Prompts larguísimos y desordenados.
- Dar por hecho que Claude "sabe" cosas de tu empresa que nunca le contaste.

### Ejemplo: de vago a bueno
| Vago | Mejor |
|---|---|
| "Haceme un resumen" | "Resumí este informe en 5 puntos para un gerente que no leyó el documento. Destacá riesgos y decisiones pendientes. Tono formal, español rioplatense." |
| "Arreglá el código" | "La función `calcular_total` devuelve un valor incorrecto con descuentos mayores al 50 %. Reproducí el error, corregilo y agregá una prueba." |

---

## 17. Seguridad, permisos y buen criterio

### Permisos
- Empezá con permisos restrictivos y ampliá con criterio.
- Usá el **modo plan** para cambios grandes.
- Evitá modos que saltean confirmaciones, salvo en entornos aislados y descartables.
- Probá las automatizaciones sobre **copias** de tus datos.

### Inyección de prompts
Cuando Claude lee contenido externo (una página, un mail, un documento), ese contenido puede incluir **instrucciones ocultas** que intentan manipularlo. Reglas de oro:
- Las instrucciones válidas vienen **de vos**, no del contenido que Claude lee.
- Desconfiá de conectores y servidores de origen desconocido.
- Mantené una persona en el circuito para acciones sensibles (enviar, pagar, borrar, publicar).

### Datos sensibles
- No pegues contraseñas, claves ni datos personales de terceros sin necesidad.
- Revisá las políticas de privacidad y retención de tu plan o de tu organización.
- Las organizaciones pueden controlar capacidades y acceso a red desde la administración.

### Criterio profesional
- **Siempre revisá el resultado**, especialmente en tareas importantes.
- En temas legales, médicos o financieros, Claude informa y orienta pero **no reemplaza a un profesional**.
- Verificá cifras, citas y fuentes.

---

## 18. Limitaciones y errores comunes

| Limitación | Qué hacer |
|---|---|
| **Puede inventar datos** (alucinar), incluso con un buen prompt | Pedir fuentes, verificar, usar Research o búsqueda web. |
| **Fecha de corte de conocimiento** | Activar búsqueda web para información reciente. |
| **Contexto limitado** | Compactar, dividir tareas, usar subagentes y archivos. |
| **Puede malinterpretar un pedido ambiguo** | Dar contexto y ejemplos; pedirle que pregunte. |
| **Resultados distintos en cada ejecución** | Para lo que debe ser idéntico, usar hooks, scripts y skills con pasos fijos. |
| **No recuerda conversaciones pasadas por defecto** | Activar memoria o búsqueda de chats, o usar CLAUDE.md y proyectos. |
| **Puede equivocarse con cálculos largos** | Pedirle que ejecute código para calcular. |

**Errores típicos de principiantes**
1. Pedir todo en un solo mensaje enorme.
2. No revisar el resultado.
3. No dar contexto.
4. Automatizar antes de entender el proceso a mano.
5. Dar permisos amplios "para que no moleste".
6. Usar siempre el modelo más grande (cuesta más y tarda más sin necesidad).

---

