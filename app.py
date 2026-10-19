import json
from pathlib import Path

import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Test de filiación divina | Demigods ARG",
    page_icon="⚡",
    layout="centered",
)

# --- Configuración de la base de datos ---
TABLE_NAME = "campistas"
CIRSE_COLUMN = "cirse"  # Se escribe CIRSE con S, según el esquema de Demigods.
DEITY_COLUMN = "deidad"
CABIN_COLUMN = "cabana"

with open(Path(__file__).with_name("data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

GODS = DATA["gods"]
QUESTIONS = DATA["questions"]
PRONOUN_QUESTION = next(q for q in QUESTIONS if "pronombres" in q.lower())
THREE_BIG = {"Zeus", "Poseidón", "Hades"}

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
    # Cualquier deidad no enumerada explícitamente va a la cabaña 11.
    return CABIN_BY_GOD.get(god, 11)


@st.cache_resource
def get_supabase_client():
    """Crea el cliente con secretos configurados en Streamlit, nunca en el código."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en los Secrets de Streamlit."
        ) from exc
    if not url or not key:
        raise RuntimeError("Los Secrets de Supabase están vacíos.")
    return create_client(url, key)


def find_campista(cirse):
    """Devuelve 'missing', 'occupied' o 'available'. Nunca modifica datos."""
    client = get_supabase_client()
    result = (
        client.table(TABLE_NAME)
        .select(f"{CIRSE_COLUMN},{DEITY_COLUMN},{CABIN_COLUMN}")
        .eq(CIRSE_COLUMN, cirse)
        .limit(2)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return "missing"
    if len(rows) > 1:
        raise RuntimeError(
            f"Hay más de una fila con ese Circe en la tabla {TABLE_NAME}. Contactá al equipo."
        )
    row = rows[0]
    # Se considera ocupado si ya tiene una deidad O una cabaña asignada.
    if row.get(DEITY_COLUMN) is not None or row.get(CABIN_COLUMN) is not None:
        return "occupied"
    return "available"


def update_campista(cirse, god, cabin):
    """Actualiza solo deidad y cabana; el filtro NULL evita doble asignación concurrente."""
    client = get_supabase_client()
    result = (
        client.table(TABLE_NAME)
        .update({DEITY_COLUMN: god, CABIN_COLUMN: cabin})
        .eq(CIRSE_COLUMN, cirse)
        .is_(DEITY_COLUMN, "null")
        .is_(CABIN_COLUMN, "null")
        .select(CIRSE_COLUMN)
        .execute()
    )
    if not result.data:
        # Otro usuario pudo terminar el test en paralelo, o la fila ya no está disponible.
        return False
    return True


def calculate_scores(answers, pronouns):
    scores = {god: 0 for god in GODS}
    for question, answer in answers.items():
        if question == PRONOUN_QUESTION:
            continue
        rule = QUESTIONS[question][answer]
        for god in rule.get("gods", []):
            if god in scores:
                scores[god] += 1
    # Regla acordada: si marcó Él (solo o combinado), Artemisa queda en cero puntos.
    if "Él" in pronouns:
        scores["Artemisa"] = 0
    return scores


def get_candidates(scores):
    ranked = sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0])))
    positive = [(g, s) for g, s in ranked if s > 0]
    if not positive:
        return [], ranked, False

    max_score = positive[0][1]
    tied_top = [g for g, score in positive if score == max_score]
    allowed_big = {tied_top[0]} if len(tied_top) == 1 and tied_top[0] in THREE_BIG else set()
    filtered = [(g, s) for g, s in positive if g not in THREE_BIG or g in allowed_big]

    # Con tres o más dioses empatados en el máximo, Hermes va primero y se muestran
    # como máximo dos de los dioses empatados. Se conserva el orden original de GODS.
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

    seen = set()
    candidates = [(g, s) for g, s in candidates if not (g in seen or seen.add(g))][:3]
    return candidates, ranked, hermes_tie_rule


def reset_session():
    for key in (
        "answers", "step", "stage", "cirse", "pronouns", "selected_god",
        "manual_god", "final_choice", "campista_checked", "db_error",
    ):
        st.session_state.pop(key, None)


# Estado de la aplicación
if "stage" not in st.session_state:
    st.session_state.stage = "cirse"
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "step" not in st.session_state:
    st.session_state.step = 0
if "pronouns" not in st.session_state:
    st.session_state.pronouns = []
if "manual_god" not in st.session_state:
    st.session_state.manual_god = GODS[0]

st.title("⚡ Test de filiación divina")
st.caption("Demigods ARG")

if st.session_state.stage == "cirse":
    st.write("Ingresá únicamente el número de Circe que te asignó el equipo.")
    with st.form("cirse_form"):
        cirse_input = st.text_input("Número de Circe", placeholder="Ej.: 1042")
        submitted = st.form_submit_button("Continuar", type="primary", use_container_width=True)
    if submitted:
        cirse = cirse_input.strip()
        if not cirse:
            st.error("Ingresá tu número de Circe.")
        elif not cirse.isdigit():
            st.error("El número de Circe debe contener solo números.")
        else:
            try:
                status = find_campista(cirse)
                if status == "missing":
                    st.error("El Circe no existe.")
                elif status == "occupied":
                    st.error("Circe no disponible.")
                else:
                    st.session_state.cirse = cirse
                    st.session_state.answers = {}
                    st.session_state.step = 0
                    st.session_state.pronouns = []
                    st.session_state.stage = "test"
                    st.rerun()
            except Exception as exc:
                st.error("No pudimos consultar la base de datos. Intentá de nuevo más tarde.")
                st.caption(f"Detalle técnico: {exc}")

elif st.session_state.stage == "test":
    # La pregunta de pronombres se presenta como selección múltiple, no como una
    # lista de combinaciones predefinidas en data.json.
    question_names = [q for q in QUESTIONS if q != PRONOUN_QUESTION] + [PRONOUN_QUESTION]
    total = len(question_names)
    step = st.session_state.step
    question = question_names[step]
    st.caption(f"Circe: {st.session_state.cirse}")
    st.progress((step + 1) / total, text=f"Pregunta {step + 1} de {total}")
    st.subheader(question)

    if question == PRONOUN_QUESTION:
        st.write("Podés seleccionar todas las opciones que quieras.")
        pronoun_options = ["Él", "Ella", "Elle"]
        current = st.session_state.pronouns
        selected = st.multiselect(
            "¿Qué pronombres usás para referirte a vos?",
            options=pronoun_options,
            default=current,
            placeholder="Elegí una o más opciones",
        )
        answer = selected
    else:
        options = list(QUESTIONS[question].keys())
        existing = st.session_state.answers.get(question)
        selected_index = options.index(existing) if existing in options else 0
        answer = st.radio(
            "Elegí una opción:", options,
            index=selected_index,
            key=f"answer_{step}",
            label_visibility="collapsed",
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Anterior", disabled=(step == 0), use_container_width=True):
            if question == PRONOUN_QUESTION:
                st.session_state.pronouns = answer
            else:
                st.session_state.answers[question] = answer
            st.session_state.step -= 1
            st.rerun()
    with col2:
        label = "Ver resultados →" if step == total - 1 else "Siguiente →"
        if st.button(label, type="primary", use_container_width=True):
            if question == PRONOUN_QUESTION:
                st.session_state.pronouns = answer
            else:
                st.session_state.answers[question] = answer
            if step == total - 1:
                st.session_state.stage = "choice"
            else:
                st.session_state.step += 1
            st.rerun()

elif st.session_state.stage == "choice":
    scores = calculate_scores(st.session_state.answers, st.session_state.pronouns)
    candidates, ranked, hermes_tie_rule = get_candidates(scores)
    st.subheader("Elegí tu filiación divina")
    st.write("Podés elegir uno de los resultados del test o seleccionar manualmente cualquier deidad.")
    if hermes_tie_rule:
        st.info("Hubo un empate de tres o más dioses en el puntaje máximo: se aplica la regla de Hermes.")

    if candidates:
        choice_labels = [f"{god} · {score} puntos" for god, score in candidates] + ["Elegir manualmente"]
        choice = st.radio("Opciones", choice_labels, index=0, key="final_choice")
        if choice == "Elegir manualmente":
            selected_god = st.selectbox("Elegí el dios o la diosa", GODS, key="manual_god_select")
        else:
            selected_god = candidates[choice_labels.index(choice)][0]
    else:
        st.warning("No hay resultados positivos para ofrecer. Podés elegir manualmente una deidad.")
        selected_god = st.selectbox("Elegí el dios o la diosa", GODS, key="manual_god_select_empty")

    st.session_state.selected_god = selected_god
    cabin = get_cabin(selected_god)
    st.write(f"**Deidad elegida:** {selected_god}")
    st.write(f"**Cabaña asignada:** {cabin}")
    st.warning("Al confirmar, se guardarán únicamente `deidad` y `cabana` en la fila de tu Circe.")

    if st.button("Confirmar filiación divina", type="primary", use_container_width=True):
        try:
            updated = update_campista(st.session_state.cirse, selected_god, cabin)
            if updated:
                st.session_state.stage = "done"
                st.rerun()
            else:
                st.error("Circe no disponible. La fila ya no está vacía o fue asignada por otra persona. Contactá al equipo si creés que es un error.")
        except Exception as exc:
            st.error("No pudimos guardar el resultado. No vuelvas a enviar varias veces; intentá de nuevo o contactá al equipo.")
            st.caption(f"Detalle técnico: {exc}")

    if st.button("Volver a las preguntas"):
        st.session_state.stage = "test"
        st.session_state.step = len([q for q in QUESTIONS if q != PRONOUN_QUESTION])
        st.rerun()

elif st.session_state.stage == "done":
    god = st.session_state.selected_god
    cabin = get_cabin(god)
    st.success(f"¡Filiación divina registrada! Tu deidad es {god} y tu cabaña es la número {cabin}.")
    st.write("Ya podés cerrar esta página.")
    if st.button("Volver al inicio", type="primary", use_container_width=True):
        reset_session()
        st.rerun()

with st.expander("Puntajes del test (modo de revisión)"):
    if st.session_state.answers:
        scores = calculate_scores(st.session_state.answers, st.session_state.pronouns)
        for god, score in sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0]))):
            st.write(f"{god}: {score}")
    else:
        st.caption("Los puntajes aparecerán después de responder las preguntas.")
