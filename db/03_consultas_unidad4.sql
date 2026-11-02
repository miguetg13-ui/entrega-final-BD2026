-- =====================================================================
--  Foro de Ayuda Técnica — Consultas de negocio (Trabajo de Unidad 4)
--  Cada una combina WHERE + JOIN + GROUP BY con una función de agregación.
--  La API expone estas mismas consultas en /consultas/... (ver api/rutas/consultas.py).
--  Para el informe: correr cada una en psql y tomar la captura.
-- =====================================================================

-- C1. "Vamos a consultar cuántas preguntas y cuántos comentarios tuvo cada
--      tema en los últimos 365 días, para saber qué temas mueven más el foro."
SELECT t.nombre                         AS tema,
       COUNT(DISTINCT p.id_pregunta)    AS preguntas,
       COUNT(c.id_comentario)           AS comentarios
FROM tema t
JOIN pregunta p        ON p.id_tema = t.id_tema
LEFT JOIN comentario c ON c.id_pregunta = p.id_pregunta
WHERE p.fecha_publicacion >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY t.nombre
ORDER BY comentarios DESC, preguntas DESC;

-- C2. "Vamos a consultar qué usuarios recibieron más votos a favor en sus
--      preguntas, para reconocer a quienes hacen las mejores preguntas."
SELECT u.nombre,
       COUNT(*)  AS votos_a_favor
FROM usuario u
JOIN pregunta p      ON p.id_usuario = u.id_usuario
JOIN voto_pregunta v ON v.id_pregunta = p.id_pregunta
WHERE v.valor = 1
GROUP BY u.nombre
HAVING COUNT(*) >= 1
ORDER BY votos_a_favor DESC, u.nombre;

-- C3. "Vamos a consultar cuáles son las etiquetas más usadas en las preguntas
--      del tema PostgreSQL, para saber de qué se pide más ayuda."
SELECT e.nombre       AS etiqueta,
       COUNT(*)       AS preguntas
FROM etiqueta e
JOIN pregunta_etiqueta pe ON pe.id_etiqueta = e.id_etiqueta
JOIN pregunta p           ON p.id_pregunta = pe.id_pregunta
JOIN tema t               ON t.id_tema = p.id_tema
WHERE t.nombre = 'PostgreSQL'
GROUP BY e.nombre
ORDER BY preguntas DESC, e.nombre;

-- C4. "Vamos a consultar las preguntas que todavía tienen menos de 2
--      comentarios, para saber a quién le falta ayuda."
SELECT p.id_pregunta,
       p.titulo,
       u.nombre                 AS autor,
       COUNT(c.id_comentario)   AS comentarios
FROM pregunta p
JOIN usuario u         ON u.id_usuario = p.id_usuario
LEFT JOIN comentario c ON c.id_pregunta = p.id_pregunta
WHERE p.fecha_publicacion <= CURRENT_TIMESTAMP
GROUP BY p.id_pregunta, p.titulo, u.nombre
HAVING COUNT(c.id_comentario) < 2
ORDER BY comentarios, p.id_pregunta;

-- BONO 1 — Self-join sobre la relación recursiva comentario -> respuesta.
-- "Vamos a consultar las conversaciones de dos niveles: una respuesta, el
--  comentario al que responde y el comentario original que inició el hilo."
SELECT r.id_comentario   AS id_respuesta,
       ur.nombre         AS quien_responde,
       r.contenido       AS respuesta,
       c.id_comentario   AS id_comentario_respondido,
       uc.nombre         AS autor_respondido,
       o.id_comentario   AS id_comentario_original,
       uo.nombre         AS autor_original,
       o.contenido       AS comentario_original
FROM comentario r
JOIN comentario c ON c.id_comentario = r.id_comentario_padre   -- nivel 1
JOIN comentario o ON o.id_comentario = c.id_comentario_padre   -- nivel 2
JOIN usuario ur   ON ur.id_usuario = r.id_usuario
JOIN usuario uc   ON uc.id_usuario = c.id_usuario
JOIN usuario uo   ON uo.id_usuario = o.id_usuario
ORDER BY r.id_comentario;

-- BONO 2 — Vista (definida en 01_ddl_completo.sql)
SELECT * FROM vw_resumen_preguntas ORDER BY ultima_actividad DESC;

-- Funciones y procedimientos (definidos en 01_ddl_completo.sql)
SELECT fn_puntaje_pregunta(1);
SELECT fn_reputacion_usuario(3);
SELECT fn_nivel_usuario(3);
SELECT fn_profundidad_comentario(6);
CALL sp_votar_pregunta(4, 5, 1::SMALLINT);

-- Triggers: estas instrucciones DEBEN fallar (es lo que se muestra en la captura)
-- T1: Ana (1) intenta votar su propia pregunta (1)
INSERT INTO voto_pregunta (id_usuario, id_pregunta, valor) VALUES (1, 1, 1);
-- T2: responder al comentario 3 (de la pregunta 2) dentro de la pregunta 1
INSERT INTO comentario (id_usuario, id_pregunta, id_comentario_padre, contenido)
VALUES (2, 1, 3, 'Respuesta en la pregunta equivocada');
-- T3: un comentario nuevo mueve la última actividad de la pregunta 4
SELECT id_pregunta, ultima_actividad FROM pregunta WHERE id_pregunta = 4;
INSERT INTO comentario (id_usuario, id_pregunta, contenido)
VALUES (1, 4, 'Usa extends para heredar de la clase base.');
SELECT id_pregunta, ultima_actividad FROM pregunta WHERE id_pregunta = 4;
