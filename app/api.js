// Comunicación con la API y avisos para el usuario.

class ErrorApi extends Error {
  constructor(status, detalle, errores = []) {
    super(detalle);
    this.status = status;
    this.errores = errores; // en los 422: [{campo, mensaje}]
  }
}

// Llama a la API y devuelve el JSON. Si la API responde con error, lanza ErrorApi.
async function api(metodo, ruta, cuerpo) {
  let respuesta;
  try {
    respuesta = await fetch(API_URL + ruta, {
      method: metodo,
      headers: cuerpo ? { "Content-Type": "application/json" } : {},
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi(0, "No se pudo conectar con la API. Revisa que esté encendida en " + API_URL + ".");
  }
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, datos.detail || "La API respondió con un error.", datos.errores || []);
  }
  return datos;
}

// Traduce el código HTTP a una frase que entienda quien usa la aplicación.
function mensajeDeError(error) {
  if (!(error instanceof ErrorApi)) return "Ocurrió un error inesperado en la aplicación.";
  switch (error.status) {
    case 0:   return error.message;
    case 404: return "No se encontró: " + error.message;
    case 409: return "No se pudo completar la operación: " + error.message;
    case 422: {
      if (error.errores.length === 0) return "Revisa los datos: " + error.message;
      return "Revisa los datos del formulario: " +
        error.errores.map(e => `${NOMBRES_CAMPOS[e.campo] || e.campo} ${e.mensaje}`).join("; ") + ".";
    }
    case 503: return error.message;
    default:  return "La API tuvo un problema (" + error.status + "). Intenta de nuevo.";
  }
}

const NOMBRES_CAMPOS = {
  nombre: "El nombre", email: "El email", descripcion: "La descripción", titulo: "El título",
  contenido: "El contenido", id_usuario: "El usuario", id_tema: "El tema", id_pregunta: "La pregunta",
  id_comentario_padre: "El comentario al que responde", valor: "El voto", etiquetas: "Las etiquetas",
  dias: "Los días", minimo: "El mínimo", id_tema_q: "El tema", max_comentarios: "El máximo de comentarios",
};

let temporizadorAviso;
function avisar(texto, tipo = "ok") {
  const aviso = document.getElementById("aviso");
  aviso.textContent = texto;
  aviso.className = tipo;
  aviso.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => (aviso.hidden = true), tipo === "error" ? 9000 : 4000);
}

function avisarError(error) {
  avisar(mensajeDeError(error), "error");
}

// Escapa texto antes de meterlo en el HTML
function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function fecha(valor) {
  if (!valor) return "";
  return new Date(valor).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}
