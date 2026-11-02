from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends

from bd import error_bd, no_existe, obtener_conexion
from modelos import PreguntaEntrada, VotoEntrada

router = APIRouter(prefix="/preguntas", tags=["Preguntas"])

# Cada pregunta con la lista de ids de sus etiquetas (para llenar el formulario de edición)
SELECT_PREGUNTA = """
    SELECT p.*,
           COALESCE(array_agg(pe.id_etiqueta ORDER BY pe.id_etiqueta)
                    FILTER (WHERE pe.id_etiqueta IS NOT NULL), '{}') AS etiquetas
    FROM pregunta p
    LEFT JOIN pregunta_etiqueta pe ON pe.id_pregunta = p.id_pregunta
"""


def _guardar_etiquetas(cur, id_pregunta: int, etiquetas: list[int]):
    cur.execute("DELETE FROM pregunta_etiqueta WHERE id_pregunta = %s", (id_pregunta,))
    for id_etiqueta in sorted(set(etiquetas)):
        cur.execute(
            "INSERT INTO pregunta_etiqueta (id_pregunta, id_etiqueta) VALUES (%s, %s)",
            (id_pregunta, id_etiqueta),
        )


@router.get("/resumen", summary="Portada del foro (consulta la vista vw_resumen_preguntas)")
def resumen_preguntas(conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT * FROM vw_resumen_preguntas ORDER BY ultima_actividad DESC, id_pregunta DESC")
        return cur.fetchall()


@router.get("")
def listar_preguntas(id_tema: Optional[int] = None, conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        if id_tema is None:
            cur.execute(SELECT_PREGUNTA + " GROUP BY p.id_pregunta ORDER BY p.id_pregunta")
        else:
            cur.execute(SELECT_PREGUNTA + " WHERE p.id_tema = %s GROUP BY p.id_pregunta ORDER BY p.id_pregunta",
                        (id_tema,))
        return cur.fetchall()


@router.get("/{id_pregunta}", summary="Detalle: puntaje (fn_puntaje_pregunta) y comentarios con su profundidad")
def obtener_pregunta(id_pregunta: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """SELECT p.*, t.nombre AS tema, u.nombre AS autor,
                          fn_puntaje_pregunta(p.id_pregunta) AS puntaje
                   FROM pregunta p
                   JOIN tema t    ON t.id_tema = p.id_tema
                   JOIN usuario u ON u.id_usuario = p.id_usuario
                   WHERE p.id_pregunta = %s""",
                (id_pregunta,),
            )
            pregunta = cur.fetchone()
            if pregunta is None:
                raise no_existe("la pregunta", id_pregunta)

            cur.execute(
                """SELECT e.* FROM etiqueta e
                   JOIN pregunta_etiqueta pe ON pe.id_etiqueta = e.id_etiqueta
                   WHERE pe.id_pregunta = %s ORDER BY e.nombre""",
                (id_pregunta,),
            )
            pregunta["etiquetas"] = cur.fetchall()

            cur.execute(
                """SELECT c.*, u.nombre AS autor,
                          fn_profundidad_comentario(c.id_comentario) AS profundidad,
                          COALESCE(SUM(v.valor), 0) AS puntaje
                   FROM comentario c
                   JOIN usuario u ON u.id_usuario = c.id_usuario
                   LEFT JOIN voto_comentario v ON v.id_comentario = c.id_comentario
                   WHERE c.id_pregunta = %s
                   GROUP BY c.id_comentario, u.nombre
                   ORDER BY c.fecha_publicacion, c.id_comentario""",
                (id_pregunta,),
            )
            pregunta["comentarios"] = cur.fetchall()
        return pregunta
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.post("", status_code=201)
def crear_pregunta(datos: PreguntaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """INSERT INTO pregunta (id_usuario, id_tema, titulo, contenido)
                   VALUES (%s, %s, %s, %s) RETURNING id_pregunta""",
                (datos.id_usuario, datos.id_tema, datos.titulo, datos.contenido),
            )
            id_pregunta = cur.fetchone()["id_pregunta"]
            _guardar_etiquetas(cur, id_pregunta, datos.etiquetas)
            cur.execute(SELECT_PREGUNTA + " WHERE p.id_pregunta = %s GROUP BY p.id_pregunta", (id_pregunta,))
            fila = cur.fetchone()
        conexion.commit()  # la pregunta y sus etiquetas se guardan juntas o no se guarda nada
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.put("/{id_pregunta}")
def actualizar_pregunta(id_pregunta: int, datos: PreguntaEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """UPDATE pregunta SET id_usuario = %s, id_tema = %s, titulo = %s, contenido = %s
                   WHERE id_pregunta = %s""",
                (datos.id_usuario, datos.id_tema, datos.titulo, datos.contenido, id_pregunta),
            )
            if cur.rowcount == 0:
                conexion.rollback()
                raise no_existe("la pregunta", id_pregunta)
            _guardar_etiquetas(cur, id_pregunta, datos.etiquetas)
            cur.execute(SELECT_PREGUNTA + " WHERE p.id_pregunta = %s GROUP BY p.id_pregunta", (id_pregunta,))
            fila = cur.fetchone()
        conexion.commit()
        return fila
    except psycopg2.Error as e:
        raise error_bd(conexion, e)


@router.delete("/{id_pregunta}")
def borrar_pregunta(id_pregunta: int, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            # Comentarios, votos y etiquetas de la pregunta se borran en cascada (ON DELETE CASCADE)
            cur.execute("DELETE FROM pregunta WHERE id_pregunta = %s", (id_pregunta,))
            borrados = cur.rowcount
        conexion.commit()
    except psycopg2.Error as e:
        raise error_bd(conexion, e, "borrar")
    if borrados == 0:
        raise no_existe("la pregunta", id_pregunta)
    return {"mensaje": f"Pregunta {id_pregunta} borrada, con sus comentarios y votos."}


@router.post("/{id_pregunta}/votos",
             summary="Votar una pregunta (CALL sp_votar_pregunta; el trigger impide votar la propia)")
def votar_pregunta(id_pregunta: int, voto: VotoEntrada, conexion=Depends(obtener_conexion)):
    try:
        with conexion.cursor() as cur:
            cur.execute("SELECT 1 FROM pregunta WHERE id_pregunta = %s", (id_pregunta,))
            if cur.fetchone() is None:
                raise no_existe("la pregunta", id_pregunta)
            cur.execute("CALL sp_votar_pregunta(%s, %s, %s::SMALLINT)",
                        (voto.id_usuario, id_pregunta, voto.valor))
            cur.execute("SELECT fn_puntaje_pregunta(%s) AS puntaje", (id_pregunta,))
            puntaje = cur.fetchone()["puntaje"]
        conexion.commit()
        return {"mensaje": "Voto registrado.", "id_pregunta": id_pregunta, "puntaje": puntaje}
    except psycopg2.Error as e:
        raise error_bd(conexion, e)
