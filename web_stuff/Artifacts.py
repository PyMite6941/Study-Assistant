import streamlit as st
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.collection = st.session_state.studyai.collection
    st.session_state.messages = []
    st.session_state.processed_files = []
    st.session_state.current_quiz = None
    st.session_state.user_submitted = False
    st.session_state.initialized = True

if "fc_idx" not in st.session_state:
    st.session_state.fc_idx = 0
if "fc_revealed" not in st.session_state:
    st.session_state.fc_revealed = False
if "fc_streak" not in st.session_state:
    st.session_state.fc_streak = 0
if "fc_session_xp" not in st.session_state:
    st.session_state.fc_session_xp = 0
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {}

ai = st.session_state.studyai

st.title("Artifacts")

tab_flash, tab_quiz, tab_study_plans, tab_concept_maps = st.tabs(
    ["Flashcards", "Quizzes", "Study Plans", "Concept Maps"]
)

# ── FLASHCARDS ────────────────────────────────────────────────────────────────
with tab_flash:
    flashcards = ai.load_flashcards()
    if not flashcards:
        st.info("No saved flashcards yet. Generate some in Chat and hit 'Save to study later'.")
    else:
        total = len(flashcards)
        if st.session_state.fc_idx >= total:
            st.session_state.fc_idx = 0

        idx = st.session_state.fc_idx
        card = flashcards[idx]
        streak = st.session_state.fc_streak

        col_cards, col_streak, col_xp = st.columns(3)
        col_cards.metric("Card", f"{idx + 1} / {total}")
        col_streak.metric("Streak 🔥", streak)
        col_xp.metric("Session XP", f"+{st.session_state.fc_session_xp}")

        st.progress((idx + 1) / total)

        with st.container(border=True):
            st.markdown(f"### {card['Question']}")
            if st.session_state.fc_revealed:
                st.divider()
                st.markdown(f"**{card['Answer']}**")

        if not st.session_state.fc_revealed:
            if st.button("Reveal Answer", use_container_width=True, type="primary"):
                st.session_state.fc_revealed = True
                st.rerun()
        else:
            xp_preview = 15 * (streak + 1)
            col_knew, col_missed = st.columns(2)
            with col_knew:
                if st.button(f"I knew it ✓  (+{xp_preview} XP)", use_container_width=True, type="primary"):
                    new_streak = streak + 1
                    earned = ai.calculate_xp(15, new_streak, 0)
                    st.session_state.fc_streak = new_streak
                    st.session_state.fc_session_xp += earned
                    st.session_state.fc_idx = (idx + 1) % total
                    st.session_state.fc_revealed = False
                    st.rerun()
            with col_missed:
                if st.button("Missed it ✗  (+2 XP)", use_container_width=True):
                    earned = ai.calculate_xp(2, 0, 0)
                    st.session_state.fc_streak = 0
                    st.session_state.fc_session_xp += earned
                    st.session_state.fc_idx = (idx + 1) % total
                    st.session_state.fc_revealed = False
                    st.rerun()

        col_prev, _, col_next = st.columns([1, 6, 1])
        with col_prev:
            if st.button("◀", use_container_width=True):
                st.session_state.fc_idx = (idx - 1) % total
                st.session_state.fc_revealed = False
                st.rerun()
        with col_next:
            if st.button("▶", use_container_width=True):
                st.session_state.fc_idx = (idx + 1) % total
                st.session_state.fc_revealed = False
                st.rerun()

# ── QUIZZES ───────────────────────────────────────────────────────────────────
with tab_quiz:
    quizzes = ai.load_quizzes()
    if not quizzes:
        st.info("No saved quizzes yet. Generate one in Chat and save it.")
    else:
        answered = sum(1 for v in st.session_state.quiz_state.values() if v.get("submitted"))
        correct_count = sum(1 for v in st.session_state.quiz_state.values() if v.get("submitted") and v.get("correct"))
        session_xp = sum(v.get("xp", 0) for v in st.session_state.quiz_state.values() if v.get("submitted"))

        col_q, col_c, col_xp = st.columns(3)
        col_q.metric("Answered", f"{answered} / {len(quizzes)}")
        col_c.metric("Correct ✓", correct_count)
        col_xp.metric("Session XP", f"+{session_xp}")

        if answered > 0 and answered == len(quizzes):
            pct = round(correct_count / len(quizzes) * 100)
            st.success(f"All done! Score: {correct_count}/{len(quizzes)} ({pct}%)")

        st.divider()

        for i, q in enumerate(quizzes):
            q_state = st.session_state.quiz_state.get(i, {})
            submitted = q_state.get("submitted", False)

            label = f"Q{i + 1}"
            if submitted:
                label += " ✓" if q_state.get("correct") else " ✗"

            with st.expander(label, expanded=not submitted):
                st.markdown(q.get("question", ""))
                if not submitted:
                    answer = st.radio("Your answer:", ["A", "B", "C", "D"], index=None, key=f"aq_{i}")
                    if st.button("Submit", key=f"aqs_{i}") and answer:
                        correct = answer == q.get("answer", "")
                        xp = ai.calculate_xp(15, 1, 0) if correct else ai.calculate_xp(2, 0, 0)
                        st.session_state.quiz_state[i] = {
                            "submitted": True,
                            "user_answer": answer,
                            "correct": correct,
                            "xp": xp,
                        }
                        st.rerun()
                else:
                    if q_state.get("correct"):
                        st.success(f"Correct! +{q_state['xp']} XP")
                    else:
                        st.error(f"Wrong — answer was **{q.get('answer', '')}** | +{q_state['xp']} XP")

# ── STUDY PLANS ───────────────────────────────────────────────────────────────
with tab_study_plans:
    plans = ai.load_study_plans()
    if not plans:
        st.info("No saved study plans yet.")
    else:
        st.write(f"{len(plans)} study plan(s) saved.")
        for i, p in enumerate(plans):
            with st.expander(f"{p.get('topic', 'Plan')} — {p.get('days', '')} days (created {p.get('created', '')})"):
                for day_info in p.get("plan", []):
                    st.markdown(f"**Day {day_info['day']}: {day_info.get('focus', '')}**")
                    for task in day_info.get("tasks", []):
                        st.write(f"• {task}")

# ── CONCEPT MAPS ──────────────────────────────────────────────────────────────
with tab_concept_maps:
    maps = ai.load_concept_maps()
    if not maps:
        st.info("No saved concept maps yet.")
    else:
        st.write(f"{len(maps)} concept map(s) saved.")
        for i, m in enumerate(maps):
            with st.expander(f"Concept Map {i + 1}"):
                st.graphviz_chart(m.get("dot", ""))
