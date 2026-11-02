"""Conexión a PostgreSQL y traducción de los errores de la base a respuestas HTTP.

Este es el ÚNICO archivo del proyecto que sabe cómo conectarse a la base.
Las credenciales salen del archivo .env (nunca se escriben en el código).
"""
import os

import psycopg2
from dotenv import load_dotenv
from fastapi import HTTPException
from psycopg2 import errors, pool
from psycopg2.extras import RealDictCursor

load_dotenv()

_pool = None


def _obtener_pool():
    """Crea el pool de conexiones la primera vez que se necesita."""
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "foro_ayuda_tecnica"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            cursor_factory=RealDictCursor,  # cada fila llega como diccionario {columna: valor}
        )
    return _pool


def obtener_conexion():
    """Dependencia de FastAPI: presta una conexión por solicitud y la devuelve al final."""
    conexion = _obtener_pool().getconn()
    try:
        yield conexion
    finally:
        # Si quedó una transacción abierta (por ejemplo, un GET), se cierra sin guardar
        if conexion.status != psycopg2.extensions.STATUS_READY:
            conexion.rollback()
        _obtener_pool().putconn(conexion)


# --- Mensajes para el usuario según la restricción que rechazó el dato -------------

# Llave foránea al BORRAR: el registro todavía tiene otros que dependen de él
MENSAJES_FK_BORRAR = {
    "fk_pregunta_usuario": "No se puede borrar: el usuario tiene preguntas publicadas.",
    "fk_comentario_usuario": "No se puede borrar: el usuario tiene comentarios publicados.",
    "fk_pregunta_tema": "No se puede borrar: el tema tiene preguntas.",
}

# Llave foránea al GUARDAR: se apuntó a un registro que no existe
MENSAJES_FK_GUARDAR = {
    "fk_pregunta_usuario": "El usuario elegido no existe.",
    "fk_pregunta_tema": "El tema elegido no existe.",
    "fk_comentario_usuario": "El usuario elegido no existe.",
    "fk_comentario_pregunta": "La pregunta elegida no existe.",
    "fk_comentario_padre": "El comentario al que respondes no existe.",
    "fk_pe_etiqueta": "Alguna de las etiquetas elegidas no existe.",
    "fk_voto_pregunta_usuario": "El usuario que vota no existe.",
    "fk_voto_comentario_usuario": "El usuario que vota no existe.",
}

MENSAJES_UNICO = {
    "usuario_email_key": "Ya existe un usuario con ese email.",
    "tema_nombre_key": "Ya existe un tema con ese nombre.",
    "etiqueta_nombre_key": "Ya existe una etiqueta con ese nombre.",
    "pregunta_etiqueta_pkey": "La pregunta ya tiene esa etiqueta.",
}


def error_bd(conexion, e: psycopg2.Error, accion: str = "guardar") -> HTTPException:
    """Deshace la transacción y convierte el error de PostgreSQL en una respuesta HTTP.

    Uso:  except psycopg2.Error as e:  raise error_bd(conexion, e, "borrar")
    """
    conexion.rollback()  # sin esto la conexión queda inservible ("current transaction is aborted")
    restriccion = e.diag.constraint_name

    if isinstance(e, errors.ForeignKeyViolation):  # 23503
        mensajes = MENSAJES_FK_BORRAR if accion == "borrar" else MENSAJES_FK_GUARDAR
        return HTTPException(409, mensajes.get(restriccion, "El dato está relacionado con otros registros."))
    if isinstance(e, errors.UniqueViolation):  # 23505
        return HTTPException(409, MENSAJES_UNICO.get(restriccion, "Ese dato ya existe."))
    if isinstance(e, errors.CheckViolation):  # 23514
        return HTTPException(409, "El valor no cumple las reglas de la base de datos.")
    if isinstance(e, errors.RaiseException):  # P0001: RAISE EXCEPTION de un trigger o función
        return HTTPException(409, e.diag.message_primary)
    if isinstance(e, errors.NoDataFound):  # P0002: las funciones avisan que el registro no existe
        return HTTPException(404, e.diag.message_primary)
    if isinstance(e, (errors.InvalidParameterValue, errors.NotNullViolation,
                      errors.StringDataRightTruncation)):
        return HTTPException(422, e.diag.message_primary)
    return HTTPException(500, "Error inesperado de la base de datos.")


def no_existe(que: str, id_: int) -> HTTPException:
    return HTTPException(404, f"No existe {que} {id_}.")
