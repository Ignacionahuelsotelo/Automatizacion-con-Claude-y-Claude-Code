/*
 * Mi Café, front. Un solo archivo (sin módulos ni build), ordenado en secciones:
 *   1. Referencias al DOM y estado
 *   2. API (único punto de `fetch`)
 *   3. Gustos 👍/👎
 *   4. Preferencias
 *   5. Indicadores
 *   6. Noticias de ayer
 *   7. Resumen
 *   8. Caja de preguntas
 *   9. Arranque
 *
 * Contrato de la API que usa el front (todo JSON; los errores traen `errores`: lista de frases en español):
 *   GET  /api/preferencias  -> {preferencias:{indicadores,temas}, opciones:{indicadores:{clave:texto}, temas}, aviso?}
 *   POST /api/preferencias  {indicadores,temas} -> {ok, preferencias} | 400 {ok:false, errores}
 *   GET  /api/gustos        -> {votos:[{tipo,clave,voto}], aviso?}
 *   POST /api/gustos        {tipo,clave,voto|null,titulo?,medio?,seccion?} -> {ok, votos} | 400 {errores}
 *   GET  /api/indicadores   -> {indicadores:[{nombre,valor,fecha,fuente,desactualizado}], avisos:[texto]}
 *   GET  /api/noticias      -> {notas:[{titulo,link,medio,seccion,fecha}], fallas:[{medio,seccion,motivo}]}
 *   GET  /api/claude        -> {disponible, estado:ok|no_instalado|no_responde|con_error, mensaje} (siempre 200)
 *   GET  /api/resumen       -> {resumen: null | {fecha,generado_en,texto,indicadores,chequeo:{aprobado,no_cumple},
 *                                pedido? (texto que la persona pidió ese día),
 *                                notas:[{titulo,medio,seccion,link}]}} (`notas` se calcula al responder; sirve para votar)
 *   POST /api/resumen       {pedido?} -> 202 {ok, estado} (empieza a armarlo en segundo plano)
 *                              | 400 {ok:false, errores} si el pedido no valida | 409 {ok:false, errores} si ya hay uno
 *   GET  /api/resumen/estado -> {estado:libre|en_curso|listo|fallo, etapa, etapas:[{clave,texto,situacion:pendiente|en_curso|hecha}],
 *                                intento, intentos_max, inicio, resultado?:{resumen,avisos} (listo), errores?, avisos? (fallo)}
 *   POST /api/preguntas     {fecha,link,pregunta} -> {ok, respuesta, link} | error {ok:false, errores}
 * El front no calcula ni reformatea números: muestra los textos tal como los manda el servidor.
 */
(function () {
  "use strict";

  // --- 1. Referencias al DOM y estado -----------------------------------------
  const $ = (id) => document.getElementById(id);

  const SECCIONES = ["Política", "Economía", "Internacional", "Deportes", "Tecnología"];
  const APERTURAS = ["Lo más importante de hoy:", "Lo que viene hoy:"];

  const dom = {
    avisoPrefs: $("aviso"),
    estadoPrefs: $("estado"),
    estadoGustos: $("estado-gustos"),
    estadoVotoResumen: $("estado-voto-resumen"),
    listaIndicadores: $("lista-indicadores"),
    estadoIndicadores: $("estado-indicadores"),
    avisosIndicadores: $("avisos-indicadores"),
    listaNoticias: $("lista-noticias"),
    estadoNoticias: $("estado-noticias"),
    avisosNoticias: $("avisos-noticias"),
    botonResumen: $("boton-resumen"),
    pedido: $("pedido-noticias"),
    contadorPedido: $("contador-pedido"),
    estadoClaude: $("estado-claude"),
    estadoResumen: $("estado-resumen"),
    etapasResumen: $("etapas-resumen"),
    contenidoResumen: $("resumen"),
    avisoCorrector: $("aviso-corrector"),
    cabeceraResumen: $("cabecera-resumen"),
    cajaPreguntas: $("caja-preguntas"),
    notaElegida: $("nota-elegida"),
    campoPregunta: $("pregunta"),
    botonPregunta: $("boton-pregunta"),
    estadoPregunta: $("estado-pregunta"),
    respuestaPregunta: $("respuesta-pregunta"),
  };

  const votosGuardados = new Map(); // "tipo|clave" -> "me_gusta" | "no_me_gusta"
  let notaActual = null; // {fecha, link, titulo, boton} de la nota elegida

  // Muestra un aviso en una caja; sin líneas la oculta.
  function mostrarAvisos(caja, lineas) {
    caja.textContent = (lineas || []).join(" ");
    caja.hidden = !lineas || lineas.length === 0;
  }

  const MAXIMO_PEDIDO = 500; // el que vale es el del servidor (MAXIMO_PEDIDO_USUARIO)

  // --- 2. API: único punto de `fetch` -----------------------------------------
  // Devuelve siempre {ok, red, datos, errores}; nunca tira.
  //   red: true si no hubo conexión con el servidor.
  //   datos: el JSON (también en errores HTTP, puede traer `avisos`); null si no era JSON.
  //   errores: frases en español para mostrar (las del servidor, o una propia si no hay).
  async function api(ruta, { metodo = "GET", cuerpo } = {}) {
    const opciones = { method: metodo };
    if (cuerpo !== undefined) {
      opciones.headers = { "Content-Type": "application/json" };
      opciones.body = JSON.stringify(cuerpo);
    }
    let respuesta;
    try {
      respuesta = await fetch(ruta, opciones);
    } catch (error) {
      return { ok: false, red: true, datos: null, errores: ["No se pudo conectar con el servidor."] };
    }
    let datos = null;
    try {
      datos = await respuesta.json();
    } catch (error) {
      return { ok: false, red: false, datos: null, errores: ["El servidor respondió algo que no se entiende."] };
    }
    const ok = respuesta.ok && datos !== null && datos.ok !== false;
    const errores = ok ? [] : (datos && Array.isArray(datos.errores) && datos.errores.length
      ? datos.errores
      : [`El servidor respondió con un error (${respuesta.status}).`]);
    return { ok, red: false, datos, errores };
  }

  // --- 3. Gustos 👍/👎 ---------------------------------------------------------
  // Votos de notas (clave: link) y de temas (clave: nombre). Un voto repetido se quita.
  const ICONOS_VOTO = {
    me_gusta: "M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 2 2v4h6a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.8 20H7",
    no_me_gusta: "M7 13V4H4v9zM7 13l4 8a2 2 0 0 0 2-2v-4h6a2 2 0 0 0 2-2.3l-1.2-7A2 2 0 0 0 17.8 4H7",
  };
  const SVG_NS = "http://www.w3.org/2000/svg";

  function crearIcono(trazo) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    const camino = document.createElementNS(SVG_NS, "path");
    camino.setAttribute("d", trazo);
    svg.appendChild(camino);
    return svg;
  }

  function claveVoto(tipo, clave) {
    return tipo + "|" + clave;
  }

  function recibirVotos(votos) {
    votosGuardados.clear();
    votos.forEach((voto) => votosGuardados.set(claveVoto(voto.tipo, voto.clave), voto.voto));
    pintarVotos();
  }

  // Marca el 👍 o el 👎 que corresponde a cada botón según lo guardado.
  function pintarVotos() {
    document.querySelectorAll("button[data-tipo]").forEach((boton) => {
      const activo = votosGuardados.get(claveVoto(boton.dataset.tipo, boton.dataset.clave)) === boton.dataset.voto;
      boton.setAttribute("aria-pressed", String(activo));
      boton.classList.toggle("activo", activo);
    });
  }

  // `destino` es el <p> donde se muestra el mensaje (por defecto, el de "Noticias de ayer").
  async function votar(tipo, clave, voto, nota, destino) {
    const quitar = votosGuardados.get(claveVoto(tipo, clave)) === voto;
    const cuerpo = { tipo, clave, voto: quitar ? null : voto };
    if (nota && !quitar) {
      cuerpo.titulo = nota.titulo;
      cuerpo.medio = nota.medio;
      cuerpo.seccion = nota.seccion;
    }
    destino = destino || (tipo === "nota" ? dom.estadoGustos : dom.estadoPrefs);
    destino.textContent = "Guardando voto…";
    const r = await api("/api/gustos", { metodo: "POST", cuerpo });
    if (r.red) {
      destino.textContent = r.errores[0];
    } else if (!r.ok) {
      destino.textContent = "No se guardó el voto: " + r.errores.join(" ");
    } else {
      recibirVotos(r.datos.votos);
      destino.textContent = quitar ? "Voto quitado." : "Voto guardado.";
    }
  }

  // `descripcion` (título de la nota o nombre del tema) da el nombre accesible completo al botón.
  function crearBotonesVoto(tipo, clave, nota, descripcion, destino) {
    const grupo = document.createElement("span");
    grupo.className = "votos";
    grupo.setAttribute("role", "group");
    [["me_gusta", "Me gusta"], ["no_me_gusta", "No me gusta"]].forEach(([voto, texto]) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "voto";
      boton.dataset.tipo = tipo;
      boton.dataset.clave = clave;
      boton.dataset.voto = voto;
      boton.title = texto;
      boton.setAttribute("aria-label", descripcion ? `${texto}: ${descripcion}` : texto);
      boton.appendChild(crearIcono(ICONOS_VOTO[voto]));
      boton.addEventListener("click", () => votar(tipo, clave, voto, nota, destino));
      grupo.appendChild(boton);
    });
    return grupo;
  }

  async function cargarGustos() {
    const r = await api("/api/gustos");
    if (!r.ok) {
      dom.estadoGustos.textContent = "No se pudieron cargar los gustos.";
      return;
    }
    recibirVotos(r.datos.votos);
    dom.estadoGustos.textContent = r.datos.aviso || "";
  }

  // --- 4. Preferencias ---------------------------------------------------------
  function crearCasilla(grupo, valor, texto, marcada) {
    const etiqueta = document.createElement("label");
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.name = grupo;
    casilla.value = valor;
    casilla.checked = marcada;
    casilla.addEventListener("change", guardarPreferencias);
    etiqueta.appendChild(casilla);
    etiqueta.appendChild(document.createTextNode(" " + texto));
    return etiqueta;
  }

  function elegidas(grupo) {
    return Array.from(document.querySelectorAll("input[type=checkbox]"))
      .filter((casilla) => casilla.name === grupo && casilla.checked)
      .map((casilla) => casilla.value);
  }

  function dibujarPreferencias(datos) {
    const prefs = datos.preferencias;
    const opciones = datos.opciones;
    $("indicadores").replaceChildren(
      ...Object.entries(opciones.indicadores).map(([clave, texto]) =>
        crearCasilla("indicadores", clave, texto, prefs.indicadores.includes(clave)))
    );
    $("temas").replaceChildren(
      ...opciones.temas.map((tema) => {
        const grupo = document.createElement("span");
        grupo.className = "tema";
        grupo.appendChild(crearCasilla("temas", tema, tema, prefs.temas.includes(tema)));
        grupo.appendChild(crearBotonesVoto("tema", tema, undefined, `tema ${tema}`));
        return grupo;
      })
    );
    pintarVotos();
  }

  async function cargarPreferencias() {
    const r = await api("/api/preferencias");
    if (!r.ok) {
      dom.estadoPrefs.textContent = "No se pudieron cargar las preferencias.";
      return;
    }
    dibujarPreferencias(r.datos);
    dom.avisoPrefs.textContent = r.datos.aviso || "";
    dom.avisoPrefs.hidden = !r.datos.aviso;
  }

  async function guardarPreferencias() {
    const cuerpo = { indicadores: elegidas("indicadores"), temas: elegidas("temas") };
    dom.estadoPrefs.textContent = "Guardando…";
    const r = await api("/api/preferencias", { metodo: "POST", cuerpo });
    if (r.red) {
      dom.estadoPrefs.textContent = r.errores[0];
    } else if (!r.ok) {
      dom.estadoPrefs.textContent = "No se guardó: " + r.errores.join(" ");
    } else {
      dom.avisoPrefs.hidden = true;
      dom.estadoPrefs.textContent = "Guardado.";
      cargarIndicadores();
      cargarNoticias();
    }
  }

  // --- 5. Indicadores ----------------------------------------------------------
  function dibujarIndicador(indicador) {
    const elemento = document.createElement("li");
    const nombre = document.createElement("span");
    nombre.className = "ind-nombre";
    nombre.textContent = indicador.nombre;

    const valor = document.createElement("span");
    valor.className = "ind-valor" + (indicador.valor ? "" : " vacio");
    valor.textContent = indicador.valor || "sin dato";

    const detalle = document.createElement("span");
    detalle.className = "ind-meta";
    detalle.textContent = indicador.valor
      ? `${indicador.fecha} · ${indicador.fuente}`
      : indicador.fuente;
    if (indicador.desactualizado) {
      const marca = document.createElement("em");
      marca.textContent = " · Desactualizado";
      detalle.appendChild(marca);
    }
    elemento.append(nombre, valor, detalle);
    return elemento;
  }

  async function cargarIndicadores() {
    dom.estadoIndicadores.textContent = "Cargando indicadores…";
    const r = await api("/api/indicadores");
    if (!r.ok) {
      dom.estadoIndicadores.textContent = "No se pudieron cargar los indicadores.";
      return;
    }
    dom.listaIndicadores.replaceChildren(...r.datos.indicadores.map(dibujarIndicador));
    mostrarAvisos(dom.avisosIndicadores, r.datos.avisos);
    dom.estadoIndicadores.textContent = "";
  }

  // --- 6. Noticias de ayer -----------------------------------------------------
  function textoFalla(falla) {
    return `No se pudo leer el feed de ${falla.medio} (${falla.seccion}): ${falla.motivo}.`;
  }

  function crearEnlaceExterno(url, texto) {
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.target = "_blank";
    enlace.rel = "noopener noreferrer";
    enlace.textContent = texto;
    return enlace;
  }

  function dibujarNoticia(nota) {
    const elemento = document.createElement("li");
    elemento.appendChild(crearEnlaceExterno(nota.link, nota.titulo));

    const detalle = document.createElement("span");
    detalle.className = "nota-meta";
    detalle.textContent = `${nota.medio} · ${nota.seccion} · ${nota.fecha}`;
    const pie = document.createElement("div");
    pie.className = "nota-pie";
    pie.append(detalle, crearBotonesVoto("nota", nota.link, nota, nota.titulo));
    elemento.appendChild(pie);
    return elemento;
  }

  async function cargarNoticias() {
    dom.estadoNoticias.textContent = "Cargando noticias…";
    const r = await api("/api/noticias");
    if (!r.ok) {
      dom.estadoNoticias.textContent = "No se pudieron cargar las noticias.";
      return;
    }
    dom.listaNoticias.replaceChildren(...r.datos.notas.map(dibujarNoticia));
    pintarVotos();
    mostrarAvisos(dom.avisosNoticias, r.datos.fallas.map(textoFalla));
    dom.estadoNoticias.textContent = r.datos.notas.length
      ? ""
      : "No hay notas de ayer para los temas elegidos.";
  }

  // --- 7. Resumen --------------------------------------------------------------
  function fechaLegible(fecha) {
    const [anio, mes, dia] = fecha.split("-");
    return `${dia}/${mes}/${anio}`;
  }

  function crearParrafoEnlace(url) {
    const parrafo = document.createElement("p");
    const enlace = crearEnlaceExterno(url, url);
    enlace.className = "enlace";
    parrafo.appendChild(enlace);
    return parrafo;
  }

  function crearParrafo(texto, clase) {
    const parrafo = document.createElement("p");
    if (clase) parrafo.className = clase;
    parrafo.textContent = texto;
    return parrafo;
  }

  // El título de cada nota es un botón que la elige para preguntarle a Claude.
  function crearTituloNota(linea, link, fecha) {
    const titulo = document.createElement("h4");
    if (!link) {
      titulo.textContent = linea;
      return titulo;
    }
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "titulo-nota";
    boton.textContent = linea;
    boton.title = "Preguntar sobre esta nota";
    boton.setAttribute("aria-pressed", "false");
    boton.addEventListener("click", () => elegirNota({ fecha, link, titulo: linea, boton }));
    titulo.appendChild(boton);
    return titulo;
  }

  // Convierte el texto del resumen en elementos. Los bloques se separan con línea en blanco;
  // dentro de una nota, la primera línea es el título, la anterior al enlace es "Medio, fecha"
  // y el enlace va solo. Todo con textContent, sin HTML del modelo.
  function elementosDelResumen(texto, fecha, notas) {
    const elementos = [];
    const notasPorLink = new Map((notas || []).map((nota) => [nota.link, nota]));
    let votada = false; // solo el primer link de cada bloque lleva botones
    (texto || "").split(/\n\s*\n/).forEach((bloque) => {
      const lineas = bloque.split("\n").map((linea) => linea.trim()).filter(Boolean);
      let esperaTitulo = true;
      votada = false;
      lineas.forEach((linea, indice) => {
        const siguiente = lineas[indice + 1] || "";
        if (SECCIONES.includes(linea)) {
          const encabezado = document.createElement("h3");
          encabezado.textContent = linea;
          elementos.push(encabezado);
        } else if (APERTURAS.some((inicio) => linea.startsWith(inicio))) {
          elementos.push(crearParrafo(linea, "destacado"));
          esperaTitulo = false;
        } else if (/^https?:\/\//.test(linea)) {
          elementos.push(crearParrafoEnlace(linea));
          const nota = notasPorLink.get(linea);
          if (nota && !votada) {
            votada = true;
            const pie = document.createElement("div");
            pie.className = "nota-pie votos-nota";
            pie.appendChild(crearBotonesVoto("nota", nota.link, nota, nota.titulo, dom.estadoVotoResumen));
            elementos.push(pie);
          }
        } else if (esperaTitulo) {
          const link = lineas.slice(indice + 1).find((otra) => /^https?:\/\//.test(otra));
          elementos.push(crearTituloNota(linea, link, fecha));
          esperaTitulo = false;
        } else if (linea.startsWith("Por qué importa:")) {
          elementos.push(crearParrafo(linea, "por-que"));
        } else if (/^https?:\/\//.test(siguiente)) {
          elementos.push(crearParrafo(linea, "fuente"));
        } else {
          elementos.push(crearParrafo(linea));
        }
      });
    });
    return elementos;
  }

  function limpiarResumen() {
    dom.avisoCorrector.hidden = true;
    dom.avisoCorrector.textContent = "";
    dom.cabeceraResumen.hidden = true;
    dom.cabeceraResumen.textContent = "";
    dom.contenidoResumen.replaceChildren();
    dom.estadoVotoResumen.textContent = "";
    ocultarCaja();
  }

  function mostrarResumen(resumen) {
    limpiarResumen();
    if (!resumen) {
      dom.contenidoResumen.appendChild(crearParrafo("Todavía no hay un resumen guardado. Tocá «Preparar el de hoy»."));
      return;
    }
    dom.cabeceraResumen.textContent = `Resumen del ${fechaLegible(resumen.fecha)}, con las notas de ayer. Preparado el ${resumen.generado_en}.`;
    if (resumen.pedido) {
      dom.cabeceraResumen.appendChild(document.createElement("br"));
      dom.cabeceraResumen.appendChild(document.createTextNode(`Pedido de hoy: "${resumen.pedido}"`));
    }
    dom.cabeceraResumen.hidden = false;

    if (resumen.chequeo && !resumen.chequeo.aprobado) {
      dom.avisoCorrector.textContent = "Aviso del corrector: el resumen no cumple estas reglas: "
        + (resumen.chequeo.no_cumple || []).join(" ");
      dom.avisoCorrector.hidden = false;
    }
    dom.contenidoResumen.replaceChildren(...elementosDelResumen(resumen.texto, resumen.fecha, resumen.notas));
    pintarVotos();
  }

  async function cargarResumen() {
    const r = await api("/api/resumen");
    if (!r.ok) {
      dom.estadoResumen.textContent = "No se pudo cargar el último resumen guardado.";
      return;
    }
    mostrarResumen(r.datos.resumen);
  }

  // Los avisos que vienen con el resumen (fuentes caídas, datos viejos) van a sus secciones.
  function mostrarAvisosDelResumen(avisos) {
    if (!avisos) return;
    mostrarAvisos(dom.avisosIndicadores, avisos.indicadores);
    mostrarAvisos(dom.avisosNoticias, (avisos.noticias || []).map(textoFalla));
  }

  // Chequea si Claude está disponible y lo muestra junto al botón. Devuelve true si lo está.
  async function comprobarClaude() {
    const r = await api("/api/claude");
    if (!r.datos || r.red) {
      dom.estadoClaude.textContent = "No se pudo comprobar si Claude está disponible.";
      return false;
    }
    dom.estadoClaude.textContent = r.datos.disponible ? "Claude: listo" : r.datos.mensaje;
    return r.datos.disponible === true;
  }

  // Armado en segundo plano (spec 30): el POST lo inicia y la página consulta el estado cada 1,5 s.
  const INTERVALO_ESTADO_MS = 1500;
  const FALLOS_SEGUIDOS_MAXIMOS = 3;
  let siguiendoResumen = false;

  function textoEtapa(etapa, estado) {
    const intento = estado.intento && etapa.clave === "redactando"
      ? ` (intento ${estado.intento} de ${estado.intentos_max})` : "";
    return etapa.texto + intento;
  }

  function pintarEtapas(estado) {
    const marcas = { hecha: "✓ ", en_curso: "→ ", pendiente: "· " };
    dom.etapasResumen.replaceChildren(...estado.etapas.map((etapa) => {
      const item = document.createElement("li");
      item.className = "etapa " + etapa.situacion;
      if (etapa.situacion === "en_curso") item.setAttribute("aria-current", "step");
      item.textContent = marcas[etapa.situacion] + textoEtapa(etapa, estado);
      return item;
    }));
    dom.etapasResumen.hidden = false;
  }

  function ocuparResumen(ocupado) {
    dom.botonResumen.disabled = ocupado;
    dom.pedido.disabled = ocupado;
    if (ocupado) {
      dom.botonResumen.setAttribute("aria-busy", "true");
      dom.contenidoResumen.setAttribute("aria-busy", "true");
    } else {
      dom.botonResumen.removeAttribute("aria-busy");
      dom.contenidoResumen.removeAttribute("aria-busy");
    }
  }

  function terminarSeguimiento() {
    siguiendoResumen = false;
    dom.etapasResumen.hidden = true;
    dom.etapasResumen.replaceChildren();
    ocuparResumen(false);
  }

  async function mostrarResultado(estado) {
    if (estado.estado === "listo") {
      const { resumen, avisos } = estado.resultado;
      mostrarAvisosDelResumen(avisos);
      dom.listaIndicadores.replaceChildren(...resumen.indicadores.map(dibujarIndicador));
      mostrarResumen(resumen);
      dom.estadoResumen.textContent = "";
      dom.pedido.value = ""; // salió bien: el pedido ya quedó en el resumen
      actualizarContador();
    } else {
      mostrarAvisosDelResumen(estado.avisos);
      dom.estadoResumen.textContent = "No se pudo preparar el resumen: " + (estado.errores || []).join(" ");
      await cargarResumen(); // se vuelve a mostrar el último resumen guardado (si hay)
    }
  }

  // Consulta el estado hasta que termine. Tres fallos de red seguidos frenan el seguimiento.
  async function seguirResumen() {
    if (siguiendoResumen) return;
    siguiendoResumen = true;
    ocuparResumen(true);
    let fallos = 0;
    while (true) {
      const r = await api("/api/resumen/estado");
      if (!r.ok || !r.datos || !Array.isArray(r.datos.etapas)) {
        fallos += 1;
        if (fallos >= FALLOS_SEGUIDOS_MAXIMOS) {
          terminarSeguimiento();
          dom.estadoResumen.textContent = "Se perdió la conexión con el servidor. Revisá que siga andando y recargá la página.";
          return;
        }
      } else {
        fallos = 0;
        const estado = r.datos;
        if (estado.estado === "en_curso") {
          pintarEtapas(estado);
          dom.estadoResumen.textContent = "Preparando el resumen. Puede tardar varios minutos.";
        } else {
          terminarSeguimiento();
          if (estado.estado !== "libre") await mostrarResultado(estado);
          return;
        }
      }
      await new Promise((resolver) => setTimeout(resolver, INTERVALO_ESTADO_MS));
    }
  }

  function actualizarContador() {
    dom.contadorPedido.textContent = `${dom.pedido.value.length}/${MAXIMO_PEDIDO}`;
  }

  async function prepararResumen() {
    ocuparResumen(true);
    limpiarResumen();
    dom.estadoResumen.textContent = "Iniciando…";
    const texto = dom.pedido.value.trim();
    const cuerpo = texto ? { pedido: texto } : undefined; // vacío: no se manda el campo
    const r = await api("/api/resumen", { metodo: "POST", cuerpo });
    // 409: ya había uno en curso (otra pestaña o una recarga): se retoma el seguimiento.
    const yaEnCurso = !r.ok && !r.red && r.datos && r.datos.estado === undefined
      && r.errores.some((texto) => texto.startsWith("Ya se está preparando"));
    if (!r.ok && !yaEnCurso) {
      dom.estadoResumen.textContent = r.red
        ? "No se pudo preparar el resumen. Revisá que el servidor siga andando."
        : "No se pudo preparar el resumen: " + r.errores.join(" ");
      ocuparResumen(false);
      await cargarResumen();
      return;
    }
    await seguirResumen();
  }

  // Al cargar: si hay un armado en curso se retoma; si terminó, se muestra su resultado.
  async function retomarResumen() {
    const r = await api("/api/resumen/estado");
    if (!r.ok || !r.datos) return;
    if (r.datos.estado === "en_curso") {
      ocuparResumen(true); // el botón arranca deshabilitado
      seguirResumen();
    }
  }

  // --- 8. Caja de preguntas ----------------------------------------------------
  // Se elige una nota tocando su título en el resumen. La respuesta sale solo de esa nota
  // (la arma el servidor) y muestra el link de la nota.
  function limpiarRespuesta() {
    dom.estadoPregunta.textContent = "";
    dom.respuestaPregunta.replaceChildren();
  }

  function elegirNota(elegida) {
    document.querySelectorAll("button.titulo-nota").forEach((boton) => boton.setAttribute("aria-pressed", "false"));
    elegida.boton.setAttribute("aria-pressed", "true");
    notaActual = elegida;
    dom.notaElegida.textContent = `Nota elegida: «${elegida.titulo}».`;
    dom.botonPregunta.disabled = false;
    dom.cajaPreguntas.hidden = false;
    limpiarRespuesta();
  }

  function ocultarCaja() {
    notaActual = null;
    dom.cajaPreguntas.hidden = true;
    dom.notaElegida.textContent = "";
    dom.campoPregunta.value = "";
    dom.botonPregunta.disabled = true;
    limpiarRespuesta();
  }

  function mostrarRespuesta(datos) {
    dom.respuestaPregunta.replaceChildren(
      crearParrafo("Respuesta, según la nota:", "fuente"),
      crearParrafo(datos.respuesta),
      crearParrafoEnlace(datos.link)
    );
  }

  async function preguntar() {
    if (!notaActual) return;
    const pregunta = dom.campoPregunta.value.trim();
    if (!pregunta) {
      dom.estadoPregunta.textContent = "Escribí una pregunta.";
      return;
    }
    dom.botonPregunta.disabled = true;
    dom.respuestaPregunta.replaceChildren();
    dom.estadoPregunta.textContent = "Pensando… Claude está leyendo la nota. Puede tardar hasta 5 minutos.";
    try {
      const r = await api("/api/preguntas", {
        metodo: "POST",
        cuerpo: { fecha: notaActual.fecha, link: notaActual.link, pregunta },
      });
      if (r.red) {
        dom.estadoPregunta.textContent = r.errores[0];
      } else if (!r.ok) {
        dom.estadoPregunta.textContent = "No se pudo responder: " + r.errores.join(" ");
      } else {
        dom.estadoPregunta.textContent = "";
        mostrarRespuesta(r.datos);
      }
    } finally {
      dom.botonPregunta.disabled = notaActual === null;
    }
  }

  // --- 9. Arranque -------------------------------------------------------------
  dom.botonPregunta.addEventListener("click", preguntar);
  dom.botonResumen.addEventListener("click", prepararResumen);
  dom.pedido.addEventListener("input", actualizarContador);

  $("fecha-hoy").textContent = new Date().toLocaleDateString("es-AR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  actualizarContador();
  cargarPreferencias();
  cargarGustos();
  cargarIndicadores();
  cargarNoticias();
  cargarResumen();
  comprobarClaude();
  retomarResumen();
})();
