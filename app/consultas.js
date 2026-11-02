// Vista "Consultas": las consultas de negocio (JOIN / GROUP BY) que expone la API.

const CONSULTAS = [
  {
    titulo: "¿Qué temas mueven más el foro?",
    descripcion: "Preguntas y comentarios de cada tema en los últimos días.",
    ruta: "/consultas/actividad-por-tema",
    parametros: [{ n: "dias", l: "Últimos días", valor: 365 }],
    columnas: [["tema", "Tema"], ["preguntas", "Preguntas"], ["comentarios", "Comentarios"]],
  },
  {
    titulo: "¿Quién hace las mejores preguntas?",
    descripcion: "Usuarios con más votos a favor en sus preguntas.",
    ruta: "/consultas/usuarios-mas-votados",
    parametros: [{ n: "minimo", l: "Mínimo de votos", valor: 1 }],
    columnas: [["nombre", "Usuario"], ["votos_a_favor", "Votos a favor"]],
  },
  {
    titulo: "¿De qué se pide más ayuda en un tema?",
    descripcion: "Etiquetas más usadas en las preguntas del tema elegido.",
    ruta: "/consultas/etiquetas-por-tema",
    parametros: [{ n: "id_tema", l: "Tema", fuente: "temas" }],
    columnas: [["etiqueta", "Etiqueta"], ["preguntas", "Preguntas"]],
  },
  {
    titulo: "¿A quién le falta ayuda?",
    descripcion: "Preguntas con menos comentarios que el máximo indicado.",
    ruta: "/consultas/preguntas-sin-ayuda",
    parametros: [{ n: "max_comentarios", l: "Menos de … comentarios", valor: 2 }],
    columnas: [["id_pregunta", "ID"], ["titulo", "Pregunta"], ["autor", "Autor"], ["comentarios", "Comentarios"]],
  },
  {
    titulo: "Conversaciones de dos niveles",
    descripcion: "Respuestas a respuestas: quién respondió a quién (self-join sobre comentario).",
    ruta: "/consultas/hilos",
    parametros: [],
    columnas: [["quien_responde", "Responde"], ["respuesta", "Respuesta"], ["autor_respondido", "A quién"],
               ["autor_original", "Inició el hilo"], ["original", "Comentario original"]],
  },
];

async function vistaConsultas() {
  const contenido = document.getElementById("contenido");
  try {
    await cargarCatalogos(["temas"]);
  } catch (e) {
    avisarError(e);
  }
  contenido.innerHTML = `<h2>Consultas de negocio</h2>` + CONSULTAS.map((q, i) => `
    <section class="tarjeta consulta">
      <h3>${q.titulo}</h3>
      <p class="meta">${q.descripcion}</p>
      <form class="en-linea" data-consulta="${i}" novalidate>
        ${q.parametros.map(p => `<label>${p.l} ${p.fuente
          ? `<select name="${p.n}">${(catalogos[p.fuente] || []).map(o =>
              `<option value="${o.valor}">${esc(o.texto)}</option>`).join("")}</select>`
          : `<input name="${p.n}" type="number" value="${p.valor}">`}</label>`).join("")}
        <button type="submit" class="principal">Consultar</button>
      </form>
      <div class="resultado"></div>
    </section>`).join("");

  document.querySelectorAll("[data-consulta]").forEach(form => {
    form.onsubmit = evento => {
      evento.preventDefault();
      ejecutarConsulta(form);
    };
    ejecutarConsulta(form);
  });
}

async function ejecutarConsulta(form) {
  const q = CONSULTAS[form.dataset.consulta];
  const caja = form.nextElementSibling;
  const parametros = new URLSearchParams();
  q.parametros.forEach(p => parametros.set(p.n, form.elements[p.n].value));
  try {
    const filas = await api("GET", q.ruta + (q.parametros.length ? "?" + parametros : ""));
    caja.innerHTML = filas.length === 0 ? `<p class="vacio">La consulta no devolvió resultados.</p>` : `
      <table><thead><tr>${q.columnas.map(([, t]) => `<th>${t}</th>`).join("")}</tr></thead>
      <tbody>${filas.map(f => `<tr>${q.columnas.map(([c]) => `<td>${esc(f[c])}</td>`).join("")}</tr>`).join("")}
      </tbody></table>`;
  } catch (e) {
    caja.innerHTML = "";
    avisarError(e);
  }
}
