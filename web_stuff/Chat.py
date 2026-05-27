import streamlit as st
import re
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

def _triples_to_dot(triples):
    dot = "digraph {\n  rankdir=LR;\n  node [shape=box style=rounded];\n"
    for triple in triples:
        if len(triple) == 3:
            a = triple[0].replace('"', "'")
            rel = triple[1].replace('"', "'")
            b = triple[2].replace('"', "'")
            dot += f'  "{a}" -> "{b}" [label="{rel}"];\n'
    dot += "}"
    return dot

def _award_xp(ai, amount, streak=1):
    prev_level = ai.get_level_info()['level']
    xp = ai.calculate_xp(amount, streak, 0)
    ai.update_streak()
    new_info = ai.get_level_info()
    leveled_up = new_info['level'] > prev_level
    return xp, new_info, leveled_up

def _show_xp_result(xp, new_info, leveled_up, prefix=""):
    if leveled_up:
        st.balloons()
        st.success(f"{prefix}+{xp} XP — Level up! You're now **Lv.{new_info['level']} — {new_info['title']}**!")
    else:
        st.success(f"{prefix}+{xp} XP")

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.collection = st.session_state.studyai.collection
    st.session_state.messages = []
    st.session_state.processed_files = []
    st.session_state.current_quiz = None
    st.session_state.current_quiz_topic = ""
    st.session_state.user_submitted = False
    st.session_state.quiz_result = None
    st.session_state.pending_flashcards = None
    st.session_state.initialized = True

# Add any missing keys for sessions that initialized before these were added
for _key, _default in [
    ("current_quiz_topic", ""),
    ("quiz_result", None),
    ("pending_flashcards", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

st.title("Chat with your notes")

if "messages" not in st.session_state:
    st.session_state.messages = []

ai = st.session_state.studyai
st.caption(f"Using **{ai._provider}** — {ai.asking_model}")

chat_ready, chat_msg = ai.check_chat_ready()
if not chat_ready:
    st.error(f"Chat unavailable: {chat_msg}")
    st.stop()

if st.session_state.collection.count() == 0:
    st.warning("Your knowledge base is empty. Go to **Add Content** to upload your notes first.")
    st.stop()

# ── Chat history ──────────────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message['sources']:
                    st.info(source)

# ── Persistent quiz widget (outside if prompt so it survives reruns) ──────────
if st.session_state.current_quiz:
    quiz = st.session_state.current_quiz
    with st.container(border=True):
        if not st.session_state.user_submitted:
            st.markdown("**🎯 Answer the question:**")
            st.markdown(quiz['question'])
            answer = st.radio("Your answer:", ["A", "B", "C", "D"], index=None, key="chat_quiz_radio")
            col_sub, col_save = st.columns(2)
            with col_sub:
                if st.button("Submit answer", key="chat_quiz_submit", type="primary"):
                    if answer:
                        correct = answer == quiz['answer']
                        ai.save_stats(st.session_state.current_quiz_topic, correct=correct)
                        base_xp = 15 if correct else 2
                        xp, new_info, leveled_up = _award_xp(ai, base_xp)
                        st.session_state.quiz_result = {
                            "correct": correct,
                            "answer": quiz['answer'],
                            "xp": xp,
                            "new_info": new_info,
                            "leveled_up": leveled_up,
                        }
                        st.session_state.user_submitted = True
                        st.rerun()
            with col_save:
                if st.button("Save for later", key="chat_quiz_save"):
                    ai.save_quizzes(quiz)
                    xp, new_info, leveled_up = _award_xp(ai, 10)
                    _show_xp_result(xp, new_info, leveled_up, prefix="Saved! ")
        else:
            result = st.session_state.quiz_result
            if result['correct']:
                st.success(f"Correct! +{result['xp']} XP")
            else:
                st.error(f"Wrong — answer was **{result['answer']}** | +{result['xp']} XP")
            if result.get('leveled_up'):
                lvl = result['new_info']
                st.balloons()
                st.info(f"Level up! You're now **Lv.{lvl['level']} — {lvl['title']}**!")
            col_next, col_save2 = st.columns(2)
            with col_next:
                if st.button("Dismiss", key="chat_quiz_dismiss"):
                    st.session_state.current_quiz = None
                    st.session_state.user_submitted = False
                    st.session_state.quiz_result = None
                    st.rerun()
            with col_save2:
                if st.button("Save question", key="chat_quiz_save_after"):
                    ai.save_quizzes(quiz)
                    xp, new_info, leveled_up = _award_xp(ai, 10)
                    _show_xp_result(xp, new_info, leveled_up, prefix="Saved! ")

# ── Persistent flashcard save widget ─────────────────────────────────────────
if st.session_state.pending_flashcards:
    cards = st.session_state.pending_flashcards
    with st.container(border=True):
        st.markdown(f"**{len(cards)} flashcard(s) ready**")
        st.table(cards)
        col_sv, col_dis = st.columns(2)
        with col_sv:
            if st.button("Save flashcards", key="chat_fc_save", type="primary"):
                ai.save_flashcards(cards)
                xp, new_info, leveled_up = _award_xp(ai, 25)
                _show_xp_result(xp, new_info, leveled_up, prefix="Saved! ")
                st.session_state.pending_flashcards = None
                st.rerun()
        with col_dis:
            if st.button("Dismiss", key="chat_fc_dismiss"):
                st.session_state.pending_flashcards = None
                st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
prompt = st.chat_input("What can I do to help?")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    saved_text = ""
    sources = []
    try:
        with st.spinner("Thinking..."):
            msg_type, data, sources = ai.designate_function(prompt, stream=False)
        with st.chat_message("assistant"):
            if msg_type == 'quiz':
                if isinstance(data, str):
                    st.warning(data)
                    saved_text = data
                else:
                    st.write("Here's your question — answer below!")
                    topic = ai._clean_topic(re.sub(r'(quiz me on|create quiz|generate quiz|make quiz)', '', prompt, flags=re.IGNORECASE).strip())
                    st.session_state.current_quiz = data
                    st.session_state.current_quiz_topic = topic
                    st.session_state.user_submitted = False
                    st.session_state.quiz_result = None
                    saved_text = str(data)
            elif msg_type == 'flashcards':
                if isinstance(data, str):
                    st.warning(data)
                    saved_text = data
                else:
                    st.write(f"Generated {len(data)} flashcard(s) — save them below!")
                    st.session_state.pending_flashcards = data
                    saved_text = str(data)
            elif msg_type == 'study_plan':
                if data:
                    st.write(f"Study plan for **{data['topic']}** — {data['days']} days")
                    for day_info in data['plan']:
                        with st.expander(f"Day {day_info['day']}: {day_info.get('focus', '')}"):
                            for task in day_info.get('tasks', []):
                                st.checkbox(task, key=f"plan_{day_info['day']}_{task}")
                    if st.button("Save plan"):
                        ai.save_study_plan(data)
                        st.success("Plan saved!")
                else:
                    st.warning("Could not generate a study plan. Try adding more notes on this topic first.")
                saved_text = str(data)
            elif msg_type == 'concept_map':
                if data:
                    st.write("Concept map:")
                    st.graphviz_chart(_triples_to_dot(data))
                    if st.button("Save map"):
                        ai.save_concept_map({"dot": _triples_to_dot(data)})
                        st.success("Concept map saved!")
                else:
                    st.warning("Could not generate a concept map. Try adding more notes on this topic first.")
                saved_text = str(data)
            elif msg_type == 'video':
                if data:
                    st.write("Videos found:")
                    for item in data:
                        st.markdown(f"[{item['title']}]({item['url']})")
                else:
                    st.warning("No videos found. Try a different search term.")
                saved_text = str(data)
            else:
                st.markdown(data)
                saved_text = data or ""
            if sources:
                with st.expander("View sources"):
                    for s in sources:
                        st.info(s)
    except Exception as e:
        import traceback
        with st.chat_message("assistant"):
            st.error(f"**Error:** {e}")
            st.code(traceback.format_exc())
        saved_text = f"[Error: {e}]"
    st.session_state.messages.append({'role': 'assistant', 'content': saved_text})
