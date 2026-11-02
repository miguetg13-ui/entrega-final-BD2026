// Pantallas de CRUD (listar, crear, editar, borrar) para cada tabla, a partir de una configuración.

// De dónde salen las opciones de cada <select>: [ruta de la API, campo id, cómo mostrar cada fila]
const FUENTES = {
  usuarios:    ["/usuarios", "id_usuario", f => f.nombre],
  temas:       ["/temas", "id_tema", f => f.nombre],
  etiquetas:   ["/etiquetas", "id_etiqueta", f => f.nombre],
  preguntas:   ["/preguntas", "id_pregunta", f => `#${f.id_pregunta} ${f.titulo}`],
  comentarios: ["/comentarios", "id_comentario", f => `#${f.id_comentario} ${f.autor}: ${f.contenido.slice(0, 50)}`],
};

const catalogos = {}; // { usuarios: [{valor, texto}], ... } cargados desde la API

async function cargarCatalogos(nombres) {
  await Promise.all(nombres.map(async nombre => {
    const [ruta, id, texto] = FUENTES[nombre];
    const filas = await api("GET", ruta);
    catalogos[nombre] = filas.map(f => ({ valor: f[id], texto: texto(f) }));
  }));
}

function textoDe(catalogo, valor) {
  const item = (catalogos[catalogo] || []).find(o => o.valor === valor);
  return item ? item.texto : valor;
}

const ENTIDADES = {
  usuarios: {
    titulo: "Usuarios", singular: "usuario", ruta: "/usuarios", id: "id_usuario", catalogos: [],
    columnas: [
      { c: "id_usuario", t: "ID" }, { c: "nombre", t: "Nombre" }, { c: "email", t: "Email" },
      { c: "fecha_registro", t: "Registro", f: fecha },
    ],
    campos: [
      { n: "nombre", l: "Nombre", tipo: "text" },
      { n: "email", l: "Email", tipo: "text" },
    ],
    extra: fila => `<button type="button" data-perfil="${fila.id_usuario}">Perfil</button>`,
  },
  temas: {
    titulo: "Temas", singular: "tema", ruta: "/temas", id: "id_tema", catalogos: [],
    columnas: [{ c: "id_tema", t: "ID" }, { c: "nombre", t: "Nombre" }, { c: "descripcion", t: "Descripción" }],
    campos: [
      { n: "nombre", l: "Nombre", tipo: "text" },
      { n: "descripcion", l: "Descripción (opcional)", tipo: "textarea", opcional: true },
    ],
  },
  etiquetas: {
    titulo: "Etiquetas", singular: "etiqueta", ruta: "/etiquetas", id: "id_etiqueta", catalogos: [],
    columnas: [{ c: "id_etiqueta", t: "ID" }, { c: "nombre", t: "Nombre" }],
    campos: [{ n: "nombre", l: "Nombre", tipo: "text" }],
  },
  preguntas: {
    titulo: "Preguntas", singular: "pregunta", ruta: "/preguntas", id: "id_pregunta",
    catalogos: ["usuarios", "temas", "etiquetas"],
    columnas: [
      { c: "id_pregunta", t: "ID" }, { c: "titulo", t: "Título" },
      { c: "id_usuario", t: "Autor", f: v => textoDe("usuarios", v) },
      { c: "id_tema", t: "Tema", f: v => textoDe("temas", v) },
      { c: "etiquetas", t: "Etiquetas", f: v => v.map(id => textoDe("etiquetas", id)).join(", ") },
      { c: "fecha_publicacion", t: "Publicada", f: fecha },
    ],
    campos: [
      { n: "id_usuario", l: "Autor", tipo: "select", fuente: "usuarios" },
      { n: "id_tema", l: "Tema", tipo: "select", fuente: "temas" },
      { n: "titulo", l: "Título", tipo: "text" },
      { n: "contenido", l: "Contenido", tipo: "textarea" },
      { n: "etiquetas", l: "Etiquetas", tipo: "checks", fuente: "etiquetas" },
    ],
  },
  comentarios: {
    titulo: "Comentarios", singular: "comentario", ruta: "/comentarios", id: "id_comentario",
    catalogos: ["usuarios", "preguntas", "comentarios"],
    columnas: [
      { c: "id_comentario", t: "ID" }, { c: "pregunta", t: "Pregunta" }, { c: "autor", t: "Autor" },
      { c: "id_comentario_padre", t: "Responde a", f: v => (v ? "#" + v : "—") },
      { c: "contenido", t: "Contenido" }, { c: "fecha_publicacion", t: "Fecha", f: fecha },
    ],
    campos: [
      { n: "id_usuario", l: "Autor", tipo: "select", fuente: "usuarios" },
      { n: "id_pregunta", l: "Pregunta", tipo: "select", fuente: "preguntas" },
      { n: "id_comentario_padre", l: "Responde al comentario (opcional)", tipo: "select",
        fuente: "comentarios", opcional: true },
      { n: "contenido", l: "Contenido", tipo: "textarea" },
    ],
  },
};

async function vistaCrud(nombre) {
  const ent = ENTIDADES[nombre];
  const contenido = document.getElementById("contenido");
  contenido.innerHTML = `
    <h2>${ent.titulo}</h2>
    <div id="perfil" hidden></div>
    <div class="dos-columnas">
      <form id="formulario" class="tarjeta" novalidate></form>
      <div id="tabla" class="tarjeta">Cargando…</div>
    </div>`;
  try {
    await cargarCatalogos(ent.catalogos);
  } catch (e) {
    avisarError(e);
  }
  pintarFormulario(ent, null);
  await pintarTabla(ent);
}

function campoHtml(campo, valor) {
  const id = "campo-" + campo.n;
  if (campo.tipo === "textarea") {
    return `<textarea id="${id}" name="${campo.n}" rows="4">${esc(valor)}</textarea>`;
  }
  if (campo.tipo === "select") {
    const opciones = (catalogos[campo.fuente] || []).map(o =>
      `<option value="${o.valor}" ${o.valor === valor ? "selected" : ""}>${esc(o.texto)}</option>`).join("");
    const vacia = campo.opcional ? "Ninguno" : "Elige una opción";
    return `<select id="${id}" name="${campo.n}"><option value="">${vacia}</option>${opciones}</select>`;
  }
  if (campo.tipo === "checks") {
    const elegidos = valor || [];
    return `<div class="checks" id="${id}">` + (catalogos[campo.fuente] || []).map(o => `
      <label><input type="checkbox" name="${campo.n}" value="${o.valor}"
        ${elegidos.includes(o.valor) ? "checked" : ""}> ${esc(o.texto)}</label>`).join("") + `</div>`;
  }
  return `<input id="${id}" name="${campo.n}" type="text" value="${esc(valor)}">`;
}

function pintarFormulario(ent, fila) {
  const form = document.getElementById("formulario");
  const editando = fila !== null;
  form.innerHTML = `
    <h3>${editando ? `Editar ${ent.singular} #${fila[ent.id]}` : `Nuevo ${ent.singular}`}</h3>
    ${ent.campos.map(c => `
      <div class="campo" data-campo="${c.n}">
        <label for="campo-${c.n}">${c.l}</label>
        ${campoHtml(c, editando ? fila[c.n] : (c.tipo === "checks" ? [] : ""))}
      </div>`).join("")}
    <div class="botones">
      <button type="submit" class="principal">${editando ? "Guardar cambios" : "Crear"}</button>
      ${editando ? `<button type="button" id="cancelar">Cancelar</button>` : ""}
    </div>`;

  form.onsubmit = async evento => {
    evento.preventDefault();
    form.querySelectorAll(".invalido").forEach(el => el.classList.remove("invalido"));
    const cuerpo = leerFormulario(ent, form);
    try {
      if (editando) {
        await api("PUT", `${ent.ruta}/${fila[ent.id]}`, cuerpo);
        avisar(`${capital(ent.singular)} #${fila[ent.id]} actualizado.`);
      } else {
        const nueva = await api("POST", ent.ruta, cuerpo);
        avisar(`${capital(ent.singular)} #${nueva[ent.id]} creado.`);
      }
      if (ent.catalogos.length) await cargarCatalogos(ent.catalogos);
      pintarFormulario(ent, null);
      await pintarTabla(ent);
    } catch (e) {
      // 422: se marcan en rojo los campos que la API rechazó
      (e.errores || []).forEach(err =>
        form.querySelector(`[data-campo="${err.campo}"]`)?.classList.add("invalido"));
      avisarError(e);
    }
  };
  if (editando) document.getElementById("cancelar").onclick = () => pintarFormulario(ent, null);
}

function leerFormulario(ent, form) {
  const cuerpo = {};
  for (const c of ent.campos) {
    if (c.tipo === "checks") {
      cuerpo[c.n] = [...form.querySelectorAll(`input[name="${c.n}"]:checked`)].map(i => Number(i.value));
    } else if (c.tipo === "select") {
      const v = form.elements[c.n].value;
      cuerpo[c.n] = v === "" ? null : Number(v);
    } else {
      const v = form.elements[c.n].value.trim();
      cuerpo[c.n] = v === "" && c.opcional ? null : v;
    }
  }
  return cuerpo;
}

async function pintarTabla(ent) {
  const tabla = document.getElementById("tabla");
  let filas;
  try {
    filas = await api("GET", ent.ruta);
  } catch (e) {
    tabla.innerHTML = `<p class="vacio">No se pudieron cargar los datos.</p>`;
    return avisarError(e);
  }
  if (filas.length === 0) {
    tabla.innerHTML = `<p class="vacio">Todavía no hay registros.</p>`;
    return;
  }
  tabla.innerHTML = `<table>
    <thead><tr>${ent.columnas.map(c => `<th>${c.t}</th>`).join("")}<th></th></tr></thead>
    <tbody>${filas.map(fila => `
      <tr>
        ${ent.columnas.map(c => `<td>${esc(c.f ? c.f(fila[c.c]) : fila[c.c])}</td>`).join("")}
        <td class="acciones">
          ${ent.extra ? ent.extra(fila) : ""}
          <button type="button" data-editar="${fila[ent.id]}">Editar</button>
          <span class="borrado"><button type="button" class="peligro" data-borrar="${fila[ent.id]}">Borrar</button></span>
        </td>
      </tr>`).join("")}
    </tbody></table>`;

  tabla.querySelectorAll("[data-editar]").forEach(b => (b.onclick = () => {
    const fila = filas.find(f => String(f[ent.id]) === b.dataset.editar);
    pintarFormulario(ent, fila);
    document.getElementById("formulario").scrollIntoView({ behavior: "smooth" });
  }));

  // Borrar pide confirmación en la misma fila
  tabla.querySelectorAll("[data-borrar]").forEach(b => (b.onclick = () => {
    const id = b.dataset.borrar;
    const zona = b.parentElement;
    zona.innerHTML = `¿Borrar? <button type="button" class="peligro" data-si>Sí</button>
                      <button type="button" data-no>No</button>`;
    zona.querySelector("[data-no]").onclick = () => pintarTabla(ent);
    zona.querySelector("[data-si]").onclick = async () => {
      try {
        const r = await api("DELETE", `${ent.ruta}/${id}`);
        avisar(r.mensaje);
        if (ent.catalogos.length) await cargarCatalogos(ent.catalogos);
      } catch (e) {
        avisarError(e);
      }
      await pintarTabla(ent);
    };
  }));

  tabla.querySelectorAll("[data-perfil]").forEach(b => (b.onclick = () => mostrarPerfil(b.dataset.perfil)));
}

// Perfil: reputación y nivel calculados por las funciones fn_reputacion_usuario y fn_nivel_usuario
async function mostrarPerfil(id) {
  const caja = document.getElementById("perfil");
  try {
    const p = await api("GET", `/usuarios/${id}/perfil`);
    caja.innerHTML = `<strong>${esc(p.nombre)}</strong> (${esc(p.email)}) —
      reputación <strong>${p.reputacion}</strong>, nivel <span class="chip">${esc(p.nivel)}</span>,
      ${p.preguntas} pregunta(s), ${p.comentarios} comentario(s).
      <button type="button" id="cerrar-perfil">Cerrar</button>`;
    caja.className = "tarjeta perfil";
    caja.hidden = false;
    document.getElementById("cerrar-perfil").onclick = () => (caja.hidden = true);
  } catch (e) {
    avisarError(e);
  }
}

function capital(texto) {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
