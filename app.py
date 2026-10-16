import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Test de filiación divina | Demigods IT", page_icon="⚡", layout="centered")

with open(Path(__file__).with_name("data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

GODS = DATA["gods"]
QUESTIONS = DATA["questions"]
THREE_BIG = {"Zeus", "Poseidón", "Hades"}
# Hera y Hestia están mencionadas expresamente en la regla de bendición.
BLESSING_GODS = {"Hera", "Hestia"}

st.title("⚡ Test de filiación divina")
st.write("Respondé las preguntas y descubrí qué dios o diosa podría reclamarte como descendiente.")
st.caption("Demigods IT · Universo de Percy Jackson")

if "answers" not in st.session_state:
    st.session_state.answers = {}
if "step" not in st.session_state:
    st.session_state.step = 0
if "finished" not in st.session_state:
    st.session_state.finished = False

question_names = list(QUESTIONS.keys())
total = len(question_names)

def calculate_scores(answers):
    scores = {god: 0 for god in GODS}
    exclude_artemisa = False
    for question, answer in answers.items():
        rule = QUESTIONS[question][answer]
        for god in rule.get("gods", []):
            scores[god] += 1
        if rule.get("action") == "exclude_artemisa":
            exclude_artemisa = True
    return scores, exclude_artemisa

def get_candidates(scores, exclude_artemisa):
    ranked = sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0])))
    # No mostrar dioses con cero puntos como candidatos ordinarios.
    positive = [(g, s) for g, s in ranked if s > 0]
    if exclude_artemisa:
        positive = [(g, s) for g, s in positive if g != "Artemisa"]

    if not positive:
        return [], ranked, False

    # Regla de los tres grandes: solo puede salir uno si es líder único.
    top_score = positive[0][1]
    top_gods = [g for g, s in positive if s == top_score]
    if len(top_gods) == 1 and top_gods[0] in THREE_BIG:
        big_gods_allowed = {top_gods[0]}
    else:
        big_gods_allowed = set()

    filtered = [(g, s) for g, s in positive if g not in THREE_BIG or g in big_gods_allowed]

    # Regla Hermes 1: cuatro o más dioses empatados en el puntaje máximo.
    max_score = max(s for _, s in positive)
    tied_max = [g for g, s in positive if s == max_score]
    hermes_tie_rule = len(tied_max) >= 4
    if hermes_tie_rule:
        others = [(g, s) for g, s in filtered if g not in tied_max and g != "Hermes"]
        candidates = [("Hermes", scores["Hermes"])] + others[:2]
        # Evitar duplicados en caso de que Hermes ya estuviera entre los empatados.
        seen = set()
        candidates = [(g, s) for g, s in candidates if not (g in seen or seen.add(g))]
    else:
        candidates = filtered[:3]

    # Regla bendición: ofrecer cuatro opciones si Hera o Hestia entra entre los candidatos.
    is_blessing = any(g in BLESSING_GODS for g, _ in candidates)
    if is_blessing and not hermes_tie_rule:
        candidates = filtered[:4]

    return candidates, ranked, hermes_tie_rule

# Pantalla final
if st.session_state.finished:
    scores, exclude_artemisa = calculate_scores(st.session_state.answers)
    candidates, ranked, hermes_tie_rule = get_candidates(scores, exclude_artemisa)
    st.success("¡Test completado!")
    if candidates:
        first, first_score = candidates[0]
        st.header(f"Tu resultado principal: {first}")
        st.write(f"Puntaje: **{first_score}**")
        if len(candidates) > 1:
            st.subheader("Otras filiaciones posibles")
            for index, (god, score) in enumerate(candidates[1:], start=2):
                st.write(f"**{index}. {god}** — {score} puntos")
        if hermes_tie_rule:
            st.info("Se aplicó la regla de Hermes por empate amplio.")
        if any(g in BLESSING_GODS for g, _ in candidates):
            st.info("Este resultado puede corresponder a una bendición, según las reglas del test.")
    else:
        st.warning("No hay suficientes puntos para determinar una filiación.")
    with st.expander("Ver puntajes de todos los dioses"):
        for god, score in sorted(scores.items(), key=lambda item: (-item[1], GODS.index(item[0]))):
            st.write(f"{god}: {score}")
    left, right = st.columns(2)
    with left:
        if st.button("Volver a revisar respuestas", use_container_width=True):
            st.session_state.finished = False
            st.session_state.step = total - 1
            st.rerun()
    with right:
        if st.button("Hacer el test de nuevo", type="primary", use_container_width=True):
            st.session_state.answers = {}
            st.session_state.step = 0
            st.session_state.finished = False
            st.rerun()
    st.caption("El resultado se calcula localmente durante esta sesión; el test no guarda ni envía las respuestas a una base de datos.")
    st.stop()

# Pregunta actual
step = st.session_state.step
question = question_names[step]
options = list(QUESTIONS[question].keys())
st.progress((step + 1) / total, text=f"Pregunta {step + 1} de {total}")
st.subheader(question)

# Ayuda breve para pronombres, sin asociar identidad con filiación.
if "pronombres" in question.lower():
    st.caption("Esta respuesta solo aplica la regla de elegibilidad de Artemisa definida para este test.")

existing = st.session_state.answers.get(question)
selected_index = options.index(existing) if existing in options else 0
answer = st.radio(
    "Elegí una opción:",
    options,
    index=selected_index,
    key=f"answer_{step}",
    label_visibility="collapsed",
)

col1, col2 = st.columns(2)
with col1:
    if st.button("← Anterior", disabled=(step == 0), use_container_width=True):
        st.session_state.answers[question] = answer
        st.session_state.step -= 1
        st.rerun()
with col2:
    button_label = "Ver resultados →" if step == total - 1 else "Siguiente →"
    if st.button(button_label, type="primary", use_container_width=True):
        st.session_state.answers[question] = answer
        if step == total - 1:
            st.session_state.finished = True
        else:
            st.session_state.step += 1
        st.rerun()
