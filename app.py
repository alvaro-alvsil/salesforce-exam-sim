import streamlit as st
import json
import os
import time
import random
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Salesforce Certification Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Salesforce-themed CSS
st.markdown("""
<style>
    /* Salesforce Brand Palette */
    :root {
        --sfdc-blue: #0176D3;
        --sfdc-dark-blue: #032D60;
        --sfdc-success: #2E844A;
        --sfdc-danger: #EA001E;
        --sfdc-bg-light: #F3F3F3;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0176D3 0%, #032D60 100%);
        color: white !important;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
    }
    .main-header h1 {
        color: white !important;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        color: #E0E8F5 !important;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }
    
    .question-card {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 12px;
        background-color: #E8F4FE;
        color: #0176D3;
        margin-right: 0.5rem;
    }
    
    .score-pass {
        background-color: #D4EDDA;
        color: #155724;
        border: 2px solid #C3E6CB;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    .score-fail {
        background-color: #F8D7DA;
        color: #721C24;
        border: 2px solid #F5C6CB;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Dynamic Live Timer (Updates automatically every 1 second)
# ---------------------------------------------------------
@st.fragment(run_every="1s")
def render_live_timer(exam_mode, start_time, time_limit_minutes):
    if exam_mode == "exam":
        st.info("⏱️ **Modo Examen**")
        elapsed = time.time() - start_time
        total_seconds = time_limit_minutes * 60
        remaining = max(0, total_seconds - elapsed)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        
        if remaining <= 0:
            st.error("⏰ **¡Tiempo finalizado!**")
        elif remaining < 300:
            st.error(f"⏳ **Tiempo restante: {mins:02d}:{secs:02d}**")
        else:
            st.metric("⏳ Tiempo restante", f"{mins:02d}:{secs:02d}")
    else:
        st.success("🎓 **Modo Estudio** (Sin límite de tiempo)")
        elapsed = time.time() - start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        st.metric("⏱️ Tiempo transcurrido", f"{mins:02d}:{secs:02d}")


# ---------------------------------------------------------
# Helper Functions: Exam Loader & Question Preparer
# ---------------------------------------------------------
def find_exam_files():
    """Scans for .json exam files in local and relative directories."""
    possible_dirs = [
        Path(__file__).parent / "exams",
        Path("exams"),
        Path("/exams")
    ]
    exam_files = []
    seen = set()
    for d in possible_dirs:
        if d.is_dir():
            for f in d.glob("*.json"):
                resolved = f.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    exam_files.append(resolved)
    return sorted(exam_files, key=lambda x: x.name)


def load_exam_data(file_path):
    """Loads and validates an exam JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def prepare_exam(raw_data, shuffle_questions=False, shuffle_options=False):
    """Creates a ready-to-use exam structure, applying optional shuffling."""
    questions = list(raw_data.get("questions", []))
    
    if shuffle_questions:
        random.shuffle(questions)
    
    prepared_questions = []
    for q in questions:
        q_copy = dict(q)
        original_options = q.get("options", {})
        original_correct = q.get("correct_answers", [])
        
        if shuffle_options:
            # Pair each original key with its text
            items = list(original_options.items())
            random.shuffle(items)
            
            # Reassign keys A, B, C, D...
            standard_keys = [chr(65 + i) for i in range(len(items))]
            new_options = {}
            new_correct = []
            
            for new_key, (old_key, text) in zip(standard_keys, items):
                new_options[new_key] = text
                if old_key in original_correct:
                    new_correct.append(new_key)
            
            q_copy["options"] = new_options
            q_copy["correct_answers"] = sorted(new_correct)
        else:
            q_copy["options"] = original_options
            q_copy["correct_answers"] = original_correct
            
        prepared_questions.append(q_copy)
        
    return {
        "exam_title": raw_data.get("exam_title", "Salesforce Exam"),
        "time_limit_minutes": raw_data.get("time_limit_minutes", 105),
        "passing_score_percent": raw_data.get("passing_score_percent", 65),
        "questions": prepared_questions
    }


# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "menu"  # "menu", "exam", "results"

if "exam_data" not in st.session_state:
    st.session_state.exam_data = None

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}  # {q_idx: list_of_keys}

if "marked_for_review" not in st.session_state:
    st.session_state.marked_for_review = {}  # {q_idx: bool}

if "study_feedback_shown" not in st.session_state:
    st.session_state.study_feedback_shown = {}  # {q_idx: bool}

if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0

if "exam_mode" not in st.session_state:
    st.session_state.exam_mode = "exam"  # "exam" or "study"

if "start_time" not in st.session_state:
    st.session_state.start_time = 0

if "end_time" not in st.session_state:
    st.session_state.end_time = 0

if "session_seed" not in st.session_state:
    st.session_state.session_seed = 1

if "confirm_finish" not in st.session_state:
    st.session_state.confirm_finish = False


def reset_to_menu():
    st.session_state.screen = "menu"
    st.session_state.exam_data = None
    st.session_state.user_answers = {}
    st.session_state.marked_for_review = {}
    st.session_state.study_feedback_shown = {}
    st.session_state.current_q_idx = 0
    st.session_state.start_time = 0
    st.session_state.end_time = 0
    st.session_state.confirm_finish = False


def restart_same_exam(raw_data, shuffle_q, shuffle_opt):
    st.session_state.exam_data = prepare_exam(raw_data, shuffle_q, shuffle_opt)
    st.session_state.user_answers = {}
    st.session_state.marked_for_review = {}
    st.session_state.study_feedback_shown = {}
    st.session_state.current_q_idx = 0
    st.session_state.start_time = time.time()
    st.session_state.end_time = 0
    st.session_state.session_seed += 1
    st.session_state.confirm_finish = False
    st.session_state.screen = "exam"


# ---------------------------------------------------------
# SCREEN 1: Home / Exam Selection
# ---------------------------------------------------------
def render_menu_screen():
    st.markdown("""
    <div class="main-header">
        <h1>⚡ Salesforce Certification Exam Simulator</h1>
        <p>Entrenamiento oficial simulado para certificaciones de Salesforce (Kryterion / Webassessor)</p>
    </div>
    """, unsafe_allow_html=True)
    
    exam_files = find_exam_files()
    
    if not exam_files:
        st.warning("⚠️ No se encontraron archivos de examen en la carpeta `/exams` o `./exams`. Por favor añade al menos un archivo `.json` para comenzar.")
        return

    # Create exam selector options
    exam_catalog = {}
    for fpath in exam_files:
        try:
            raw = load_exam_data(fpath)
            title = raw.get("exam_title", fpath.stem)
            q_count = len(raw.get("questions", []))
            exam_catalog[f"{title} ({q_count} preguntas)"] = (fpath, raw)
        except Exception as e:
            st.error(f"Error al leer '{fpath.name}': {e}")
            
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        with st.container(border=True):
            st.subheader("📋 1. Selecciona tu Examen")
            selected_label = st.selectbox(
                "Exámenes disponibles detectados en `/exams`:",
                options=list(exam_catalog.keys())
            )
            
            selected_fpath, selected_raw = exam_catalog[selected_label]
            
            st.divider()
            st.subheader("⚙️ 2. Modo de Práctica")
            
            mode_choice = st.radio(
                "Elige la experiencia de simulación:",
                options=[
                    ("exam", "⏱️ Modo Examen (Simulación Real)", "Temporizador activo, sin respuestas ni explicaciones hasta entregar el examen. Idéntico a Kryterion."),
                    ("study", "🎓 Modo Estudio (Práctica Guiada)", "Sin límite de tiempo. Comprobación y feedback inmediato tras cada respuesta con la explicación oficial.")
                ],
                format_func=lambda x: x[1],
                help="Elige si deseas una prueba cronometrada formal o una sesión de aprendizaje interactiva."
            )
            
            st.caption(mode_choice[2])
            
            st.divider()
            st.subheader("🔀 3. Opciones de Aleatorización")
            c1, c2 = st.columns(2)
            with c1:
                shuffle_questions = st.checkbox("Barajar orden de preguntas", value=True)
            with c2:
                shuffle_options = st.checkbox("Barajar orden de opciones (A/B/C/D)", value=False)
                
            st.divider()
            if st.button("🚀 Comenzar Examen", type="primary", use_container_width=True):
                st.session_state.raw_exam_cache = selected_raw
                st.session_state.shuffle_questions = shuffle_questions
                st.session_state.shuffle_options = shuffle_options
                st.session_state.exam_mode = mode_choice[0]
                restart_same_exam(selected_raw, shuffle_questions, shuffle_options)
                st.rerun()

    with col_right:
        with st.container(border=True):
            st.subheader("ℹ️ Ficha Técnica del Examen")
            raw_data = selected_raw
            questions = raw_data.get("questions", [])
            
            # Extract unique topics
            topics = list(dict.fromkeys([q.get("topic", "General") for q in questions]))
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Preguntas", len(questions))
            m2.metric("Tiempo", f"{raw_data.get('time_limit_minutes', 105)} min")
            m3.metric("Para Aprobar", f"{raw_data.get('passing_score_percent', 65)}%")
            
            st.markdown("#### 🎯 Áreas Temáticas Evaluadas:")
            for t in topics:
                t_count = sum(1 for q in questions if q.get("topic") == t)
                st.markdown(f"- **{t}** (`{t_count}` preguntas)")
                
            st.info("""
            **Consejos de Certificación Salesforce:**
            - Lee con atención si la pregunta pide una opción única o múltiple (**Choose 2** o **Choose 3**).
            - En caso de duda durante el examen, usa la bandera **🚩 Marcar para revisar** y vuelve a ella antes de finalizar.
            """)


# ---------------------------------------------------------
# SCREEN 2: Exam Interface
# ---------------------------------------------------------
def render_exam_screen():
    exam = st.session_state.exam_data
    questions = exam["questions"]
    total_q = len(questions)
    curr_idx = st.session_state.current_q_idx
    q = questions[curr_idx]
    
    # ------------------ SIDEBAR ------------------
    with st.sidebar:
        st.markdown(f"### ⚡ {exam['exam_title']}")
        
        # Dynamic live countdown / elapsed timer
        render_live_timer(
            st.session_state.exam_mode,
            st.session_state.start_time,
            exam["time_limit_minutes"]
        )
            
        st.divider()
        
        # Progress calculation
        answered_count = sum(1 for idx in range(total_q) if len(st.session_state.user_answers.get(idx, [])) > 0)
        progress_val = answered_count / total_q if total_q > 0 else 0.0
        st.write(f"**Progreso:** {answered_count} de {total_q} respondidas ({int(progress_val * 100)}%)")
        st.progress(progress_val)
        
        # Quick Navigation Grid
        st.markdown("#### 🗺️ Matriz de Navegación")
        cols_per_row = 5
        grid_rows = (total_q + cols_per_row - 1) // cols_per_row
        
        for r in range(grid_rows):
            nav_cols = st.columns(cols_per_row)
            for c in range(cols_per_row):
                target_idx = r * cols_per_row + c
                if target_idx < total_q:
                    is_current = (target_idx == curr_idx)
                    is_marked = st.session_state.marked_for_review.get(target_idx, False)
                    is_answered = len(st.session_state.user_answers.get(target_idx, [])) > 0
                    
                    if is_marked:
                        prefix = "🚩"
                    elif is_answered:
                        prefix = "✅"
                    else:
                        prefix = "⚪"
                        
                    btn_label = f"{prefix} {target_idx + 1}"
                    btn_type = "primary" if is_current else "secondary"
                    
                    if nav_cols[c].button(btn_label, key=f"nav_{target_idx}_{st.session_state.session_seed}", type=btn_type, use_container_width=True):
                        st.session_state.current_q_idx = target_idx
                        st.session_state.confirm_finish = False
                        st.rerun()

        st.caption("Leyenda: 🚩 Revisar | ✅ Respondida | ⚪ Sin responder")
        
        st.divider()
        if st.button("🏁 Entregar Examen", type="primary", use_container_width=True):
            st.session_state.confirm_finish = True
            
        if st.button("❌ Salir al Menú Principal", use_container_width=True):
            reset_to_menu()
            st.rerun()

    # ------------------ MAIN CONTENT AREA ------------------
    # Confirmation dialog for finishing
    if st.session_state.confirm_finish:
        with st.container(border=True):
            unanswered = total_q - answered_count
            marked_count = sum(1 for m in st.session_state.marked_for_review.values() if m)
            
            st.warning("### ⚠️ Confirmación de Entrega del Examen")
            st.write(f"- Preguntas respondidas: **{answered_count} / {total_q}**")
            if unanswered > 0:
                st.write(f"- ⚠️ **Preguntas sin responder:** `{unanswered}`")
            if marked_count > 0:
                st.write(f"- 🚩 **Preguntas marcadas para revisión:** `{marked_count}`")
                
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("✅ Sí, finalizar y ver resultados", type="primary", use_container_width=True):
                    st.session_state.end_time = time.time()
                    st.session_state.screen = "results"
                    st.session_state.confirm_finish = False
                    st.rerun()
            with c_no:
                if st.button("↩️ Volver a revisar preguntas", use_container_width=True):
                    st.session_state.confirm_finish = False
                    st.rerun()
        st.divider()

    # Question Header Bar
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown(f"#### Pregunta {curr_idx + 1} de {total_q}")
        st.markdown(f"<span class='badge-pill'>📂 {q.get('topic', 'General')}</span>", unsafe_allow_html=True)
        if q["type"] == "multiple":
            req_count = len(q["correct_answers"])
            st.markdown(f"<span class='badge-pill' style='background-color: #FEF3D6; color: #B25E00;'>Multi-opción (Elige {req_count})</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-pill' style='background-color: #E6F6EC; color: #2E844A;'>Opción Única</span>", unsafe_allow_html=True)
            
    with top_col2:
        is_marked = st.session_state.marked_for_review.get(curr_idx, False)
        new_marked = st.checkbox(
            "🚩 **Marcar para revisar**",
            value=is_marked,
            key=f"review_chk_{curr_idx}_{st.session_state.session_seed}"
        )
        if new_marked != is_marked:
            st.session_state.marked_for_review[curr_idx] = new_marked
            st.rerun()

    # Question Box
    with st.container(border=True):
        st.markdown(f"### {q['question']}")
        st.write("")
        
        current_answers = st.session_state.user_answers.get(curr_idx, [])
        options_dict = q["options"]
        
        # Render Options
        if q["type"] == "single":
            options_keys = list(options_dict.keys())
            
            # Find default index
            default_index = None
            if current_answers and current_answers[0] in options_keys:
                default_index = options_keys.index(current_answers[0])
                
            selected_option = st.radio(
                "Selecciona una respuesta:",
                options=options_keys,
                format_func=lambda k: f"{k}.  {options_dict[k]}",
                index=default_index,
                key=f"radio_{curr_idx}_{st.session_state.session_seed}"
            )
            
            if selected_option:
                st.session_state.user_answers[curr_idx] = [selected_option]
                
        else:  # Multiple choice
            req_count = len(q["correct_answers"])
            st.write(f"**Selecciona exactamente {req_count} respuestas:**")
            
            new_selected = []
            for opt_key, opt_text in options_dict.items():
                checked = st.checkbox(
                    f"**{opt_key}.**  {opt_text}",
                    value=(opt_key in current_answers),
                    key=f"chk_{curr_idx}_{opt_key}_{st.session_state.session_seed}"
                )
                if checked:
                    new_selected.append(opt_key)
            
            st.session_state.user_answers[curr_idx] = sorted(new_selected)
            
            # Validation feedback badge
            sel_count = len(new_selected)
            if sel_count == req_count:
                st.caption(f"✅ Has seleccionado {sel_count} de {req_count} respuestas requeridas.")
            elif sel_count < req_count:
                st.caption(f"⚠️ Seleccionadas: {sel_count}/{req_count}. Debes elegir {req_count - sel_count} más.")
            else:
                st.warning(f"⚠️ Has seleccionado {sel_count} opciones, pero la pregunta requiere exactamente {req_count}. Por favor desmarca {sel_count - req_count}.")

    # ------------------ STUDY MODE IMMEDIATE FEEDBACK ------------------
    if st.session_state.exam_mode == "study":
        show_feedback = st.session_state.study_feedback_shown.get(curr_idx, False)
        c_fb1, c_fb2 = st.columns([1, 4])
        with c_fb1:
            if st.button("💡 " + ("Ocultar Explicación" if show_feedback else "Comprobar Respuesta"), key=f"btn_study_{curr_idx}"):
                st.session_state.study_feedback_shown[curr_idx] = not show_feedback
                st.rerun()
                
        if show_feedback:
            user_ans = set(st.session_state.user_answers.get(curr_idx, []))
            corr_ans = set(q["correct_answers"])
            
            with st.container(border=True):
                if not user_ans:
                    st.info(f"ℹ️ Aún no has seleccionado ninguna opción. La(s) respuesta(s) correcta(s) es/son: **{', '.join(q['correct_answers'])}**")
                elif user_ans == corr_ans:
                    st.success(f"🎉 **¡Correcto!** Respuesta(s) correcta(s): **{', '.join(q['correct_answers'])}**")
                else:
                    st.error(f"❌ **Incorrecto.** Tu respuesta: {', '.join(user_ans) if user_ans else 'Ninguna'}. Correcta(s): **{', '.join(q['correct_answers'])}**")
                    
                st.markdown(f"**📖 Explicación Técnica Oficial:**\n\n{q.get('explanation', 'No disponible.')}")

    st.write("")
    # ------------------ NAVIGATION BUTTONS ------------------
    nav_prev, nav_center, nav_next = st.columns([1, 2, 1])
    
    with nav_prev:
        if st.button("⬅️ Anterior", disabled=(curr_idx == 0), use_container_width=True):
            st.session_state.current_q_idx -= 1
            st.session_state.confirm_finish = False
            st.rerun()
            
    with nav_center:
        st.write("")
        
    with nav_next:
        if curr_idx < total_q - 1:
            if st.button("Siguiente ➡️", type="primary", use_container_width=True):
                st.session_state.current_q_idx += 1
                st.session_state.confirm_finish = False
                st.rerun()
        else:
            if st.button("🏁 Finalizar Examen", type="primary", use_container_width=True):
                st.session_state.confirm_finish = True
                st.rerun()


# ---------------------------------------------------------
# SCREEN 3: Results & Review Screen
# ---------------------------------------------------------
def render_results_screen():
    exam = st.session_state.exam_data
    questions = exam["questions"]
    total_q = len(questions)
    passing_pct = exam.get("passing_score_percent", 65)
    
    # Calculate score
    correct_count = 0
    topic_data = {}
    
    for idx, q in enumerate(questions):
        topic = q.get("topic", "General")
        if topic not in topic_data:
            topic_data[topic] = {"total": 0, "correct": 0}
        topic_data[topic]["total"] += 1
        
        user_ans = set(st.session_state.user_answers.get(idx, []))
        corr_ans = set(q["correct_answers"])
        
        if user_ans and user_ans == corr_ans:
            correct_count += 1
            topic_data[topic]["correct"] += 1

    score_pct = round((correct_count / total_q) * 100, 1) if total_q > 0 else 0
    passed = score_pct >= passing_pct
    
    # Calculate time taken
    total_duration = max(1, int(st.session_state.end_time - st.session_state.start_time)) if st.session_state.end_time > 0 else 0
    dur_mins = total_duration // 60
    dur_secs = total_duration % 60
    
    if passed:
        st.balloons()
        
    # Result Banner
    st.markdown("""
    <div class="main-header">
        <h1>📊 Informe Oficial de Resultados</h1>
        <p>Simulación completada según las pautas de puntuación de Salesforce</p>
    </div>
    """, unsafe_allow_html=True)
    
    c_res, c_stats = st.columns([1, 2], gap="large")
    
    with c_res:
        if passed:
            st.markdown(f"""
            <div class="score-pass">
                <h1 style="color: #155724; font-size: 2.8rem; margin: 0;">APROBADO</h1>
                <h3 style="margin: 0.5rem 0;">¡Enhorabuena! Has superado el examen</h3>
                <p style="font-size: 1.3rem; font-weight: bold; margin: 0;">Puntuación: {score_pct}%</p>
                <p style="margin: 0;">Requerido para aprobar: {passing_pct}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="score-fail">
                <h1 style="color: #721C24; font-size: 2.8rem; margin: 0;">NO APTO</h1>
                <h3 style="margin: 0.5rem 0;">No has alcanzado la puntuación mínima requerida</h3>
                <p style="font-size: 1.3rem; font-weight: bold; margin: 0;">Puntuación: {score_pct}%</p>
                <p style="margin: 0;">Requerido para aprobar: {passing_pct}%</p>
            </div>
            """, unsafe_allow_html=True)
            
    with c_stats:
        with st.container(border=True):
            st.subheader("📈 Resumen Global")
            m1, m2, m3 = st.columns(3)
            m1.metric("Aciertos", f"{correct_count} / {total_q}")
            m2.metric("Porcentaje Final", f"{score_pct}%", f"{round(score_pct - passing_pct, 1)}% vs corte")
            m3.metric("Tiempo Invertido", f"{dur_mins:02d}:{dur_secs:02d} min")
            
            st.divider()
            btn_restart, btn_menu = st.columns(2)
            with btn_restart:
                if st.button("🔄 Repetir este Examen", type="primary", use_container_width=True):
                    restart_same_exam(st.session_state.raw_exam_cache, st.session_state.shuffle_questions, st.session_state.shuffle_options)
                    st.rerun()
            with btn_menu:
                if st.button("🏠 Elegir otro Examen / Menú", use_container_width=True):
                    reset_to_menu()
                    st.rerun()

    st.write("")
    # ------------------ TOPIC BREAKDOWN ------------------
    st.subheader("🎯 Desglose por Área Temática (Section Breakdown)")
    st.caption("Salesforce evalúa el dominio por secciones para orientar tu preparación:")
    
    topic_rows = []
    for t_name, vals in topic_data.items():
        pct = round((vals["correct"] / vals["total"]) * 100, 1) if vals["total"] > 0 else 0
        topic_rows.append({
            "Sección Temática": t_name,
            "Aciertos": f"{vals['correct']} / {vals['total']}",
            "Puntuación (%)": pct,
            "Rendimiento": "✅ Fuerte" if pct >= passing_pct else "⚠️ Requiere Estudio"
        })
        
    df_topics = pd.DataFrame(topic_rows)
    
    col_chart, col_table = st.columns([1, 1], gap="medium")
    with col_chart:
        # Chart using pandas / streamlit
        chart_df = df_topics.set_index("Sección Temática")[["Puntuación (%)"]]
        st.bar_chart(chart_df, color="#0176D3")
        
    with col_table:
        st.dataframe(
            df_topics,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Puntuación (%)": st.column_config.ProgressColumn(
                    "Puntuación (%)",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

    st.divider()
    # ------------------ DETAILED REVIEW ------------------
    st.subheader("🔍 Revisión Detallada de Preguntas")
    
    review_filter = st.radio(
        "Filtrar preguntas:",
        options=["Todas", "Solo Falladas", "Marcadas para Revisar", "Solo Acertadas"],
        horizontal=True
    )
    
    filtered_items = []
    for idx, q in enumerate(questions):
        user_ans = set(st.session_state.user_answers.get(idx, []))
        corr_ans = set(q["correct_answers"])
        is_corr = (user_ans == corr_ans)
        is_marked = st.session_state.marked_for_review.get(idx, False)
        
        if review_filter == "Todas":
            filtered_items.append((idx, q, is_corr, is_marked))
        elif review_filter == "Solo Falladas" and not is_corr:
            filtered_items.append((idx, q, is_corr, is_marked))
        elif review_filter == "Marcadas para Revisar" and is_marked:
            filtered_items.append((idx, q, is_corr, is_marked))
        elif review_filter == "Solo Acertadas" and is_corr:
            filtered_items.append((idx, q, is_corr, is_marked))
            
    if not filtered_items:
        st.info("No hay preguntas que coincidan con el filtro seleccionado.")
    else:
        for idx, q, is_corr, is_marked in filtered_items:
            user_ans = st.session_state.user_answers.get(idx, [])
            corr_ans = q["correct_answers"]
            
            with st.container(border=True):
                # Header
                h_left, h_right = st.columns([3, 1])
                with h_left:
                    status_icon = "✅ Correcta" if is_corr else "❌ Incorrecta"
                    review_tag = " | 🚩 Marcada para Revisión" if is_marked else ""
                    st.markdown(f"**Pregunta {idx + 1}** — `{q['topic']}` — **{status_icon}**{review_tag}")
                with h_right:
                    user_str = ", ".join(user_ans) if user_ans else "Sin responder"
                    corr_str = ", ".join(corr_ans)
                    st.caption(f"Tu resp: **{user_str}** | Correcta: **{corr_str}**")
                    
                st.markdown(f"**{q['question']}**")
                st.write("")
                
                # Display options with visual markers
                for opt_key, opt_text in q["options"].items():
                    is_user_choice = opt_key in user_ans
                    is_correct_choice = opt_key in corr_ans
                    
                    if is_correct_choice and is_user_choice:
                        st.markdown(f"- ✅ **{opt_key}.** {opt_text} *(Tu respuesta correcta)*")
                    elif is_correct_choice and not is_user_choice:
                        st.markdown(f"- 🟢 **{opt_key}.** {opt_text} *(Respuesta correcta omitida)*")
                    elif not is_correct_choice and is_user_choice:
                        st.markdown(f"- ❌ **{opt_key}.** {opt_text} *(Tu respuesta incorrecta)*")
                    else:
                        st.markdown(f"- ⚪ **{opt_key}.** {opt_text}")
                        
                st.write("")
                st.info(f"**📖 Explicación Técnica:**\n\n{q.get('explanation', '')}")


# ---------------------------------------------------------
# Main App Router
# ---------------------------------------------------------
def main():
    if st.session_state.screen == "menu":
        render_menu_screen()
    elif st.session_state.screen == "exam":
        render_exam_screen()
    elif st.session_state.screen == "results":
        render_results_screen()


if __name__ == "__main__":
    main()
