# Demigods ARG — Test e inscripción (modo preparado para Supabase)

## Archivos
- `app.py`: interfaz, preguntas, puntuaciones, selección de deidad, cálculo de cabaña y vista previa.
- `data.json`: datos y reglas del test.
- `requirements.txt`: dependencia de Streamlit.

## Publicación de prueba
Subí los tres archivos a la raíz de un repositorio GitHub y publicá `app.py` en Streamlit Community Cloud.

## Estado de la conexión
Esta versión NO consulta ni escribe en Supabase. El Circe se valida solo como campo numérico y no se puede saber todavía si existe o está ocupado. En el código están las funciones `check_cirse_in_database()` y `update_campista_in_database()` como puntos de integración para implementar cuando tengamos el proyecto Next.js/Supabase y definamos el mecanismo seguro de actualización.

Al confirmar, muestra una vista previa del payload que se enviaría; no persiste datos. Los datos se mantienen en la sesión de Streamlit.

## Reglas implementadas
- Se solicita Circe, nombre, apellido y correo antes del test.
- El resultado ofrece hasta tres deidades y una cuarta opción `Elegir manualmente`.
- Si tres o más deidades empatan en el máximo, Hermes aparece primero y se muestran hasta dos de las deidades empatadas, con desempate determinista según el orden de la lista original.
- Los Tres Grandes solo pueden aparecer como candidato si uno de ellos tiene el máximo puntaje en solitario.
- Artemisa se excluye según la regla de pronombres del test.
- La cabaña se calcula con la lista recibida; las deidades no enumeradas van a la cabaña 11.
- No se inserta ninguna fila ni se actualiza Supabase.

## Nota para la integración real
La versión definitiva debería realizar la validación y actualización exclusivamente en el backend de Next.js (o en una API de servidor protegida). La operación será un `UPDATE` filtrado por `circe` y por el estado pendiente del registro; nunca un `INSERT`. No se deben incluir claves privilegiadas de Supabase en el frontend ni en un repositorio público.
