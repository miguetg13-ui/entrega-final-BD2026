# Diccionario de datos — Foro de Ayuda Técnica

Base: `foro_ayuda_tecnica` (PostgreSQL 18). PK = llave primaria, FK = llave foránea, UQ = única.

## usuario
Personas registradas en el foro: preguntan, comentan y votan.

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_usuario | SERIAL (integer) | No | PK | Identificador del usuario |
| nombre | VARCHAR(100) | No | | Nombre que se muestra en el foro |
| email | VARCHAR(150) | No | UQ `usuario_email_key` | Correo del usuario; no se puede repetir |
| fecha_registro | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Cuándo se registró |

## tema
Categorías grandes del foro (PostgreSQL, Python…).

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_tema | SERIAL (integer) | No | PK | Identificador del tema |
| nombre | VARCHAR(100) | No | UQ `tema_nombre_key` | Nombre del tema |
| descripcion | VARCHAR(255) | Sí | | Para qué sirve el tema |

## etiqueta
Palabras clave que clasifican las preguntas con más detalle que el tema.

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_etiqueta | SERIAL (integer) | No | PK | Identificador de la etiqueta |
| nombre | VARCHAR(50) | No | UQ `etiqueta_nombre_key` | Texto de la etiqueta (ej. `sql`) |

## pregunta
Cada consulta de ayuda que publica un usuario.

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_pregunta | SERIAL (integer) | No | PK | Identificador de la pregunta |
| id_usuario | INTEGER | No | FK `fk_pregunta_usuario` → usuario | Quién la publicó |
| id_tema | INTEGER | No | FK `fk_pregunta_tema` → tema; índice `idx_pregunta_id_tema` | Tema al que pertenece |
| titulo | VARCHAR(200) | No | | Título corto de la pregunta |
| contenido | TEXT | No | | Explicación completa del problema |
| fecha_publicacion | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Cuándo se publicó |
| ultima_actividad | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Último comentario recibido; la mantiene un trigger |

## pregunta_etiqueta
Asocia preguntas con etiquetas (relación N:M).

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_pregunta | INTEGER | No | PK compuesta; FK `fk_pe_pregunta` → pregunta (CASCADE) | Pregunta etiquetada |
| id_etiqueta | INTEGER | No | PK compuesta; FK `fk_pe_etiqueta` → etiqueta (CASCADE) | Etiqueta asignada |

## comentario
Respuestas a una pregunta, o a otro comentario (relación recursiva).

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_comentario | SERIAL (integer) | No | PK | Identificador del comentario |
| id_usuario | INTEGER | No | FK `fk_comentario_usuario` → usuario | Quién lo escribió |
| id_pregunta | INTEGER | No | FK `fk_comentario_pregunta` → pregunta (CASCADE); índice `idx_comentario_id_pregunta` | Pregunta en la que aparece |
| id_comentario_padre | INTEGER | Sí | FK `fk_comentario_padre` → comentario (CASCADE) | Comentario al que responde; NULL si responde directamente a la pregunta |
| contenido | TEXT | No | | Texto del comentario |
| fecha_publicacion | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Cuándo se publicó |

## voto_pregunta
Votos de los usuarios sobre las preguntas (un voto por usuario y pregunta).

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_usuario | INTEGER | No | PK compuesta; FK → usuario (CASCADE) | Quién vota |
| id_pregunta | INTEGER | No | PK compuesta; FK → pregunta (CASCADE) | Pregunta votada |
| valor | SMALLINT | No | CHECK `valor IN (-1, 1)` | 1 = a favor, -1 = en contra |
| fecha_voto | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Cuándo votó (o cambió su voto) |

## voto_comentario
Votos de los usuarios sobre los comentarios (un voto por usuario y comentario).

| Columna | Tipo | Nulo | Restricción | Descripción |
|---|---|---|---|---|
| id_usuario | INTEGER | No | PK compuesta; FK → usuario (CASCADE) | Quién vota |
| id_comentario | INTEGER | No | PK compuesta; FK → comentario (CASCADE) | Comentario votado |
| valor | SMALLINT | No | CHECK `valor IN (-1, 1)` | 1 = a favor, -1 = en contra |
| fecha_voto | TIMESTAMP | No | DEFAULT CURRENT_TIMESTAMP | Cuándo votó |

## Vista vw_resumen_preguntas
Resumen de cada pregunta: id, título, tema, autor, fechas, número de comentarios, puntaje y etiquetas (en un solo texto). La aplicación la usa como portada del foro.

## Funciones, procedimientos y triggers

| Objeto | Tipo | Qué hace |
|---|---|---|
| `fn_puntaje_pregunta(id)` | Función (OUT) | Suma de los votos de una pregunta; 404 si no existe |
| `fn_reputacion_usuario(id)` | Función (OUT) | Votos recibidos en las preguntas y los comentarios del usuario |
| `fn_nivel_usuario(id)` | Función | Nuevo / Colaborador / Experto / En observación, según la reputación |
| `fn_profundidad_comentario(id)` | Función (ciclo WHILE) | En qué nivel de la conversación está un comentario |
| `sp_votar_pregunta(usuario, pregunta, valor)` | Procedimiento | Registra el voto o lo cambia si ya existía |
| `trg_voto_pregunta_no_propio` / `trg_voto_comentario_no_propio` | Trigger BEFORE | Impide votar lo propio |
| `trg_comentario_validar_padre` | Trigger BEFORE | La respuesta debe ir en la misma pregunta que el comentario al que responde |
| `trg_comentario_actualiza_pregunta` | Trigger AFTER | Actualiza `pregunta.ultima_actividad` |
