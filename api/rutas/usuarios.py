import psycopg2
from fastapi import APIRouter, Depends

from bd import error_bd, no_existe, obtener_conexion
from modelos import UsuarioEntrada

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("")
def listar_usuarios(conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM usuario ORDER BY id_usuario")
        return cur.fetchall()


@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
        fila = cur.fetchone()
    if fila is None:
        raise no_existe("el usuario", id_usuario)
    return fila


@router.get("/{id_usuario}/perfil", summary="Reputación y nivel (usa fn_reputacion_usuario y fn_nivel_usuario)")
def perfil_usuario(id_usuario: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """SELECT u.id_usuario, u.nombre, u.email,
                          fn_reputacion_usuario(u.id_usuario) AS reputacion,
                          fn_nivel_usuario(u.id_usuario)      AS nivel,
                          (SELECT COUNT(*) FROM pregunta p   WHERE p.id_usuario = u.id_usuario) AS preguntas,
                          (SELECT COUNT(*) FROM comentario c WHERE c.id_usuario = u.id_usuario) AS comentarios
                   FROM usuario u WHERE u.id_usuario = %s""",
                (id_usuario,),
            )
            fila = cur.fetchone()
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
    if fila is None:
        raise no_existe("el usuario", id_usuario)
    return fila


@router.post("", status_code=201)
def crear_usuario(datos: UsuarioEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "INSERT INTO usuario (nombre, email) VALUES (%s, %s) RETURNING *",
                (datos.nombre, datos.email),
            )
            fila = cur.fetchone()
        conexion.commit()
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.put("/{id_usuario}")
def actualizar_usuario(id_usuario: int, datos: UsuarioEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "UPDATE usuario SET nombre = %s, email = %s WHERE id_usuario = %s RETURNING *",
                (datos.nombre, datos.email, id_usuario),
            )
            fila = cur.fetchone()
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
    if fila is None:
        raise no_existe("el usuario", id_usuario)
    return fila


@router.delete("/{id_usuario}")
def borrar_usuario(id_usuario: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
            borrados = cur.rowcount
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e, "borrar")
    if borrados == 0:
        raise no_existe("el usuario", id_usuario)
    return {"mensaje": f"Usuario {id_usuario} borrado."}
