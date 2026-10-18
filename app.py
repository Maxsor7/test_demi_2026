import json
import re
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Inscripción de campistas | Demigods IT", page_icon="⚡", layout="centered")

with open(Path(__file__).with_name("data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

GODS = DATA["gods"]
QUESTIONS = DATA["questions"]
THREE_BIG = {"Zeus", "Poseidón", "Hades"}

# Cabañas confirmadas por Demigods ARG. Toda deidad no listada va a la 11.
CABIN_BY_GOD = {
    "Zeus": 1, "Eolo": 1,
    "Hera": 2,
    "Poseidón": 3,
    "Demeter": 4, "Deméter": 4, "Perséfone": 4,
    "Ares": 5, "Deimos": 5, "Fobos": 5,
    "Atenea": 6,
    "Apolo": 7, "Asclepio": 7, "Higía": 7,
    "Artemisa": 8,
    "Hefesto": 9,
    "Afrodita": 10,
    "Hermes": 11, "Hebe": 11, "Jano": 11, "Harmonía": 11,
    "Dionisio": 12,
    "Hades": 13,
    "Iris": 14,
    "Hypnos": 15, "Tánatos": 15, "Nix": 15,
    "Némesis": 16,
    "Hécate": 20,
}

def get_cabin(god):
    return CABIN_BY_GOD.get(god, 11)

def calculate_scores(answers):
    scores = {god: 0 for god in GODS}
    exclude_artemisa = False
    for question, answer in answers.items():
        rule = QUESTIONS[question][answer]
        for god in rule.get("gods", []):
            if god in scores:
                scores[god] += 1
        if rule.get("action") == "exclude_artemisa":
            exclude_artemisa = True
    return scores, exclude_artemisa

def get_candidates(scores, exclude_artemisa):
    ranked = sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0])))
    positive = [(g, s) for g, s in ranked if s > 0]
    if exclude_artemisa:
        positive = [(g, s) for g, s in positive if g != "Artemisa"]
    if not positive:
        return [], ranked, False

    max_score = positive[0][1]
    tied_top = [g for g, s in positive if s == max_score]
    # Los Tres Grandes solo pueden aparecer si uno de ellos es líder único.
    allowed_big = {tied_top[0]} if len(tied_top) == 1 and tied_top[0] in THREE_BIG else set()
    filtered = [(g, s) for g, s in positive if g not in THREE_BIG or g in allowed_big]

    # Si tres o más dioses empatan en el máximo, Hermes va primero y se muestran
    # como máximo dos de los dioses empatados. La lista de GODS desempata el orden.
    hermes_tie_rule = len(tied_top) >= 3
    if hermes_tie_rule:
        top_allowed = [(g, s) for g, s in filtered if g in tied_top and g != "Hermes"]
        candidates = [("Hermes", scores.get("Hermes", 0))]
        candidates.extend(top_allowed[:2])
        for item in filtered:
            if len(candidates) >= 3:
                break
            if item[0] not in {g for g, _ in candidates}:
                candidates.append(item)
    else:
        candidates = filtered[:3]

    # Siempre habrá hasta tres opciones de deidad; la cuarta opción es selección manual.
    # Si quedan menos de tres candidatos positivos, no se inventan puntuaciones.
    seen = set()
    candidates = [(g, s) for g, s in candidates if not (g in seen or seen.add(g))][:3]
    return candidates, ranked, hermes_tie_rule

def validate_form(cirse, nombre, apellido, email):
    errors = []
    cirse = cirse.strip()
    if not cirse:
        errors.append("Ingresá tu número de Circe.")
    elif not cirse.isdigit():
        errors.append("El número de Circe debe ser numérico.")
    if not nombre.strip():
        errors.append("Ingresá tu nombre.")
    if not apellido.strip():
        errors.append("Ingresá tu apellido.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        errors.append("Ingresá un correo electrónico válido.")
    return errors

# Estas funciones quedan como puntos de integración. En esta versión no consultan ni escriben Supabase.
def check_cirse_in_database(cirse):
    """TODO: consultar Supabase y devolver 'missing', 'occupied' o 'available'."""
    return "not_connected"

def update_campista_in_database(payload):
    """TODO: actualizar la fila existente filtrando por circe; nunca insertar una nueva."""
    raise NotImplementedError("La conexión con Supabase todavía no está activada.")

if "answers" not in st.session_state: st.session_state.answers = {}
if "step" not in st.session_state: st.session_state.step = 0
if "stage" not in st.session_state: st.session_state.stage = "form"
if "profile" not in st.session_state: st.session_state.profile = {}
if "selected_god" not in st.session_state: st.session_state.selected_god = None
if "manual_god" not in st.session_state: st.session_state.manual_god = GODS[0]

st.title("⚡ Inscripción de campistas")
st.caption("Demigods ARG · Test de filiación divina")
st.info("Versión de prueba: el formulario y los resultados funcionan, pero todavía no se consulta ni se modifica Supabase. Por eso, la existencia o disponibilidad del Circe aún no puede verificarse.")

if st.session_state.stage == "form":
    st.subheader("Identificación del campista")
    st.write("Ingresá el número de Circe que te asignó el equipo de Demigods ARG.")
    with st.form("campista_form"):
        cirse = st.text_input("Número de Circe", placeholder="Ej.: 1042")
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        email = st.text_input("Correo electrónico", placeholder="nombre@ejemplo.com")
        submitted = st.form_submit_button("Continuar al test", type="primary", use_container_width=True)
    if submitted:
        errors = validate_form(cirse, nombre, apellido, email)
        if errors:
            for error in errors: st.error(error)
        else:
            # No se consulta la base todavía; solo conservamos los datos en la sesión actual.
            st.session_state.profile = {"circe": int(cirse.strip()), "nombre": nombre.strip(), "apellido": apellido.strip(), "email": email.strip()}
            st.session_state.answers = {}
            st.session_state.step = 0
            st.session_state.stage = "test"
            st.rerun()

elif st.session_state.stage == "test":
    question_names = list(QUESTIONS.keys())
    total = len(question_names)
    step = st.session_state.step
    question = question_names[step]
    options = list(QUESTIONS[question].keys())
    st.caption(f"Campista: {st.session_state.profile.get('nombre', '')} · Circe: {st.session_state.profile.get('circe', '')}")
    st.progress((step + 1) / total, text=f"Pregunta {step + 1} de {total}")
    st.subheader(question)
    if "pronombres" in question.lower():
        st.caption("Esta respuesta aplica la regla de elegibilidad de Artemisa definida para este test.")
    existing = st.session_state.answers.get(question)
    selected_index = options.index(existing) if existing in options else 0
    answer = st.radio("Elegí una opción:", options, index=selected_index, key=f"answer_{step}", label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Anterior", disabled=(step == 0), use_container_width=True):
            st.session_state.answers[question] = answer
            st.session_state.step -= 1
            st.rerun()
    with col2:
        label = "Ver resultados →" if step == total - 1 else "Siguiente →"
        if st.button(label, type="primary", use_container_width=True):
            st.session_state.answers[question] = answer
            if step == total - 1:
                st.session_state.stage = "choice"
            else:
                st.session_state.step += 1
            st.rerun()

elif st.session_state.stage == "choice":
    scores, exclude_artemisa = calculate_scores(st.session_state.answers)
    candidates, ranked, hermes_tie_rule = get_candidates(scores, exclude_artemisa)
    st.subheader("Elegí tu filiación divina")
    st.write("Podés elegir uno de los resultados del test o seleccionar manualmente cualquier deidad.")
    if hermes_tie_rule:
        st.info("Hubo un empate de tres o más dioses en el puntaje máximo: se aplica la regla de Hermes.")
    if candidates:
        labels = [f"{god} · {score} puntos" for god, score in candidates]
        choice_labels = labels + ["Elegir manualmente"]
        choice = st.radio("Opciones", choice_labels, index=0, key="final_choice")
        if choice == "Elegir manualmente":
            manual_god = st.selectbox("Elegí el dios o la diosa", GODS, index=GODS.index(st.session_state.manual_god) if st.session_state.manual_god in GODS else 0)
            selected_god = manual_god
        else:
            selected_god = candidates[choice_labels.index(choice)][0]
        st.session_state.selected_god = selected_god
        cabin = get_cabin(selected_god)
        profile = st.session_state.profile
        st.divider()
        st.subheader("Resumen de inscripción")
        st.write(f"**Nombre:** {profile['nombre']} {profile['apellido']}")
        st.write(f"**Circe:** {profile['circe']}")
        st.write(f"**Correo:** {profile['email']}")
        st.write(f"**Padre/madre divino/a:** {selected_god}")
        st.write(f"**Cabaña asignada:** {cabin}")
        st.warning("Esto es una vista previa. Todavía no se guarda nada en la base de datos.")
        if st.button("Confirmar en modo de prueba", type="primary", use_container_width=True):
            st.session_state.stage = "preview_done"
            st.rerun()
    else:
        st.warning("No hay resultados positivos para ofrecer. Podés elegir manualmente una deidad.")
        manual_god = st.selectbox("Elegí el dios o la diosa", GODS)
        st.session_state.selected_god = manual_god
        st.write(f"Cabaña asignada: **{get_cabin(manual_god)}**")
        if st.button("Continuar", type="primary", use_container_width=True):
            st.session_state.stage = "preview_done"
            st.rerun()
    if st.button("Volver a las preguntas"):
        st.session_state.stage = "test"
        st.session_state.step = len(QUESTIONS) - 1
        st.rerun()

elif st.session_state.stage == "preview_done":
    profile = st.session_state.profile
    god = st.session_state.selected_god
    cabin = get_cabin(god)
    st.success(f"¡Bienvenido/a, {profile['nombre']}, hijo/a de {god}! Tu cabaña es la número {cabin}.")
    st.info("Inscripción simulada: no se envió ni guardó información en Supabase.")
    with st.expander("Ver datos que se enviarían al conectar la base de datos"):
        payload = {"circe": profile["circe"], "nombre": profile["nombre"], "apellido": profile["apellido"], "email": profile["email"], "deidad": god, "cabana": cabin}
        st.json(payload)
    if st.button("Volver al inicio", type="primary"):
        for key in ("answers", "step", "stage", "profile", "selected_god", "manual_god", "final_choice"):
            st.session_state.pop(key, None)
        st.rerun()

with st.expander("Puntajes del test (modo de revisión)"):
    if st.session_state.answers:
        scores, exclude_artemisa = calculate_scores(st.session_state.answers)
        for god, score in sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0]))):
            st.write(f"{god}: {score}")
    else:
        st.caption("Los puntajes aparecerán después de responder las preguntas.")
