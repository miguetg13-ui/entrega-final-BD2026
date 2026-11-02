// Vista "Foro": la portada (vista vw_resumen_preguntas) y el detalle de una pregunta,
// donde se ve la lógica del motor: votar (sp_votar_pregunta + trigger de voto propio),
// puntaje (fn_puntaje_pregunta), respuestas (trigger de comentario padre) y última actividad.

async function vistaForo() {
  const contenido = document.getElementById("contenido");
  contenido.innerHTML = `<h2>Preguntas recientes</h2><div id="lista-foro">Cargando…</div>`;
  try {
    const preguntas = await api("GET", "/preguntas/resumen");
    document.getElementById("lista-foro").innerHTML = preguntas.length === 0
      ? `<p class="vacio">Todavía no hay preguntas.</p>`
      : preguntas.map(p => `
        <article class="tarjeta pregunta" data-id="${p.id_pregunta}">
          <div class="puntaje ${p.puntaje < 0 ? "negativo" : ""}">${p.puntaje}<small>puntos</small></div>
          <div>
            <h3>${esc(p.titulo)}</h3>
            <p class="meta">${esc(p.tema)} · por ${esc(p.autor)} · ${p.num_comentarios} comentario(s)
              · última actividad ${fecha(p.ultima_actividad)}</p>
            ${p.etiquetas ? p.etiquetas.split(", ").map(e => `<span class="chip">${esc(e)}</span>`).join("") : ""}
          </div>
        </article>`).join("");
    document.querySelectorAll(".pregunta").forEach(a => (a.onclick = () => vistaPregunta(a.dataset.id)));
  } catch (e) {
    document.getElementById("lista-foro").innerHTML = `<p class="vacio">No se pudo cargar el foro.</p>`;
    avisarError(e);
  }
}

// Ordena los comentarios como conversación: cada respuesta justo debajo del comentario al que responde
function enArbol(comentarios) {
  const hijos = {};
  comentarios.forEach(c => (hijos[c.id_comentario_padre ?? 0] ||= []).push(c));
  const orden = [];
  const visitar = id => (hijos[id] || []).forEach(c => {
    orden.push(c);
    visitar(c.id_comentario);
  });
  visitar(0);
  return orden;
}

async function vistaPregunta(id, respondiendoA = null) {
  const contenido = document.getElementById("contenido");
  let p;
  try {
    [p] = await Promise.all([api("GET", `/preguntas/${id}`), cargarCatalogos(["usuarios"])]);
  } catch (e) {
    avisarError(e);
    return vistaForo();
  }
  const opcionesUsuario = catalogos.usuarios.map(u => `<option value="${u.valor}">${esc(u.texto)}</option>`).join("");
  const padre = p.comentarios.find(c => String(c.id_comentario) === String(respondiendoA));

  contenido.innerHTML = `
    <button type="button" id="volver">← Volver al foro</button>
    <article class="tarjeta detalle">
      <div class="puntaje grande ${p.puntaje < 0 ? "negativo" : ""}">${p.puntaje}<small>puntos</small></div>
      <div>
        <h2>${esc(p.titulo)}</h2>
        <p class="meta">${esc(p.tema)} · por ${esc(p.autor)} · publicada ${fecha(p.fecha_publicacion)}
          · <strong>última actividad ${fecha(p.ultima_actividad)}</strong></p>
        <p>${esc(p.contenido)}</p>
        ${p.etiquetas.map(e => `<span class="chip">${esc(e.nombre)}</span>`).join("")}
        <form id="votar" class="en-linea">
          <label>Votar como <select name="usuario"><option value="">Elige usuario</option>${opcionesUsuario}</select></label>
          <button type="submit" value="1">👍 A favor</button>
          <button type="submit" value="-1">👎 En contra</button>
        </form>
      </div>
    </article>

    <h3>Comentarios (${p.comentarios.length})</h3>
    <div id="comentarios">${p.comentarios.length === 0 ? `<p class="vacio">Nadie ha respondido todavía.</p>` :
      enArbol(p.comentarios).map(c => `
        <div class="tarjeta comentario" style="margin-left:${c.profundidad * 2}rem">
          <p class="meta">#${c.id_comentario} · ${esc(c.autor)} · ${fecha(c.fecha_publicacion)} ·
            ${c.puntaje} punto(s) · nivel ${c.profundidad}
            ${c.id_comentario_padre ? `· responde a #${c.id_comentario_padre}` : ""}</p>
          <p>${esc(c.contenido)}</p>
          <button type="button" data-responder="${c.id_comentario}">Responder</button>
        </div>`).join("")}
    </div>

    <form id="comentar" class="tarjeta" novalidate>
      <h3>${padre ? `Respondiendo a #${padre.id_comentario} de ${esc(padre.autor)}
        <button type="button" id="no-responder">Cancelar respuesta</button>` : "Agregar un comentario"}</h3>
      <div class="campo" data-campo="id_usuario"><label>Autor</label>
        <select name="usuario"><option value="">Elige usuario</option>${opcionesUsuario}</select></div>
      <div class="campo" data-campo="contenido"><label>Comentario</label><textarea name="contenido" rows="3"></textarea></div>
      <button type="submit" class="principal">Publicar</button>
    </form>`;

  document.getElementById("volver").onclick = vistaForo;
  document.querySelectorAll("[data-responder]").forEach(b =>
    (b.onclick = () => vistaPregunta(id, b.dataset.responder).then(() =>
      document.getElementById("comentar").scrollIntoView({ behavior: "smooth" }))));
  document.getElementById("no-responder")?.addEventListener("click", () => vistaPregunta(id));

  const votar = document.getElementById("votar");
  votar.onsubmit = async evento => {
    evento.preventDefault();
    const usuario = votar.elements.usuario.value;
    if (!usuario) return avisar("Elige con qué usuario vas a votar.", "error");
    try {
      const r = await api("POST", `/preguntas/${id}/votos`,
        { id_usuario: Number(usuario), valor: Number(evento.submitter.value) });
      avisar(`Voto registrado. La pregunta ahora tiene ${r.puntaje} punto(s).`);
      await vistaPregunta(id);
    } catch (e) {
      avisarError(e);
    }
  };

  const comentar = document.getElementById("comentar");
  comentar.onsubmit = async evento => {
    evento.preventDefault();
    comentar.querySelectorAll(".invalido").forEach(el => el.classList.remove("invalido"));
    const usuario = comentar.elements.usuario.value;
    try {
      await api("POST", "/comentarios", {
        id_usuario: usuario ? Number(usuario) : null,
        id_pregunta: Number(id),
        id_comentario_padre: padre ? padre.id_comentario : null,
        contenido: comentar.elements.contenido.value.trim(),
      });
      avisar("Comentario publicado. La última actividad de la pregunta se actualizó.");
      await vistaPregunta(id);
    } catch (e) {
      (e.errores || []).forEach(err =>
        comentar.querySelector(`[data-campo="${err.campo}"]`)?.classList.add("invalido"));
      avisarError(e);
    }
  };
}
