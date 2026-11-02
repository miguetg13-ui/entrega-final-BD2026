"""Consultas de negocio: las mismas del Trabajo de Unidad 4 (db/03_consultas_unidad4.sql),
con los valores fijos convertidos en parámetros que manda la aplicación."""
from fastapi import APIRouter, Depends, Query

from bd import no_existe, obtener_conexion

router = APIRouter(prefix="/consultas", tags=["Consultas de negocio"])


@router.get("/actividad-por-tema",
            summary="¿Qué temas mueven más el foro? Preguntas y comentarios por tema en los últimos N días")
def actividad_por_tema(dias: int = Query(365, ge=1, le=3650), conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute(
            """SELECT t.nombre                      AS tema,
                      COUNT(DISTINCT p.id_pregunta) AS preguntas,
                      COUNT(c.id_comentario)        AS comentarios
               FROM tema t
               JOIN pregunta p        ON p.id_tema = t.id_tema
               LEFT JOIN comentario c ON c.id_pregunta = p.id_pregunta
               WHERE p.fecha_publicacion >= CURRENT_DATE - make_interval(days => %s)
               GROUP BY t.nombre
               ORDER BY comentarios DESC, preguntas DESC""",
            (dias,),
        )
        return cur.fetchall()


@router.get("/usuarios-mas-votados",
            summary="¿Quién hace las mejores preguntas? Usuarios con más votos a favor en sus preguntas")
def usuarios_mas_votados(minimo: int = Query(1, ge=1), conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute(
            """SELECT u.id_usuario, u.nombre, COUNT(*) AS votos_a_favor
               FROM usuario u
               JOIN pregunta p      ON p.id_usuario = u.id_usuario
               JOIN voto_pregunta v ON v.id_pregunta = p.id_pregunta
               WHERE v.valor = 1
               GROUP BY u.id_usuario, u.nombre
               HAVING COUNT(*) >= %s
               ORDER BY votos_a_favor DESC, u.nombre""",
            (minimo,),
        )
        return cur.fetchall()


@router.get("/etiquetas-por-tema",
            summary="¿De qué se pide más ayuda en un tema? Etiquetas más usadas en las preguntas del tema")
def etiquetas_por_tema(id_tema: int = Query(..., gt=0), conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute("SELECT 1 FROM tema WHERE id_tema = %s", (id_tema,))
        if cur.fetchone() is None:
            raise no_existe("el tema", id_tema)
        cur.execute(
            """SELECT e.nombre AS etiqueta, COUNT(*) AS preguntas
               FROM etiqueta e
               JOIN pregunta_etiqueta pe ON pe.id_etiqueta = e.id_etiqueta
               JOIN pregunta p           ON p.id_pregunta = pe.id_pregunta
               WHERE p.id_tema = %s
               GROUP BY e.nombre
               ORDER BY preguntas DESC, e.nombre""",
            (id_tema,),
        )
        return cur.fetchall()


@router.get("/preguntas-sin-ayuda",
            summary="¿A quién le falta ayuda? Preguntas con menos de N comentarios")
def preguntas_sin_ayuda(max_comentarios: int = Query(2, ge=1), conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute(
            """SELECT p.id_pregunta, p.titulo, u.nombre AS autor,
                      COUNT(c.id_comentario) AS comentarios
               FROM pregunta p
               JOIN usuario u         ON u.id_usuario = p.id_usuario
               LEFT JOIN comentario c ON c.id_pregunta = p.id_pregunta
               WHERE p.fecha_publicacion <= CURRENT_TIMESTAMP
               GROUP BY p.id_pregunta, p.titulo, u.nombre
               HAVING COUNT(c.id_comentario) < %s
               ORDER BY comentarios, p.id_pregunta""",
            (max_comentarios,),
        )
        return cur.fetchall()


@router.get("/hilos",
            summary="Conversaciones de dos niveles (self-join sobre comentario -> comentario padre)")
def hilos(conexion=Depends(obtener_conexion)):
    with conexion.cursor() as cur:
        cur.execute(
            """SELECT r.id_comentario AS id_respuesta,      ur.nombre AS quien_responde, r.contenido AS respuesta,
                      c.id_comentario AS id_respondido,     uc.nombre AS autor_respondido,
                      o.id_comentario AS id_original,       uo.nombre AS autor_original, o.contenido AS original,
                      r.id_pregunta
               FROM comentario r
               JOIN comentario c ON c.id_comentario = r.id_comentario_padre
               JOIN comentario o ON o.id_comentario = c.id_comentario_padre
               JOIN usuario ur   ON ur.id_usuario = r.id_usuario
               JOIN usuario uc   ON uc.id_usuario = c.id_usuario
               JOIN usuario uo   ON uo.id_usuario = o.id_usuario
               ORDER BY r.id_comentario"""
        )
        return cur.fetchall()
