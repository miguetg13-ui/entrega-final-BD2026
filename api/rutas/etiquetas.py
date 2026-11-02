import psycopg2
from fastapi import APIRouter, Depends

from bd import error_bd, no_existe, obtener_conexion
from modelos import EtiquetaEntrada

router = APIRouter(prefix="/etiquetas", tags=["Etiquetas"])


@router.get("")
def listar_etiquetas(conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM etiqueta ORDER BY nombre")
        return cur.fetchall()


@router.get("/{id_etiqueta}")
def obtener_etiqueta(id_etiqueta: int, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM etiqueta WHERE id_etiqueta = %s", (id_etiqueta,))
        fila = cur.fetchone()
    if fila is None:
        raise no_existe("la etiqueta", id_etiqueta)
    return fila


@router.post("", status_code=201)
def crear_etiqueta(datos: EtiquetaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("INSERT INTO etiqueta (nombre) VALUES (%s) RETURNING *", (datos.nombre,))
            fila = cur.fetchone()
        conexion.commit()
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.put("/{id_etiqueta}")
def actualizar_etiqueta(id_etiqueta: int, datos: EtiquetaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "UPDATE etiqueta SET nombre = %s WHERE id_etiqueta = %s RETURNING *",
                (datos.nombre, id_etiqueta),
            )
            fila = cur.fetchone()
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
    if fila is None:
        raise no_existe("la etiqueta", id_etiqueta)
    return fila


@router.delete("/{id_etiqueta}")
def borrar_etiqueta(id_etiqueta: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("DELETE FROM etiqueta WHERE id_etiqueta = %s", (id_etiqueta,))
            borrados = cur.rowcount
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e, "borrar")
    if borrados == 0:
        raise no_existe("la etiqueta", id_etiqueta)
    return {"mensaje": f"Etiqueta {id_etiqueta} borrada."}
