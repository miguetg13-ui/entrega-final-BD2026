import psycopg2
from fastapi import APIRouter, Depends

from bd import error_bd, no_existe, obtener_conexion
from modelos import TemaEntrada

router = APIRouter(prefix="/temas", tags=["Temas"])


@router.get("")
def listar_temas(conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM tema ORDER BY id_tema")
        return cur.fetchall()


@router.get("/{id_tema}")
def obtener_tema(id_tema: int, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM tema WHERE id_tema = %s", (id_tema,))
        fila = cur.fetchone()
    if fila is None:
        raise no_existe("el tema", id_tema)
    return fila


@router.post("", status_code=201)
def crear_tema(datos: TemaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "INSERT INTO tema (nombre, descripcion) VALUES (%s, %s) RETURNING *",
                (datos.nombre, datos.descripcion),
            )
            fila = cur.fetchone()
        conexion.commit()
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.put("/{id_tema}")
def actualizar_tema(id_tema: int, datos: TemaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "UPDATE tema SET nombre = %s, descripcion = %s WHERE id_tema = %s RETURNING *",
                (datos.nombre, datos.descripcion, id_tema),
            )
            fila = cur.fetchone()
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
    if fila is None:
        raise no_existe("el tema", id_tema)
    return fila


@router.delete("/{id_tema}")
def borrar_tema(id_tema: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("DELETE FROM tema WHERE id_tema = %s", (id_tema,))
            borrados = cur.rowcount
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e, "borrar")
    if borrados == 0:
        raise no_existe("el tema", id_tema)
    return {"mensaje": f"Tema {id_tema} borrado."}
