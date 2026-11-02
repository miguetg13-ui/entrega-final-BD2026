-- =====================================================================
--  Foro de Ayuda Técnica — Script DDL completo (Entrega Final)
--  Tablas, restricciones, índices, funciones, procedimientos, triggers
--  y vista. Listo para correr contra una base VACÍA:
--
--     createdb -U postgres foro_ayuda_tecnica
--     psql -U postgres -d foro_ayuda_tecnica -f db/01_ddl_completo.sql
--     psql -U postgres -d foro_ayuda_tecnica -f db/02_datos.sql
--
--  Cambio respecto a la Entrega 3: se agregó pregunta.ultima_actividad,
--  que mantiene el trigger trg_comentario_actualiza_pregunta.
-- =====================================================================

SET client_encoding = 'UTF8';

-- ---------------------------------------------------------------------
--  1. Tablas
-- ---------------------------------------------------------------------

CREATE TABLE usuario (
    id_usuario      SERIAL       PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL,
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT usuario_email_key UNIQUE (email)
);

CREATE TABLE tema (
    id_tema      SERIAL       PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    CONSTRAINT tema_nombre_key UNIQUE (nombre)
);

CREATE TABLE etiqueta (
    id_etiqueta  SERIAL      PRIMARY KEY,
    nombre       VARCHAR(50) NOT NULL,
    CONSTRAINT etiqueta_nombre_key UNIQUE (nombre)
);

CREATE TABLE pregunta (
    id_pregunta        SERIAL       PRIMARY KEY,
    id_usuario         INTEGER      NOT NULL,
    id_tema            INTEGER      NOT NULL,
    titulo             VARCHAR(200) NOT NULL,
    contenido          TEXT         NOT NULL,
    fecha_publicacion  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultima_actividad   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Sin ON DELETE: no se puede borrar un usuario o un tema que tenga preguntas
    CONSTRAINT fk_pregunta_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario),
    CONSTRAINT fk_pregunta_tema    FOREIGN KEY (id_tema)    REFERENCES tema (id_tema)
);

CREATE TABLE pregunta_etiqueta (
    id_pregunta  INTEGER NOT NULL,
    id_etiqueta  INTEGER NOT NULL,
    CONSTRAINT pregunta_etiqueta_pkey PRIMARY KEY (id_pregunta, id_etiqueta),
    CONSTRAINT fk_pe_pregunta FOREIGN KEY (id_pregunta) REFERENCES pregunta (id_pregunta) ON DELETE CASCADE,
    CONSTRAINT fk_pe_etiqueta FOREIGN KEY (id_etiqueta) REFERENCES etiqueta (id_etiqueta) ON DELETE CASCADE
);

CREATE TABLE comentario (
    id_comentario        SERIAL    PRIMARY KEY,
    id_usuario           INTEGER   NOT NULL,
    id_pregunta          INTEGER   NOT NULL,
    id_comentario_padre  INTEGER,                -- relación recursiva: respuesta a otro comentario
    contenido            TEXT      NOT NULL,
    fecha_publicacion    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comentario_usuario  FOREIGN KEY (id_usuario)  REFERENCES usuario (id_usuario),
    CONSTRAINT fk_comentario_pregunta FOREIGN KEY (id_pregunta) REFERENCES pregunta (id_pregunta) ON DELETE CASCADE,
    CONSTRAINT fk_comentario_padre    FOREIGN KEY (id_comentario_padre) REFERENCES comentario (id_comentario) ON DELETE CASCADE
);

CREATE TABLE voto_pregunta (
    id_usuario   INTEGER   NOT NULL,
    id_pregunta  INTEGER   NOT NULL,
    valor        SMALLINT  NOT NULL,
    fecha_voto   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT voto_pregunta_pkey PRIMARY KEY (id_usuario, id_pregunta),
    CONSTRAINT ck_voto_pregunta_valor CHECK (valor IN (-1, 1)),
    CONSTRAINT fk_voto_pregunta_usuario  FOREIGN KEY (id_usuario)  REFERENCES usuario (id_usuario)   ON DELETE CASCADE,
    CONSTRAINT fk_voto_pregunta_pregunta FOREIGN KEY (id_pregunta) REFERENCES pregunta (id_pregunta) ON DELETE CASCADE
);

CREATE TABLE voto_comentario (
    id_usuario     INTEGER   NOT NULL,
    id_comentario  INTEGER   NOT NULL,
    valor          SMALLINT  NOT NULL,
    fecha_voto     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT voto_comentario_pkey PRIMARY KEY (id_usuario, id_comentario),
    CONSTRAINT ck_voto_comentario_valor CHECK (valor IN (-1, 1)),
    CONSTRAINT fk_voto_comentario_usuario    FOREIGN KEY (id_usuario)    REFERENCES usuario (id_usuario)       ON DELETE CASCADE,
    CONSTRAINT fk_voto_comentario_comentario FOREIGN KEY (id_comentario) REFERENCES comentario (id_comentario) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
--  2. Índices
-- ---------------------------------------------------------------------

-- Listar las preguntas de un tema es la consulta más común del foro
CREATE INDEX idx_pregunta_id_tema ON pregunta (id_tema);
-- Cargar los comentarios de una pregunta (detalle de la pregunta)
CREATE INDEX idx_comentario_id_pregunta ON comentario (id_pregunta);

-- ---------------------------------------------------------------------
--  3. Funciones y procedimientos (Trabajo de Unidad 4)
-- ---------------------------------------------------------------------

-- F1. "Vamos a calcular el puntaje de una pregunta: votos positivos menos negativos"
CREATE OR REPLACE FUNCTION fn_puntaje_pregunta(
    IN  p_id_pregunta INTEGER,
    OUT puntaje       INTEGER
)
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pregunta WHERE id_pregunta = p_id_pregunta) THEN
        RAISE EXCEPTION 'No existe la pregunta %', p_id_pregunta
            USING ERRCODE = 'no_data_found';
    END IF;

    SELECT COALESCE(SUM(valor), 0) INTO puntaje
    FROM voto_pregunta
    WHERE id_pregunta = p_id_pregunta;
END;
$$ LANGUAGE plpgsql;

-- F2. "Vamos a calcular la reputación de un usuario: la suma de los votos
--      que recibieron sus preguntas y sus comentarios"
CREATE OR REPLACE FUNCTION fn_reputacion_usuario(
    IN  p_id_usuario INTEGER,
    OUT reputacion   INTEGER
)
AS $$
DECLARE
    votos_preguntas   INTEGER;
    votos_comentarios INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_usuario) THEN
        RAISE EXCEPTION 'No existe el usuario %', p_id_usuario
            USING ERRCODE = 'no_data_found';
    END IF;

    SELECT COALESCE(SUM(vp.valor), 0) INTO votos_preguntas
    FROM voto_pregunta vp
    JOIN pregunta p ON p.id_pregunta = vp.id_pregunta
    WHERE p.id_usuario = p_id_usuario;

    SELECT COALESCE(SUM(vc.valor), 0) INTO votos_comentarios
    FROM voto_comentario vc
    JOIN comentario c ON c.id_comentario = vc.id_comentario
    WHERE c.id_usuario = p_id_usuario;

    reputacion := votos_preguntas + votos_comentarios;
END;
$$ LANGUAGE plpgsql;

-- F3. "Vamos a clasificar a un usuario en un nivel según su reputación"
CREATE OR REPLACE FUNCTION fn_nivel_usuario(IN p_id_usuario INTEGER)
RETURNS VARCHAR AS $$
DECLARE
    rep INTEGER := fn_reputacion_usuario(p_id_usuario);
BEGIN
    IF rep >= 5 THEN
        RETURN 'Experto';
    ELSIF rep >= 2 THEN
        RETURN 'Colaborador';
    ELSIF rep >= 0 THEN
        RETURN 'Nuevo';
    ELSE
        RETURN 'En observación';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- F4. "Vamos a medir qué tan profunda está una respuesta dentro de una
--      conversación: 0 si comenta la pregunta, 1 si responde a un comentario..."
--      Recorre la relación recursiva comentario -> comentario padre con un ciclo.
CREATE OR REPLACE FUNCTION fn_profundidad_comentario(IN p_id_comentario INTEGER)
RETURNS INTEGER AS $$
DECLARE
    actual      INTEGER;
    profundidad INTEGER := 0;
BEGIN
    SELECT id_comentario_padre INTO actual
    FROM comentario WHERE id_comentario = p_id_comentario;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el comentario %', p_id_comentario
            USING ERRCODE = 'no_data_found';
    END IF;

    WHILE actual IS NOT NULL LOOP
        profundidad := profundidad + 1;
        SELECT id_comentario_padre INTO actual
        FROM comentario WHERE id_comentario = actual;
    END LOOP;

    RETURN profundidad;
END;
$$ LANGUAGE plpgsql;

-- P1. "Vamos a registrar el voto de un usuario sobre una pregunta; si ya
--      había votado, se cambia su voto en vez de duplicarlo"
CREATE OR REPLACE PROCEDURE sp_votar_pregunta(
    IN p_id_usuario  INTEGER,
    IN p_id_pregunta INTEGER,
    IN p_valor       SMALLINT
)
AS $$
BEGIN
    IF p_valor NOT IN (-1, 1) THEN
        RAISE EXCEPTION 'El voto debe ser 1 (a favor) o -1 (en contra), no %', p_valor
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    INSERT INTO voto_pregunta (id_usuario, id_pregunta, valor)
    VALUES (p_id_usuario, p_id_pregunta, p_valor)
    ON CONFLICT (id_usuario, id_pregunta)
    DO UPDATE SET valor = EXCLUDED.valor, fecha_voto = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
--  4. Triggers
-- ---------------------------------------------------------------------

-- T1. Qué hace: impide que un usuario vote su propia pregunta o su propio comentario.
--     Por qué importa: la reputación del foro sale de los votos; si cada quien
--     pudiera votarse a sí mismo, el puntaje y el nivel de usuario no valdrían nada.
CREATE OR REPLACE FUNCTION trg_fn_no_votar_propio()
RETURNS TRIGGER AS $$
DECLARE
    autor INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'voto_pregunta' THEN
        SELECT id_usuario INTO autor FROM pregunta WHERE id_pregunta = NEW.id_pregunta;
        IF autor = NEW.id_usuario THEN
            RAISE EXCEPTION 'No puedes votar tu propia pregunta';
        END IF;
    ELSE
        SELECT id_usuario INTO autor FROM comentario WHERE id_comentario = NEW.id_comentario;
        IF autor = NEW.id_usuario THEN
            RAISE EXCEPTION 'No puedes votar tu propio comentario';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_voto_pregunta_no_propio
BEFORE INSERT OR UPDATE ON voto_pregunta
FOR EACH ROW EXECUTE FUNCTION trg_fn_no_votar_propio();

CREATE TRIGGER trg_voto_comentario_no_propio
BEFORE INSERT OR UPDATE ON voto_comentario
FOR EACH ROW EXECUTE FUNCTION trg_fn_no_votar_propio();

-- T2. Qué hace: verifica que una respuesta (comentario con padre) pertenezca a
--     la misma pregunta que el comentario al que responde, y que no se responda a sí mismo.
--     Por qué importa: la llave foránea solo revisa que el padre exista; sin este
--     trigger se podría "responder" a un comentario de otra pregunta y los hilos
--     de conversación quedarían mezclados.
CREATE OR REPLACE FUNCTION trg_fn_validar_comentario_padre()
RETURNS TRIGGER AS $$
DECLARE
    pregunta_del_padre INTEGER;
BEGIN
    IF NEW.id_comentario_padre IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.id_comentario_padre = NEW.id_comentario THEN
        RAISE EXCEPTION 'Un comentario no puede responderse a sí mismo';
    END IF;

    SELECT id_pregunta INTO pregunta_del_padre
    FROM comentario WHERE id_comentario = NEW.id_comentario_padre;

    IF FOUND AND pregunta_del_padre <> NEW.id_pregunta THEN
        RAISE EXCEPTION 'El comentario % pertenece a otra pregunta; la respuesta debe ir en la pregunta %',
            NEW.id_comentario_padre, pregunta_del_padre;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_comentario_validar_padre
BEFORE INSERT OR UPDATE ON comentario
FOR EACH ROW EXECUTE FUNCTION trg_fn_validar_comentario_padre();

-- T3. Qué hace: cuando llega un comentario nuevo, actualiza la última actividad
--     de su pregunta.
--     Por qué importa: el foro ordena las preguntas por actividad reciente; sin
--     esto, una pregunta vieja que acaba de recibir ayuda quedaría enterrada.
CREATE OR REPLACE FUNCTION trg_fn_actualizar_actividad()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pregunta
    SET ultima_actividad = GREATEST(ultima_actividad, NEW.fecha_publicacion)
    WHERE id_pregunta = NEW.id_pregunta;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_comentario_actualiza_pregunta
AFTER INSERT ON comentario
FOR EACH ROW EXECUTE FUNCTION trg_fn_actualizar_actividad();

-- ---------------------------------------------------------------------
--  5. Vista (bono Unidad 4)
-- ---------------------------------------------------------------------

-- "Resumen de cada pregunta del foro: tema, autor, etiquetas, cuántos
--  comentarios tiene, su puntaje y cuándo tuvo actividad por última vez."
--  Es la portada del foro en la aplicación.
CREATE OR REPLACE VIEW vw_resumen_preguntas AS
SELECT p.id_pregunta,
       p.titulo,
       t.nombre AS tema,
       u.nombre AS autor,
       p.fecha_publicacion,
       p.ultima_actividad,
       (SELECT COUNT(*) FROM comentario c WHERE c.id_pregunta = p.id_pregunta) AS num_comentarios,
       (SELECT COALESCE(SUM(v.valor), 0) FROM voto_pregunta v WHERE v.id_pregunta = p.id_pregunta) AS puntaje,
       COALESCE(string_agg(e.nombre, ', ' ORDER BY e.nombre), '') AS etiquetas
FROM pregunta p
JOIN tema t    ON t.id_tema = p.id_tema
JOIN usuario u ON u.id_usuario = p.id_usuario
LEFT JOIN pregunta_etiqueta pe ON pe.id_pregunta = p.id_pregunta
LEFT JOIN etiqueta e           ON e.id_etiqueta = pe.id_etiqueta
GROUP BY p.id_pregunta, t.nombre, u.nombre;
