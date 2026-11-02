# Diagrama E-R final — Foro de Ayuda Técnica

El modelo tal como quedó implementado en `db/01_ddl_completo.sql`.
GitHub dibuja este diagrama automáticamente. En VS Code se ve con la extensión *Markdown Preview Mermaid Support*.

```mermaid
erDiagram
    USUARIO ||--o{ PREGUNTA : "publica"
    USUARIO ||--o{ COMENTARIO : "escribe"
    TEMA ||--o{ PREGUNTA : "agrupa"
    PREGUNTA ||--o{ COMENTARIO : "recibe"
    COMENTARIO |o--o{ COMENTARIO : "es respondido por"
    PREGUNTA ||--o{ PREGUNTA_ETIQUETA : "tiene"
    ETIQUETA ||--o{ PREGUNTA_ETIQUETA : "clasifica"
    USUARIO ||--o{ VOTO_PREGUNTA : "emite"
    PREGUNTA ||--o{ VOTO_PREGUNTA : "recibe"
    USUARIO ||--o{ VOTO_COMENTARIO : "emite"
    COMENTARIO ||--o{ VOTO_COMENTARIO : "recibe"

    USUARIO {
        int id_usuario PK
        varchar nombre
        varchar email UK
        timestamp fecha_registro
    }
    TEMA {
        int id_tema PK
        varchar nombre UK
        varchar descripcion
    }
    ETIQUETA {
        int id_etiqueta PK
        varchar nombre UK
    }
    PREGUNTA {
        int id_pregunta PK
        int id_usuario FK
        int id_tema FK
        varchar titulo
        text contenido
        timestamp fecha_publicacion
        timestamp ultima_actividad
    }
    PREGUNTA_ETIQUETA {
        int id_pregunta PK, FK
        int id_etiqueta PK, FK
    }
    COMENTARIO {
        int id_comentario PK
        int id_usuario FK
        int id_pregunta FK
        int id_comentario_padre FK "recursiva"
        text contenido
        timestamp fecha_publicacion
    }
    VOTO_PREGUNTA {
        int id_usuario PK, FK
        int id_pregunta PK, FK
        smallint valor "1 o -1"
        timestamp fecha_voto
    }
    VOTO_COMENTARIO {
        int id_usuario PK, FK
        int id_comentario PK, FK
        smallint valor "1 o -1"
        timestamp fecha_voto
    }
```

## Relaciones y qué pasa al borrar

| Relación | Cardinalidad | Al borrar el "padre" |
|---|---|---|
| usuario → pregunta | 1 : N | **Se impide** (409: "el usuario tiene preguntas publicadas") |
| usuario → comentario | 1 : N | **Se impide** (409: "el usuario tiene comentarios publicados") |
| tema → pregunta | 1 : N | **Se impide** (409: "el tema tiene preguntas") |
| pregunta → comentario | 1 : N | Se borran sus comentarios (CASCADE) |
| comentario → comentario (respuesta) | 1 : N, recursiva | Se borran sus respuestas (CASCADE) |
| pregunta ↔ etiqueta | N : M (tabla `pregunta_etiqueta`) | Se borra la asociación (CASCADE) |
| usuario/pregunta → voto_pregunta | N : M con atributo `valor` | Se borran los votos (CASCADE) |
| usuario/comentario → voto_comentario | N : M con atributo `valor` | Se borran los votos (CASCADE) |

## Cambio respecto a la Entrega 3

Se agregó `pregunta.ultima_actividad`. Guarda cuándo tuvo actividad la pregunta por última vez, y la actualiza el trigger `trg_comentario_actualiza_pregunta`.
