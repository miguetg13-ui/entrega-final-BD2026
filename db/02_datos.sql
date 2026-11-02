-- =====================================================================
--  Foro de Ayuda Técnica — Datos del caso
--  Los mismos datos del backup de la Entrega 3 (backupforo.sql), con las
--  tildes corregidas. Correr después de 01_ddl_completo.sql.
-- =====================================================================

SET client_encoding = 'UTF8';

INSERT INTO usuario (id_usuario, nombre, email, fecha_registro) VALUES
(1, 'Ana Torres',      'ana.torres@foro.com',      '2026-09-08 23:02:02'),
(2, 'Carlos Martinez', 'carlos.martinez@foro.com', '2026-09-08 23:02:02'),
(3, 'Laura Gomez',     'laura.gomez@foro.com',     '2026-09-08 23:02:02'),
(4, 'Diego Ramirez',   'diego.ramirez@foro.com',   '2026-09-08 23:02:02'),
(5, 'Sofia Hernandez', 'sofia.hernandez@foro.com', '2026-09-08 23:02:02');

INSERT INTO tema (id_tema, nombre, descripcion) VALUES
(1, 'PostgreSQL', 'Desarrollo y administración de bases de datos utilizando PostgreSQL y consultas SQL.'),
(2, 'Python',     'Programación, errores y soluciones en Python.'),
(3, 'Django',     'Desarrollo web utilizando el framework Django.'),
(4, 'Java',       'Programación orientada a objetos y aplicaciones Java.');

INSERT INTO etiqueta (id_etiqueta, nombre) VALUES
(1, 'postgresql'), (2, 'python'), (3, 'django'), (4, 'sql'),
(5, 'error'), (6, 'programacion'), (7, 'base-de-datos');

INSERT INTO pregunta (id_pregunta, id_usuario, id_tema, titulo, contenido, fecha_publicacion, ultima_actividad) VALUES
(1, 1, 1, '¿Cómo crear y utilizar una clave foránea en PostgreSQL?',
    'Necesito relacionar correctamente las preguntas con los usuarios utilizando claves foráneas y mantener la integridad referencial.',
    '2026-09-08 23:03:07', '2026-09-08 23:03:07'),
(2, 2, 2, '¿Cómo solucionar un error de conexión en Python?',
    'Mi aplicación Python no logra conectarse correctamente a la base de datos PostgreSQL y necesito revisar la configuración de conexión.',
    '2026-09-08 23:03:07', '2026-09-08 23:03:07'),
(3, 3, 3, '¿Cómo organizar las aplicaciones en Django?',
    'Estoy desarrollando una aplicación web en Django y quiero separar correctamente las funcionalidades en diferentes aplicaciones.',
    '2026-09-08 23:03:07', '2026-09-08 23:03:07'),
(4, 4, 4, '¿Cómo utilizar herencia en Java?',
    'Necesito implementar una clase base y varias clases derivadas en Java utilizando herencia.',
    '2026-09-08 23:03:07', '2026-09-08 23:03:07'),
(5, 5, 1, '¿Cómo consultar preguntas por tema en PostgreSQL?',
    'Quiero obtener todas las preguntas que pertenecen a un tema específico utilizando una consulta SQL.',
    '2026-09-08 23:03:07', '2026-09-08 23:03:07');

INSERT INTO pregunta_etiqueta (id_pregunta, id_etiqueta) VALUES
(1, 1), (1, 4), (1, 7), (2, 2), (2, 5), (3, 3), (3, 6), (4, 6), (5, 1), (5, 4);

-- El trigger trg_comentario_actualiza_pregunta actualiza ultima_actividad al insertar
INSERT INTO comentario (id_comentario, id_usuario, id_pregunta, id_comentario_padre, contenido, fecha_publicacion) VALUES
(1, 2, 1, NULL, 'Puedes crear una clave foránea utilizando REFERENCES y apuntando al identificador del usuario.', '2026-09-08 23:04:18'),
(2, 3, 1, NULL, 'También recomiendo agregar NOT NULL si toda pregunta debe pertenecer obligatoriamente a un usuario.', '2026-09-08 23:04:18'),
(3, 4, 2, NULL, 'Revisa que el servidor PostgreSQL esté activo y que el puerto configurado sea el correcto.', '2026-09-08 23:04:18'),
(4, 5, 3, NULL, 'Lo más recomendable es separar las funcionalidades en aplicaciones pequeñas dentro del proyecto.', '2026-09-08 23:04:18'),
(5, 1, 1, 1,    'Gracias, ya entendí cómo utilizar REFERENCES para establecer la relación.', '2026-09-08 23:05:40'),
(6, 3, 1, 5,    'Exactamente. De esta forma puedes mantener la integridad referencial entre las tablas.', '2026-09-08 23:06:59');

INSERT INTO voto_pregunta (id_usuario, id_pregunta, valor, fecha_voto) VALUES
(2, 1, 1, '2026-09-08 23:07:10'), (3, 1, 1, '2026-09-08 23:07:10'),
(4, 2, 1, '2026-09-08 23:07:10'), (5, 3, 1, '2026-09-08 23:07:10'),
(1, 4, -1, '2026-09-08 23:07:10'), (2, 5, 1, '2026-09-08 23:07:10');

INSERT INTO voto_comentario (id_usuario, id_comentario, valor, fecha_voto) VALUES
(1, 1, 1, '2026-09-08 23:07:19'), (3, 1, 1, '2026-09-08 23:07:19'),
(4, 2, 1, '2026-09-08 23:07:19'), (5, 3, -1, '2026-09-08 23:07:19'),
(2, 4, 1, '2026-09-08 23:07:19'), (4, 5, 1, '2026-09-08 23:07:19'),
(5, 6, 1, '2026-09-08 23:07:19');

-- Como los ids se insertaron a mano, las secuencias siguen desde el último id
SELECT setval('usuario_id_usuario_seq',       (SELECT MAX(id_usuario)    FROM usuario));
SELECT setval('tema_id_tema_seq',             (SELECT MAX(id_tema)       FROM tema));
SELECT setval('etiqueta_id_etiqueta_seq',     (SELECT MAX(id_etiqueta)   FROM etiqueta));
SELECT setval('pregunta_id_pregunta_seq',     (SELECT MAX(id_pregunta)   FROM pregunta));
SELECT setval('comentario_id_comentario_seq', (SELECT MAX(id_comentario) FROM comentario));
