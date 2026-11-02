# Guion de la demo en vivo (Semana 16)

Ensayar completo en el computador de la presentación, con los datos ya cargados.
Para empezar con los datos originales: `docker compose down -v` y luego `docker compose up -d --build`.

## 1. Todo corriendo
- Docker Desktop con los 3 contenedores: `foro-final-db`, `foro-final-api` y `foro-final-app`.
- Abrir http://127.0.0.1:8000/docs y mostrar los grupos de endpoints: Usuarios, Temas, Etiquetas, Preguntas, Comentarios y Consultas.
- Abrir http://localhost:5500.
- Explicar la regla: la aplicación solo conoce la URL de la API (`app/config.js`). La contraseña de la base solo está en el `.env` que lee `api/bd.py`.

## 2. Un CRUD completo desde la aplicación
1. **Usuarios** → crear "Pedro Pérez", `pedro@foro.com`.
2. En psql o pgAdmin: `SELECT * FROM usuario ORDER BY id_usuario;` → aparece.
3. Editarlo desde la aplicación (por ejemplo, cambiar el nombre) → repetir el SELECT.
4. Borrarlo (Borrar → Sí) → repetir el SELECT.

## 3. Las consultas de negocio
Pestaña **Consultas**. Para cada una, decir qué pregunta del caso responde:
- *¿Qué temas mueven más el foro?* — JOIN tema-pregunta-comentario + GROUP BY.
- *¿Quién hace las mejores preguntas?* — votos a favor por autor, con HAVING.
- *¿De qué se pide más ayuda en un tema?* — etiquetas más usadas en un tema.
- *¿A quién le falta ayuda?* — preguntas con pocos comentarios (LEFT JOIN + HAVING).
- *Conversaciones de dos niveles* — self-join de comentario sobre sí mismo.

## 4. La lógica del motor actuando
En **Foro**, abrir "¿Cómo crear y utilizar una clave foránea en PostgreSQL?" (autora: Ana Torres):
- **Procedimiento + función:** votar como *Sofia Hernandez* 👍 → el puntaje sube. Lo calcula `fn_puntaje_pregunta`, después de `CALL sp_votar_pregunta`.
- **Trigger 1:** votar como *Ana Torres* → "No puedes votar tu propia pregunta".
- **Trigger 3:** abrir "¿Cómo utilizar herencia en Java?" y agregar un comentario → la "última actividad" cambia a ahora y la pregunta sube al primer lugar del foro.
- **Trigger 2:** en **Comentarios**, crear uno en la pregunta #2 que responda al comentario #1 (que es de la pregunta #1) → "El comentario 1 pertenece a otra pregunta…".
- **Funciones de usuario:** en **Usuarios** → botón *Perfil* de Laura Gomez → reputación y nivel.

## 5. Un error a propósito
- **409:** en **Temas**, borrar *PostgreSQL* → "No se puede borrar: el tema tiene preguntas". En **Usuarios**, borrar *Ana Torres* → "el usuario tiene preguntas publicadas".
- **409 (UNIQUE):** crear un usuario con el email `ana.torres@foro.com` → "Ya existe un usuario con ese email".
- **422:** crear un tema con el nombre vacío → el campo se marca en rojo con "El nombre debe tener al menos 2 caracteres".
- **404:** en /docs, `GET /usuarios/999` → "No existe el usuario 999".

## 6. Preguntas a cualquiera — dónde está cada cosa
| Si preguntan… | Archivo |
|---|---|
| ¿Dónde está la contraseña? | `.env` (no se sube; el repositorio tiene `.env.example`) |
| ¿Cómo se conecta la API? | `api/bd.py` → `obtener_conexion()` |
| ¿Dónde se hace el rollback? | `api/bd.py` → `error_bd()` |
| ¿Cómo evitan la inyección SQL? | En todas las rutas el SQL usa `%s` y los valores van aparte en una tupla |
| ¿Cómo sale el 409 del trigger? | El trigger hace `RAISE EXCEPTION` → psycopg2 lanza `RaiseException` → `error_bd` responde 409 con ese mensaje |
| ¿Dónde está el 422? | Pydantic en `api/modelos.py`; los mensajes en español están en `main.py` |
| ¿Qué es CORS? | `main.py`: el navegador bloquea respuestas de otro puerto si la API no autoriza `localhost:5500` |
| ¿Cómo muestra el error la aplicación? | `app/api.js` → `mensajeDeError()` |
