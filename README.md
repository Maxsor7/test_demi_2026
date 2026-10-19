# Test de filiación divina — Demigods ARG

## Archivos
- `app.py`: aplicación Streamlit con conexión a Supabase.
- `data.json`: preguntas y reglas de puntuación actuales.
- `requirements.txt`: dependencias.

## Publicar en Streamlit Community Cloud
1. Subí estos tres archivos al repositorio de GitHub que quieras usar para el test.
2. En Streamlit Community Cloud, creá una app conectada a ese repositorio y seleccioná `app.py` como archivo principal.
3. En la configuración de la app, abrí **Settings → Secrets** y agregá los secretos con este formato (reemplazá los valores por los nuevos secretos; no los subas a GitHub):

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "TU_NUEVA_SERVICE_ROLE_KEY"
```

## Suposiciones del esquema de Supabase
- Tabla: `campistas`.
- Columna de búsqueda: `cirse` (con S).
- Columnas actualizadas: `deidad` y `cabana`.
- Se considera que el Circe está disponible solo cuando `deidad IS NULL` **y** `cabana IS NULL`.
- Al confirmar, se hace un `UPDATE` filtrado por `cirse` y por ambas columnas aún nulas. No se insertan filas y no se actualizan otros campos. Esto también evita una doble asignación concurrente en condiciones normales.

Si la disponibilidad se determina de otra manera, modificá la función `find_campista` y la condición de `update_campista` antes de publicar.

## Seguridad importante
La `service_role` key tiene permisos elevados y nunca debe quedar en el código, en `data.json` ni en el repositorio. Configurala solamente en **Streamlit → Settings → Secrets**. Si una clave real fue compartida en un chat o subida a GitHub, revocala y generá otra antes de probar.

## Reglas de la aplicación
- La pantalla inicial pide solamente el Circe.
- Pronombres: selección múltiple de Él, Ella y Elle. Si se selecciona Él, Artemisa queda con 0 puntos.
- Al finalizar se elige una de las opciones sugeridas o una deidad manualmente.
- Se guardan solo `deidad` y `cabana`.
- Cualquier deidad sin cabaña específica asignada se deriva a la cabaña 11.

## Probar con cuidado
Primero usá un Circe de prueba cuya fila tenga `deidad` y `cabana` vacíos. La confirmación escribe en la base real. No pruebes con un Circe de una persona real sin autorización.
