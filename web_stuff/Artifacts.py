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
if "level_up_info" not in st.session_state:
    st.session_state.level_up_info = None

ai = st.session_state.studyai

# Load all data once — reused across all tabs to avoid redundant file reads
flashcards = ai.load_flashcards()
quizzes    = ai.load_quizzes()
plans      = ai.load_study_plans()
maps       = ai.load_concept_maps()
stats      = ai.load_stats()
streak_data = ai.get_streak()
xp_info    = ai.get_level_info()

st.title("Artifacts")

# Level-up banner (survives rerun via session state)
if st.session_state.level_up_info:
    lvl = st.session_state.level_up_info
    st.balloons()
    st.success(f"Level up! You're now **Lv.{lvl['level']} — {lvl['title']}**!")
    st.session_state.level_up_info = None

tab_flash, tab_quiz, tab_study_plans, tab_concept_maps, tab_stats = st.tabs(
    ["Flashcards", "Quizzes", "Study Plans", "Concept Maps", "Stats"]
)

# ── FLASHCARDS ────────────────────────────────────────────────────────────────
with tab_flash:
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
                    prev_level = ai.get_level_info()['level']
                    new_streak = streak + 1
                    earned = ai.calculate_xp(15, new_streak, 0)
                    ai.update_streak()
                    new_info = ai.get_level_info()
                    if new_info['level'] > prev_level:
                        st.session_state.level_up_info = new_info
                    st.session_state.fc_streak = new_streak
                    st.session_state.fc_session_xp += earned
                    st.session_state.fc_idx = (idx + 1) % total
                    st.session_state.fc_revealed = False
                    st.rerun()
            with col_missed:
                if st.button("Missed it ✗  (+2 XP)", use_container_width=True):
                    earned = ai.calculate_xp(2, 0, 0)
                    ai.update_streak()
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
                        prev_level = ai.get_level_info()['level']
                        xp = ai.calculate_xp(15, 1, 0) if correct else ai.calculate_xp(2, 0, 0)
                        ai.update_streak()
                        new_info = ai.get_level_info()
                        if new_info['level'] > prev_level:
                            st.session_state.level_up_info = new_info
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
    if not maps:
        st.info("No saved concept maps yet.")
    else:
        st.write(f"{len(maps)} concept map(s) saved.")
        for i, m in enumerate(maps):
            with st.expander(f"Concept Map {i + 1}"):
                st.graphviz_chart(m.get("dot", ""))

# ── STATS ─────────────────────────────────────────────────────────────────────
with tab_stats:
    total_q = stats.get("total_questions", 0)
    correct = stats.get("correct", 0)
    accuracy = round(correct / total_q * 100) if total_q > 0 else 0

    st.subheader("Overall Progress")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total XP", xp_info['xp'])
    c2.metric("Level", f"{xp_info['level']} — {xp_info['title']}")
    c3.metric("🔥 Day Streak", streak_data['streak'])
    c4.metric("Quiz Accuracy", f"{accuracy}%")

    st.markdown(f"**{correct} correct** out of **{total_q} questions answered**")
    if xp_info['xp_to_next'] > 0:
        st.progress(xp_info['progress'], text=f"{xp_info['xp_to_next']} XP to Level {xp_info['level'] + 1} ({xp_info['title']} → {['','Apprentice','Scholar','Expert','Master','Legend'][xp_info['level']]})")
    else:
        st.progress(1.0, text="Max Level — Legend!")

    by_topic = stats.get("by_topic", {})
    if by_topic:
        st.subheader("By Topic")
        rows = []
        for topic, data in by_topic.items():
            t_total = data.get("total", 0)
            t_correct = data.get("correct", 0)
            t_acc = round(t_correct / t_total * 100) if t_total > 0 else 0
            rows.append({"Topic": topic, "Questions": t_total, "Correct": t_correct, "Accuracy": f"{t_acc}%"})
        rows.sort(key=lambda r: r["Questions"], reverse=True)
        st.table(rows)
    else:
        st.info("Answer some quizzes in Chat or here to see topic breakdown.")

    fc_count = len(flashcards)
    qz_count = len(quizzes)
    st.subheader("Saved Content")
    col_fc, col_qz = st.columns(2)
    col_fc.metric("Flashcards saved", fc_count)
    col_qz.metric("Quiz questions saved", qz_count)
