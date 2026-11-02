# Foro de Ayuda Técnica — Entrega Final de Bases de Datos

Aplicación web de un foro de preguntas técnicas. Los usuarios publican preguntas por tema, las etiquetan, las comentan, se responden entre sí y votan preguntas y comentarios.

La aplicación tiene tres capas, y **la aplicación solo habla con la API por HTTP**:

```
Aplicación web (HTML + JS)  ──HTTP──▶  API (FastAPI + psycopg2)  ──SQL──▶  PostgreSQL
   http://localhost:5500                http://127.0.0.1:8000/docs         localhost:5434
```

## Integrantes

- Fredy Manuel Guzmán Herrera
- Miguel Ángel Toro
- Juan De Dios Piedrahita Gómez

## Tecnologías

| Capa | Tecnología |
|---|---|
| Base de datos | PostgreSQL 18 |
| API | Python 3.12, FastAPI, psycopg2, python-dotenv, Uvicorn |
| Aplicación | HTML, CSS y JavaScript sin frameworks (usa `fetch` contra la API) |
| Para levantar todo | Docker Desktop (Docker Compose) |

## Estructura del repositorio

```
entrega-final/
├── README.md                    ← este archivo
├── .env.example                 ← variables que necesita la API (sin valores reales)
├── docker-compose.yml           ← levanta base + API + aplicación
├── db/
│   ├── 01_ddl_completo.sql      ← tablas, restricciones, índices, funciones, procedimiento, triggers y vista
│   ├── 02_datos.sql             ← datos del caso
│   └── 03_consultas_unidad4.sql ← consultas de negocio y pruebas de funciones/triggers
├── api/
│   ├── main.py                  ← crea la app, CORS, manejo de errores 422 y 503
│   ├── bd.py                    ← conexión (lee el .env) y traducción de errores de la base a 404/409/422
│   ├── modelos.py               ← forma del JSON de cada solicitud (Pydantic)
│   ├── rutas/                   ← un archivo por recurso: usuarios, temas, etiquetas, preguntas, comentarios, consultas
│   ├── requirements.txt
│   └── Dockerfile
├── app/
│   ├── index.html, estilos.css
│   ├── config.js                ← URL de la API
│   ├── api.js                   ← fetch + mensajes de error para el usuario
│   ├── crud.js                  ← pantallas de CRUD
│   ├── foro.js                  ← portada y detalle de pregunta (votos, comentarios, respuestas)
│   └── consultas.js             ← consultas de negocio
└── docs/
    ├── diagrama_er.md           ← E-R final
    ├── diccionario_datos.md     ← cada tabla y columna
    └── guion_demo.md            ← paso a paso de la demo en vivo
```

## Cómo levantar todo desde cero (con Docker, recomendado)

Solo hace falta **Docker Desktop** abierto (que diga *Engine running*).

1. Crear el `.env` a partir del ejemplo y poner una contraseña:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
2. Levantar las tres capas. La primera vez, la base se crea sola con `db/01_ddl_completo.sql` y `db/02_datos.sql`:
   ```powershell
   docker compose up -d --build
   ```
3. Abrir:
   - Aplicación: http://localhost:5500
   - API (Swagger): http://127.0.0.1:8000/docs
   - Base (pgAdmin): host `localhost`, puerto `5434`, usuario y contraseña del `.env`, base `foro_ayuda_tecnica`.
   - Base (psql): `docker exec -it foro-final-db psql -U postgres -d foro_ayuda_tecnica`

Otros comandos:

| Para… | Comando |
|---|---|
| Apagar todo (los datos se conservan) | `docker compose down` |
| Borrar la base y volver a crearla con los datos originales | `docker compose down -v` y luego `docker compose up -d --build` |
| Ver los logs de la API | `docker logs -f foro-final-api` |

## Cómo levantarlo sin Docker

Requiere PostgreSQL y Python 3.12 instalados.

1. **Base de datos.** Crear la base y correr los scripts en orden:
   ```powershell
   createdb -U postgres foro_ayuda_tecnica
   psql -U postgres -d foro_ayuda_tecnica -f db/01_ddl_completo.sql
   psql -U postgres -d foro_ayuda_tecnica -f db/02_datos.sql
   ```
2. **.env.** Copiar `.env.example` como `.env`, con `DB_PORT=5432` (o el puerto de su PostgreSQL) y su contraseña.
3. **API:**
   ```powershell
   cd api
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
4. **Aplicación.** Servir la carpeta `app/` en el puerto 5500, con *Live Server* de VS Code o con:
   ```powershell
   cd app
   python -m http.server 5500
   ```

## Qué hace la API

Toda la documentación interactiva está en `/docs`.

| Recurso | Endpoints |
|---|---|
| Usuarios | `GET /usuarios`, `GET /usuarios/{id}`, `POST`, `PUT /usuarios/{id}`, `DELETE /usuarios/{id}`, `GET /usuarios/{id}/perfil` |
| Temas | CRUD completo en `/temas` |
| Etiquetas | CRUD completo en `/etiquetas` |
| Preguntas (FK a usuario y tema) | CRUD completo en `/preguntas`, `GET /preguntas/resumen`, `POST /preguntas/{id}/votos` |
| Comentarios (FK a usuario, pregunta y comentario) | CRUD completo en `/comentarios`, `POST /comentarios/{id}/votos` |
| Consultas de negocio | `/consultas/actividad-por-tema`, `/consultas/usuarios-mas-votados`, `/consultas/etiquetas-por-tema`, `/consultas/preguntas-sin-ayuda`, `/consultas/hilos` |

**Lógica del motor en uso:**
- `POST /preguntas/{id}/votos` → `CALL sp_votar_pregunta(...)`. Dispara el trigger que impide votar la pregunta propia y devuelve el puntaje calculado con `fn_puntaje_pregunta`.
- `POST /comentarios` → dispara `trg_comentario_validar_padre` y `trg_comentario_actualiza_pregunta`.
- `GET /usuarios/{id}/perfil` → `fn_reputacion_usuario` y `fn_nivel_usuario`.
- `GET /preguntas/{id}` → `fn_puntaje_pregunta` y `fn_profundidad_comentario`.
- `GET /preguntas/resumen` → vista `vw_resumen_preguntas`.

**Errores:**

| Código | Cuándo |
|---|---|
| 404 | El registro no existe |
| 409 | La base rechaza el dato: llave foránea, UNIQUE, CHECK o un trigger |
| 422 | El cuerpo no tiene la forma esperada |

Después de cada error de la base se hace `conexion.rollback()` (ver `api/bd.py`).

**Seguridad:**
- Las credenciales están en `.env`, que está en `.gitignore`.
- Todo valor que llega del cliente va como parámetro `%s`; nunca se concatena en el SQL.
