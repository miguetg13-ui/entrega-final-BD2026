from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends

from bd import error_bd, no_existe, obtener_conexion
from modelos import ComentarioEntrada, VotoEntrada

router = APIRouter(prefix="/comentarios", tags=["Comentarios"])


@router.get("")
def listar_comentarios(id_pregunta: Optional[int] = None, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        consulta = """SELECT c.*, u.nombre AS autor, p.titulo AS pregunta
                      FROM comentario c
                      JOIN usuario u  ON u.id_usuario = c.id_usuario
                      JOIN pregunta p ON p.id_pregunta = c.id_pregunta"""
        if id_pregunta is None:
            cur.execute(consulta + " ORDER BY c.id_comentario")
        else:
            cur.execute(consulta + " WHERE c.id_pregunta = %s ORDER BY c.id_comentario", (id_pregunta,))
        return cur.fetchall()


@router.get("/{id_comentario}")
def obtener_comentario(id_comentario: int, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM comentario WHERE id_comentario = %s", (id_comentario,))
        fila = cur.fetchone()
    if fila is None:
        raise no_existe("el comentario", id_comentario)
    return fila


@router.post("", status_code=201,
             summary="Crear comentario (dispara los triggers de validación del padre y de última actividad)")
def crear_comentario(datos: ComentarioEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """INSERT INTO comentario (id_usuario, id_pregunta, id_comentario_padre, contenido)
                   VALUES (%s, %s, %s, %s) RETURNING *""",
                (datos.id_usuario, datos.id_pregunta, datos.id_comentario_padre, datos.contenido),
            )
            fila = cur.fetchone()
        conexion.commit()
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.put("/{id_comentario}")
def actualizar_comentario(id_comentario: int, datos: ComentarioEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """UPDATE comentario
                   SET id_usuario = %s, id_pregunta = %s, id_comentario_padre = %s, contenido = %s
                   WHERE id_comentario = %s RETURNING *""",
                (datos.id_usuario, datos.id_pregunta, datos.id_comentario_padre, datos.contenido,
                 id_comentario),
            )
            fila = cur.fetchone()
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
    if fila is None:
        raise no_existe("el comentario", id_comentario)
    return fila


@router.delete("/{id_comentario}")
def borrar_comentario(id_comentario: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            # Las respuestas a este comentario se borran en cascada (fk_comentario_padre)
            cur.execute("DELETE FROM comentario WHERE id_comentario = %s", (id_comentario,))
            borrados = cur.rowcount
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e, "borrar")
    if borrados == 0:
        raise no_existe("el comentario", id_comentario)
    return {"mensaje": f"Comentario {id_comentario} borrado, con sus respuestas."}


@router.post("/{id_comentario}/votos", summary="Votar un comentario (el trigger impide votar el propio)")
def votar_comentario(id_comentario: int, voto: VotoEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("SELECT 1 FROM comentario WHERE id_comentario = %s", (id_comentario,))
            if cur.fetchone() is None:
                raise no_existe("el comentario", id_comentario)
            cur.execute(
                """INSERT INTO voto_comentario (id_usuario, id_comentario, valor) VALUES (%s, %s, %s)
                   ON CONFLICT (id_usuario, id_comentario)
                   DO UPDATE SET valor = EXCLUDED.valor, fecha_voto = CURRENT_TIMESTAMP""",
                (voto.id_usuario, id_comentario, voto.valor),
            )
            cur.execute("SELECT COALESCE(SUM(valor), 0) AS puntaje FROM voto_comentario WHERE id_comentario = %s",
                        (id_comentario,))
            puntaje = cur.fetchone()["puntaje"]
        conexion.commit()
        return {"mensaje": "Voto registrado.", "id_comentario": id_comentario, "puntaje": puntaje}
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
