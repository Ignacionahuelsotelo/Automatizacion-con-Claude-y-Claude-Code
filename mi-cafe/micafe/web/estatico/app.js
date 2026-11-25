/*
 * Mi Café, front. Un solo archivo (sin módulos ni build), ordenado en secciones:
 *   1. Referencias al DOM y estado
 *   2. API (único punto de `fetch`)
 *   3. Gustos 👍/👎
 *   4. Preferencias (vista #preferencias dentro de la misma página: temas, subtemas, medios,
 *      indicadores, palabras, "Lo que aprendí de tus 👍/👎" y navegación)
 *   5. Indicadores
 *   6. Noticias de ayer (con etiquetas)
 *   7. Resumen (con "Cómo se armó hoy" y el aviso de pedido sin notas)
 *   8. Caja de preguntas
 *   9. Arranque
 *
 * Contrato de la API que usa el front (todo JSON; los errores traen `errores`: lista de frases en español):
 *   GET  /api/preferencias  -> {preferencias:{version:2,temas:{tema:{activo,prioridad}},subtemas,medios:{preferidos,excluidos},palabras:{seguir,evitar},indicadores},
 *                              opciones:{indicadores:{clave:texto}, secciones, subtemas, medios, prioridades, maximo_palabras, maximo_caracteres}, aviso?}
 *                              (`secciones`: lista de secciones del resumen, de config.TEMAS; el front no la copia)
 *   POST /api/preferencias  {v2 completo; la pantalla manda siempre el v2 entero} -> {ok, preferencias} | 400 {ok:false, errores}
 *   GET  /api/gustos        -> {votos:[{tipo,clave,voto}], aviso?}
 *   POST /api/gustos        {tipo,clave,voto|null,titulo?,medio?,seccion?} -> {ok, votos} | 400 {errores}
 *   GET  /api/indicadores   -> {indicadores:[{nombre,valor,fecha,fuente,desactualizado}], avisos:[texto]}
 *   GET  /api/noticias      -> {notas:[{titulo,link,medio,seccion,fecha,motivos:[texto]}], fallas:[{medio,seccion,motivo}]}
 *                              (las notas vienen en el orden del servidor, por puntaje; `motivos` da las etiquetas)
 *   GET  /api/perfil        -> {ok, prioridades:[{tipo:seccion|medio|termino,nombre,signo:1|-1,etiqueta}], reiniciado_en, votos_que_cuentan}
 *   POST /api/perfil/reiniciar {confirmar:true} -> {ok, ...perfil} | 400 {ok:false, errores}
 *   GET  /api/claude        -> {disponible, estado:ok|no_instalado|no_responde|con_error, mensaje} (siempre 200)
 *   GET  /api/resumen       -> {resumen: null | {fecha,generado_en,texto,indicadores,chequeo:{aprobado,no_cumple},
 *                                pedido? (texto que la persona pidió ese día), pedido_sin_notas? (bool),
 *                                plan? {secciones:[{seccion,cupo,pedidas,motivos}], completo} (ausente en resúmenes viejos),
 *                                temas_destildados_pedido? (temas que el pedido nombra y hoy están destildados),
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

  // Las secciones llegan del servidor en `opciones.secciones` (spec 42); acá no se copia la lista.
  let secciones = null;
  const APERTURAS = ["Lo más importante de hoy:", "Lo que viene hoy:"];

  const dom = {
    avisoPrefs: $("aviso"),
    estadoPrefs: $("estado"),
    resumenPrefs: $("resumen-prefs"),
    vistaResumen: $("vista-resumen"),
    vistaPreferencias: $("preferencias"),
    tituloPreferencias: $("titulo-preferencias"),
    estadoCargaPrefs: $("estado-carga-prefs"),
    avisoCambios: $("aviso-cambios"),
    prefTemas: $("pref-temas"),
    prefSubtemasBloque: $("pref-subtemas-bloque"),
    prefSubtemas: $("pref-subtemas"),
    prefMediosPreferidos: $("pref-medios-preferidos"),
    prefMediosExcluidos: $("pref-medios-excluidos"),
    estadoMedios: $("estado-medios"),
    prefIndicadores: $("pref-indicadores"),
    prefPalabras: $("pref-palabras"),
    botonGuardar: $("guardar-prefs"),
    avisoTemas: $("aviso-temas"),
    estadoGuardado: $("estado-guardado"),
    erroresPrefs: $("errores-prefs"),
    perfilContenido: $("perfil-contenido"),
    estadoReinicioVista: $("estado-reinicio-vista"),
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
    avisoPedido: $("aviso-pedido"),
    comoSeArmo: $("como-se-armo"),
    comoSeArmoContenido: $("como-se-armo-contenido"),
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

  // --- 4. Preferencias (vista #preferencias, spec 50) ---------------------------
  // Todo lo que se puede elegir (temas, subtemas, medios, indicadores, prioridades y topes) llega en
  // `opciones`; acá no se copia ninguna lista. Lo único fijo es que los subtemas son los de Deportes.
  const TEMA_DE_LOS_SUBTEMAS = "Deportes";

  let opciones = null; // las opciones del servidor
  let prefsGuardadas = null; // las últimas preferencias v2 del servidor
  let borrador = null; // lo que la persona está editando (v2 completo)
  let vistaAbierta = false;
  let origenDelFoco = null;
  let temaAEnfocar = null;
  const interruptores = new Map(); // tema -> {casilla, selector, estado}
  const casillasMedios = { preferidos: new Map(), excluidos: new Map() };

  function copiar(valor) {
    return JSON.parse(JSON.stringify(valor));
  }

  // Firma para comparar sin que importe el orden de las listas que el servidor ordena.
  function firma(prefs) {
    const ordenada = copiar(prefs);
    ordenada.subtemas.sort();
    ordenada.medios.preferidos.sort();
    ordenada.medios.excluidos.sort();
    ordenada.indicadores.sort();
    return JSON.stringify(ordenada);
  }

  function hayCambios() {
    return Boolean(borrador && prefsGuardadas && firma(borrador) !== firma(prefsGuardadas));
  }

  function hizoCambio() {
    dom.estadoGuardado.textContent = "";
    dom.erroresPrefs.hidden = true;
    dom.erroresPrefs.replaceChildren();
    avisarSinTemas();
  }

  function temasActivos() {
    return opciones.secciones.filter((tema) => borrador.temas[tema] && borrador.temas[tema].activo);
  }

  function avisarSinTemas() {
    dom.avisoTemas.textContent = temasActivos().length ? "" : "Elegí al menos un tema.";
  }

  function mayuscula(texto) {
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  function crearSoloLector(texto, para) {
    const etiqueta = document.createElement("label");
    etiqueta.className = "solo-lector";
    etiqueta.htmlFor = para;
    etiqueta.textContent = texto;
    return etiqueta;
  }

  // Una casilla con su etiqueta visible. `alCambiar(marcada)` recibe el estado nuevo.
  function crearCasilla(id, texto, marcada, alCambiar) {
    const etiqueta = document.createElement("label");
    etiqueta.className = "casilla";
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.id = id;
    casilla.checked = marcada;
    casilla.addEventListener("change", () => alCambiar(casilla.checked));
    const rotulo = document.createElement("span");
    rotulo.textContent = texto;
    etiqueta.append(casilla, rotulo);
    return { etiqueta, casilla };
  }

  function textoDelInterruptor(activo) {
    return activo ? "Activo" : "Apagado";
  }

  function dibujarTemas() {
    interruptores.clear();
    dom.prefTemas.replaceChildren(...opciones.secciones.map((tema, indice) => {
      const datos = borrador.temas[tema] || { activo: false, prioridad: "normal" };
      const fila = document.createElement("div");
      fila.className = "fila-tema";
      const { etiqueta, casilla } = crearCasilla(`tema-activo-${indice}`, tema, datos.activo, (marcada) => {
        borrador.temas[tema].activo = marcada;
        selector.disabled = !marcada;
        estado.textContent = textoDelInterruptor(marcada);
        if (tema === TEMA_DE_LOS_SUBTEMAS) dom.prefSubtemasBloque.hidden = !marcada;
        hizoCambio();
      });
      casilla.setAttribute("role", "switch");
      const estado = document.createElement("span");
      estado.className = "estado-tema";
      estado.textContent = textoDelInterruptor(datos.activo);

      const selector = document.createElement("select");
      selector.id = `tema-prioridad-${indice}`;
      opciones.prioridades.forEach((prioridad) => {
        const opcion = document.createElement("option");
        opcion.value = prioridad;
        opcion.textContent = mayuscula(prioridad);
        selector.appendChild(opcion);
      });
      selector.value = datos.prioridad;
      selector.disabled = !datos.activo;
      selector.addEventListener("change", () => {
        borrador.temas[tema].prioridad = selector.value;
        hizoCambio();
      });
      const grupoPrioridad = document.createElement("span");
      grupoPrioridad.className = "prioridad";
      grupoPrioridad.append(crearSoloLector(`Prioridad de ${tema}`, selector.id), selector);

      fila.append(etiqueta, estado, grupoPrioridad, crearBotonesVoto("tema", tema, undefined, `tema ${tema}`, dom.estadoPrefs));
      interruptores.set(tema, { casilla, selector, estado });
      return fila;
    }));
    const deportes = borrador.temas[TEMA_DE_LOS_SUBTEMAS];
    dom.prefSubtemasBloque.hidden = !(deportes && deportes.activo);
    pintarVotos();
  }

  // Marca o desmarca un valor en una lista del borrador manteniendo el orden de `todas`.
  function fijarEnLista(lista, todas, valor, presente) {
    const conjunto = new Set(lista);
    if (presente) conjunto.add(valor); else conjunto.delete(valor);
    return todas.filter((x) => conjunto.has(x));
  }

  function dibujarSubtemas() {
    dom.prefSubtemas.replaceChildren(...opciones.subtemas.map((subtema, indice) =>
      crearCasilla(`subtema-${indice}`, subtema, borrador.subtemas.includes(subtema), (marcada) => {
        borrador.subtemas = fijarEnLista(borrador.subtemas, opciones.subtemas, subtema, marcada);
        hizoCambio();
      }).etiqueta));
  }

  function dibujarMedios() {
    casillasMedios.preferidos.clear();
    casillasMedios.excluidos.clear();
    const lista = (clave, otra, contenedor, avisoAlPasar) => {
      contenedor.replaceChildren(...opciones.medios.map((medio, indice) => {
        const { etiqueta, casilla } = crearCasilla(`medio-${clave}-${indice}`, medio, borrador.medios[clave].includes(medio), (marcada) => {
          borrador.medios[clave] = fijarEnLista(borrador.medios[clave], opciones.medios, medio, marcada);
          dom.estadoMedios.textContent = "";
          if (marcada && borrador.medios[otra].includes(medio)) {
            borrador.medios[otra] = fijarEnLista(borrador.medios[otra], opciones.medios, medio, false);
            casillasMedios[otra].get(medio).checked = false;
            dom.estadoMedios.textContent = avisoAlPasar(medio);
          }
          hizoCambio();
        });
        casillasMedios[clave].set(medio, casilla);
        return etiqueta;
      }));
    };
    lista("preferidos", "excluidos", dom.prefMediosPreferidos,
      (medio) => `${medio} ya no está en los medios que no querés ver.`);
    lista("excluidos", "preferidos", dom.prefMediosExcluidos,
      (medio) => `${medio} ya no está en los medios que preferís.`);
  }

  function dibujarIndicadoresPrefs() {
    dom.prefIndicadores.replaceChildren(...Object.entries(opciones.indicadores).map(([clave, texto], indice) =>
      crearCasilla(`indicador-${indice}`, texto, borrador.indicadores.includes(clave), (marcada) => {
        borrador.indicadores = fijarEnLista(borrador.indicadores, Object.keys(opciones.indicadores), clave, marcada);
        hizoCambio();
      }).etiqueta));
  }

  // Un campo de palabras (seguir o evitar): input + "Agregar", lista con "Quitar" y un aviso propio.
  function crearCampoPalabras(clave, titulo) {
    const grupo = document.createElement("fieldset");
    grupo.className = "campo-palabras";
    const leyenda = document.createElement("legend");
    leyenda.textContent = titulo;
    const entrada = document.createElement("input");
    entrada.type = "text";
    entrada.id = `palabra-${clave}`;
    entrada.autocomplete = "off";
    const agregar = document.createElement("button");
    agregar.type = "button";
    agregar.className = "boton-chico";
    agregar.textContent = "Agregar";
    agregar.setAttribute("aria-label", `Agregar a ${titulo.toLowerCase()}`);
    const aviso = document.createElement("p");
    aviso.className = "estado";
    aviso.setAttribute("role", "status");
    const lista = document.createElement("ul");
    lista.className = "lista-palabras";

    const dibujarLista = () => {
      lista.replaceChildren(...borrador.palabras[clave].map((palabra) => {
        const item = document.createElement("li");
        const texto = document.createElement("span");
        texto.textContent = palabra;
        const quitar = document.createElement("button");
        quitar.type = "button";
        quitar.className = "boton-chico";
        quitar.textContent = "Quitar";
        quitar.setAttribute("aria-label", `Quitar ${palabra}`);
        quitar.addEventListener("click", () => {
          borrador.palabras[clave] = borrador.palabras[clave].filter((otra) => otra !== palabra);
          aviso.textContent = "";
          dibujarLista();
          entrada.focus();
          hizoCambio();
        });
        item.append(texto, quitar);
        return item;
      }));
    };
    const agregarPalabra = () => {
      const palabra = entrada.value.trim().replace(/\s+/g, " ");
      const actuales = borrador.palabras[clave];
      if (!palabra) {
        aviso.textContent = "Escribí una palabra.";
      } else if (Array.from(palabra).length > opciones.maximo_caracteres) {
        aviso.textContent = `Cada palabra puede tener hasta ${opciones.maximo_caracteres} caracteres.`;
      } else if (actuales.some((otra) => otra.toLowerCase() === palabra.toLowerCase())) {
        aviso.textContent = "Esa palabra ya está en la lista.";
      } else if (actuales.length >= opciones.maximo_palabras) {
        aviso.textContent = `Podés tener hasta ${opciones.maximo_palabras} palabras en esta lista.`;
      } else {
        actuales.push(palabra);
        entrada.value = "";
        aviso.textContent = "";
        dibujarLista();
        hizoCambio();
      }
      entrada.focus();
    };
    agregar.addEventListener("click", agregarPalabra);
    entrada.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") {
        evento.preventDefault();
        agregarPalabra();
      }
    });
    const fila = document.createElement("div");
    fila.className = "fila-palabra";
    fila.append(crearSoloLector(`Palabra para: ${titulo}`, entrada.id), entrada, agregar);
    grupo.append(leyenda, fila, aviso, lista);
    dibujarLista();
    return grupo;
  }

  function dibujarPalabras() {
    dom.prefPalabras.replaceChildren(
      crearCampoPalabras("seguir", "Palabras que quiero seguir"),
      crearCampoPalabras("evitar", "Palabras que quiero evitar"));
  }

  // Una línea en la vista principal: temas e indicadores elegidos (solo nombres, sin números).
  function dibujarResumenPrefs() {
    const temas = opciones.secciones.filter((tema) => prefsGuardadas.temas[tema] && prefsGuardadas.temas[tema].activo);
    const indicadores = Object.entries(opciones.indicadores)
      .filter(([clave]) => prefsGuardadas.indicadores.includes(clave)).map(([, texto]) => texto);
    dom.resumenPrefs.textContent = `Temas: ${temas.join(", ") || "ninguno"} · Indicadores: ${indicadores.join(", ") || "ninguno"}`;
  }

  function dibujarVista() {
    dibujarTemas();
    dibujarSubtemas();
    dibujarMedios();
    dibujarIndicadoresPrefs();
    dibujarPalabras();
    avisarSinTemas();
  }

  function dibujarPreferencias(datos) {
    opciones = datos.opciones;
    prefsGuardadas = datos.preferencias;
    borrador = copiar(prefsGuardadas);
    dibujarVista();
    dibujarResumenPrefs();
  }

  async function cargarPreferencias() {
    const r = await api("/api/preferencias");
    if (!r.ok) {
      dom.estadoCargaPrefs.textContent = "No se pudieron cargar las preferencias.";
      dom.resumenPrefs.textContent = "No se pudieron cargar las preferencias.";
      return;
    }
    dibujarPreferencias(r.datos);
    const lista = r.datos.opciones.secciones;
    secciones = Array.isArray(lista) && lista.length ? lista : null;
    dom.avisoPrefs.textContent = r.datos.aviso || "";
    dom.avisoPrefs.hidden = !r.datos.aviso;
  }

  // Devuelve true si se guardó. Los errores del servidor se muestran sin tocar lo escrito.
  async function guardarPreferencias() {
    if (!borrador) return false;
    dom.botonGuardar.disabled = true;
    dom.botonGuardar.setAttribute("aria-busy", "true");
    dom.estadoGuardado.textContent = "Guardando…";
    dom.erroresPrefs.hidden = true;
    const r = await api("/api/preferencias", { metodo: "POST", cuerpo: borrador });
    dom.botonGuardar.disabled = false;
    dom.botonGuardar.removeAttribute("aria-busy");
    if (!r.ok) {
      dom.estadoGuardado.textContent = "";
      dom.erroresPrefs.replaceChildren(...[r.red ? r.errores[0] : "No se guardó:", ...(r.red ? [] : r.errores)]
        .map((linea) => crearParrafo(linea)));
      dom.erroresPrefs.hidden = false;
      return false;
    }
    prefsGuardadas = r.datos.preferencias || copiar(borrador);
    borrador = copiar(prefsGuardadas);
    dibujarVista();
    dibujarResumenPrefs();
    dom.avisoPrefs.hidden = true;
    dom.estadoGuardado.textContent = "Guardado.";
    cargarIndicadores();
    cargarNoticias();
    return true;
  }

  // --- 4b. Lo que aprendí de tus 👍/👎 ------------------------------------------
  function fechaDeReinicio(texto) {
    const coincide = /^(\d{4})-(\d{2})-(\d{2})/.exec(texto || "");
    return coincide ? `${coincide[3]}/${coincide[2]}/${coincide[1]}` : texto;
  }

  async function cargarPerfilVista() {
    const r = await api("/api/perfil");
    if (!r.ok || !r.datos || !Array.isArray(r.datos.prioridades)) {
      dom.perfilContenido.replaceChildren(crearParrafo("No se pudo cargar lo que aprendí."));
      return;
    }
    const partes = [];
    if (r.datos.prioridades.length) {
      const lista = document.createElement("ul");
      r.datos.prioridades.forEach((prioridad) => {
        const item = document.createElement("li");
        item.textContent = prioridad.etiqueta;
        lista.appendChild(item);
      });
      partes.push(lista);
    } else {
      partes.push(crearParrafo("Todavía no aprendí nada de tus 👍/👎."));
    }
    partes.push(crearParrafo(`Votos que cuentan: ${r.datos.votos_que_cuentan}.`));
    if (r.datos.reiniciado_en) {
      partes.push(crearParrafo(`Último reinicio: ${fechaDeReinicio(r.datos.reiniciado_en)}.`));
    }
    dom.perfilContenido.replaceChildren(...partes);
  }

  async function reiniciarDesdeVista() {
    if (!window.confirm("¿Querés que Mi Café ignore lo aprendido de tus votos hasta ahora? Los votos no se borran.")) return;
    const r = await api("/api/perfil/reiniciar", { metodo: "POST", cuerpo: { confirmar: true } });
    dom.estadoReinicioVista.textContent = r.ok
      ? "Listo: se ignora lo aprendido hasta ahora."
      : "No se pudo reiniciar: " + r.errores.join(" ");
    if (r.ok) await cargarPerfilVista();
  }

  // --- 4c. Navegación entre la vista del resumen y la de Preferencias -------------
  async function aplicarVista() {
    const enPreferencias = location.hash === "#preferencias";
    dom.vistaResumen.hidden = enPreferencias;
    dom.vistaPreferencias.hidden = !enPreferencias;
    dom.avisoCambios.hidden = true;
    if (enPreferencias === vistaAbierta) return;
    vistaAbierta = enPreferencias;
    if (enPreferencias) {
      cargarPerfilVista();
      dom.estadoReinicioVista.textContent = "";
      await preferenciasListas;
      const destino = temaAEnfocar && interruptores.get(temaAEnfocar);
      temaAEnfocar = null;
      (destino ? destino.casilla : dom.tituloPreferencias).focus();
    } else {
      const origen = origenDelFoco && !origenDelFoco.hidden && document.contains(origenDelFoco) ? origenDelFoco : $("abrir-preferencias");
      origenDelFoco = null;
      origen.focus();
    }
  }

  // Salir con cambios sin guardar: se vuelve a la vista y se avisa (sin `beforeunload`).
  function alCambiarElHash() {
    if (vistaAbierta && location.hash !== "#preferencias" && hayCambios()) {
      history.replaceState(null, "", "#preferencias");
      dom.avisoCambios.hidden = false;
      $("cambios-guardar").focus();
      return;
    }
    aplicarVista();
  }

  // Si hay cambios sin guardar, el cambio de hash lo frena `alCambiarElHash` y muestra el aviso.
  function salirDeLaVista() {
    if (location.hash === "#preferencias") location.hash = "";
    else aplicarVista();
  }

  function irAPreferencias(tema) {
    temaAEnfocar = tema || null;
    origenDelFoco = document.activeElement;
    if (location.hash === "#preferencias") aplicarVista(); else location.hash = "#preferencias";
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

  // Etiquetas visibles (texto, no solo color) que salen de los `motivos` que calculó el servidor.
  function etiquetasDeMotivos(motivos) {
    const etiquetas = [];
    (motivos || []).forEach((motivo) => {
      let texto = null;
      if (motivo.startsWith("pedido:")) texto = "Por tu pedido";
      else if (motivo === "medio que te gusta") texto = "Medio que te gusta";
      else if (motivo === "te gustó algo parecido") texto = "Tema que te gusta";
      else if (motivo === "medio preferido") texto = "Medio preferido";
      else if (motivo === "palabra a seguir") texto = "Palabra que seguís";
      else if (motivo === "palabra a evitar") texto = "Palabra que evitás";
      else if (motivo === "subtema elegido") texto = "Subtema que elegiste";
      else if (motivo === "subtema no elegido") texto = "Subtema que no elegiste";
      if (texto && !etiquetas.includes(texto)) etiquetas.push(texto);
    });
    return etiquetas;
  }

  function dibujarNoticia(nota) {
    const elemento = document.createElement("li");
    elemento.appendChild(crearEnlaceExterno(nota.link, nota.titulo));
    const etiquetas = etiquetasDeMotivos(nota.motivos);
    if (etiquetas.length) {
      const lista = document.createElement("span");
      lista.className = "etiquetas";
      etiquetas.forEach((texto) => {
        const etiqueta = document.createElement("span");
        etiqueta.className = "etiqueta";
        etiqueta.textContent = texto;
        lista.appendChild(etiqueta);
      });
      elemento.appendChild(lista);
    }

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
        if (secciones.includes(linea)) {
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
    dom.avisoPedido.hidden = true;
    dom.avisoPedido.replaceChildren();
    dom.comoSeArmo.hidden = true;
    dom.comoSeArmo.open = false;
    dom.comoSeArmoContenido.replaceChildren();
    dom.avisoCorrector.hidden = true;
    dom.avisoCorrector.textContent = "";
    dom.cabeceraResumen.hidden = true;
    dom.cabeceraResumen.textContent = "";
    dom.contenidoResumen.replaceChildren();
    dom.estadoVotoResumen.textContent = "";
    ocultarCaja();
  }

  function textoNotas(cantidad) {
    return cantidad === 1 ? "1 nota" : `${cantidad} notas`;
  }

  // Aviso "Tu pedido no encontró notas de ayer" (solo cuando el servidor lo marca).
  function mostrarAvisoPedido(resumen) {
    if (resumen.pedido_sin_notas !== true) return;
    const destildados = Array.isArray(resumen.temas_destildados_pedido) ? resumen.temas_destildados_pedido : [];
    const partes = [document.createTextNode("Tu pedido no encontró notas de ayer.")];
    if (destildados.length) {
      partes.push(document.createTextNode(" Ese tema está destildado en tus preferencias. "));
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "boton-chico";
      boton.textContent = "Ir a preferencias";
      boton.addEventListener("click", () => irAPreferencias(destildados[0]));
      partes.push(boton);
    }
    dom.avisoPedido.replaceChildren(...partes);
    dom.avisoPedido.hidden = false;
  }

  // Los ajustes por gustos salen de /api/perfil: secciones y medios que suben o bajan por los votos.
  async function agregarAjustesDeGustos(contenedor) {
    const r = await api("/api/perfil");
    if (!r.ok || !r.datos || !Array.isArray(r.datos.prioridades)) return;
    const nombres = (signo) => r.datos.prioridades
      .filter((p) => p.signo === signo && p.tipo !== "termino")
      .map((p) => (p.tipo === "medio" ? `el medio ${p.nombre}` : p.nombre));
    const suben = nombres(1);
    const bajan = nombres(-1);
    if (suben.length) contenedor.appendChild(crearParrafo(`Subieron por tus votos: ${suben.join(", ")}.`));
    if (bajan.length) contenedor.appendChild(crearParrafo(`Bajaron por tus votos: ${bajan.join(", ")}.`));
    const reiniciar = document.createElement("button");
    reiniciar.type = "button";
    reiniciar.className = "boton-chico";
    reiniciar.textContent = "Reiniciar lo aprendido";
    const estado = document.createElement("span");
    estado.className = "estado-reinicio";
    estado.setAttribute("role", "status");
    reiniciar.addEventListener("click", async () => {
      if (!window.confirm("¿Querés que Mi Café ignore lo aprendido de tus votos hasta ahora? Los votos no se borran.")) return;
      const respuesta = await api("/api/perfil/reiniciar", { metodo: "POST", cuerpo: { confirmar: true } });
      estado.textContent = respuesta.ok
        ? "Listo: se ignora lo aprendido hasta ahora."
        : "No se pudo reiniciar: " + respuesta.errores.join(" ");
    });
    contenedor.append(reiniciar, estado);
  }

  // Bloque plegable "Cómo se armó hoy". Un resumen viejo, sin `plan`, no lo muestra.
  // Solo cantidades de notas: nunca valores de indicadores.
  function mostrarComoSeArmo(resumen) {
    const plan = resumen.plan;
    if (!plan || !Array.isArray(plan.secciones) || !plan.secciones.length) return;
    const contenido = dom.comoSeArmoContenido;
    const lista = document.createElement("ul");
    let total = 0;
    plan.secciones.forEach((cupo) => {
      total += cupo.cupo;
      const item = document.createElement("li");
      item.textContent = `${cupo.seccion}: ${textoNotas(cupo.cupo)}`;
      lista.appendChild(item);
    });
    contenido.appendChild(crearParrafo(`Notas por sección (${textoNotas(total)} en total):`));
    contenido.appendChild(lista);
    if (plan.completo === false) {
      contenido.appendChild(crearParrafo("El plan quedó incompleto: hoy no había notas suficientes para llegar a la cantidad buscada."));
    }
    if (resumen.pedido) {
      const encajaron = plan.secciones.reduce((suma, cupo) => suma + (cupo.pedidas || 0), 0);
      contenido.appendChild(crearParrafo(resumen.pedido_sin_notas === true
        ? "Con tu pedido no encajó ninguna nota."
        : `Con tu pedido encajaron ${textoNotas(encajaron)} entre las candidatas.`));
    }
    dom.comoSeArmo.hidden = false;
    agregarAjustesDeGustos(contenido);
  }

  function mostrarResumen(resumen) {
    limpiarResumen();
    if (secciones === null) {
      dom.estadoResumen.textContent = "No se pudo cargar la lista de secciones. Recargá la página.";
      return;
    }
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
    mostrarAvisoPedido(resumen);
    mostrarComoSeArmo(resumen);

    if (resumen.chequeo && !resumen.chequeo.aprobado) {
      dom.avisoCorrector.textContent = "Aviso del corrector: el resumen no cumple estas reglas: "
        + (resumen.chequeo.no_cumple || []).join(" ");
      dom.avisoCorrector.hidden = false;
    }
    dom.contenidoResumen.replaceChildren(...elementosDelResumen(resumen.texto, resumen.fecha, resumen.notas));
    pintarVotos();
  }

  async function cargarResumen() {
    await preferenciasListas; // la lista de secciones sale de ahí
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
      await preferenciasListas;
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
  dom.botonGuardar.addEventListener("click", guardarPreferencias);
  $("reiniciar-aprendido").addEventListener("click", reiniciarDesdeVista);
  $("volver-resumen").addEventListener("click", salirDeLaVista);
  $("cambios-seguir").addEventListener("click", () => {
    dom.avisoCambios.hidden = true;
    dom.tituloPreferencias.focus();
  });
  $("cambios-descartar").addEventListener("click", () => {
    borrador = copiar(prefsGuardadas);
    dibujarVista();
    hizoCambio();
    salirDeLaVista();
  });
  $("cambios-guardar").addEventListener("click", async () => {
    if (await guardarPreferencias()) salirDeLaVista();
    else dom.avisoCambios.hidden = true;
  });
  document.querySelectorAll('a[href="#preferencias"]').forEach((enlace) => {
    enlace.addEventListener("click", () => { origenDelFoco = enlace; });
  });
  window.addEventListener("hashchange", alCambiarElHash);

  $("fecha-hoy").textContent = new Date().toLocaleDateString("es-AR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  actualizarContador();
  const preferenciasListas = cargarPreferencias();
  aplicarVista();
  cargarGustos();
  cargarIndicadores();
  cargarNoticias();
  cargarResumen();
  comprobarClaude();
  retomarResumen();
})();
