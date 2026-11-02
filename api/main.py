"""API del Foro de Ayuda Técnica.

Correr:   uvicorn main:app --reload      (desde la carpeta api/)
Probar:   http://127.0.0.1:8000/docs
"""
import os

import psycopg2
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rutas import comentarios, consultas, etiquetas, preguntas, temas, usuarios

app = FastAPI(
    title="API — Foro de Ayuda Técnica",
    description="Entrega Final de Bases de Datos. La aplicación solo habla con esta API; "
                "esta API es el único programa que se conecta a PostgreSQL.",
    version="1.0.0",
)

# CORS: la aplicación web corre en otro puerto (5500), así que el navegador
# necesita que la API diga explícitamente que ese origen tiene permiso.
origenes = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origenes.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for modulo in (usuarios, temas, etiquetas, preguntas, comentarios, consultas):
    app.include_router(modulo.router)


# --- 422 en español: el cuerpo o los parámetros no tienen la forma esperada -------

def _traducir(error: dict) -> str:
    tipo, ctx = error["type"], error.get("ctx", {})
    if error.get("input") is None and tipo in ("int_type", "string_type", "list_type"):
        return "es obligatorio"  # el campo llegó vacío (null)
    mensajes = {
        "missing": "es obligatorio",
        "string_too_short": f"debe tener al menos {ctx.get('min_length')} caracteres",
        "string_too_long": f"debe tener máximo {ctx.get('max_length')} caracteres",
        "string_pattern_mismatch": "no tiene un formato válido",
        "string_type": "debe ser texto",
        "int_parsing": "debe ser un número entero",
        "int_type": "debe ser un número entero",
        "greater_than": f"debe ser mayor que {ctx.get('gt')}",
        "greater_than_equal": f"debe ser mayor o igual a {ctx.get('ge')}",
        "less_than_equal": f"debe ser menor o igual a {ctx.get('le')}",
        "literal_error": f"debe ser uno de: {str(ctx.get('expected')).replace(' or ', ' o ')}",
        "list_type": "debe ser una lista",
        "extra_forbidden": "no es un campo permitido",
        "json_invalid": "el cuerpo no es un JSON válido",
        "model_attributes_type": "el cuerpo debe ser un objeto JSON",
    }
    return mensajes.get(tipo, error["msg"])


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        campo = ".".join(str(p) for p in error["loc"] if p not in ("body", "query", "path"))
        errores.append({"campo": campo, "mensaje": _traducir(error)})
    resumen = "; ".join(f"{e['campo']}: {e['mensaje']}" if e["campo"] else e["mensaje"] for e in errores)
    return JSONResponse(status_code=422,
                        content={"detail": f"Datos inválidos — {resumen}", "errores": errores})


@app.exception_handler(psycopg2.OperationalError)
async def base_no_disponible(request: Request, exc: psycopg2.OperationalError):
    return JSONResponse(status_code=503,
                        content={"detail": "La API no pudo conectarse a la base de datos. ¿Está PostgreSQL encendido?"})


@app.get("/", tags=["Inicio"])
def inicio():
    return {"mensaje": "API del Foro de Ayuda Técnica", "documentacion": "/docs"}
