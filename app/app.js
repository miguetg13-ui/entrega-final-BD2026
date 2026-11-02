// Menú principal: cada botón muestra una vista. La vista actual queda en la URL (#usuarios, #consultas…).

const VISTAS = {
  foro: vistaForo,
  consultas: vistaConsultas,
  preguntas: () => vistaCrud("preguntas"),
  comentarios: () => vistaCrud("comentarios"),
  usuarios: () => vistaCrud("usuarios"),
  temas: () => vistaCrud("temas"),
  etiquetas: () => vistaCrud("etiquetas"),
};

function abrir(nombre) {
  if (!VISTAS[nombre]) nombre = "foro";
  document.querySelectorAll("#menu button").forEach(b =>
    b.classList.toggle("activo", b.dataset.vista === nombre));
  history.replaceState(null, "", "#" + nombre);
  document.getElementById("aviso").hidden = true;
  VISTAS[nombre]();
}

document.querySelectorAll("#menu button").forEach(b => (b.onclick = () => abrir(b.dataset.vista)));
window.addEventListener("hashchange", () => abrir(location.hash.slice(1)));
abrir(location.hash.slice(1));
