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

st.title("Artifacts")

tab_flash, tab_quiz, tab_study_plans, tab_concept_maps = st.tabs(["Flashcards", "Quizzes", "Study Plans", "Concept Maps"])

with tab_flash:
    flashcards = st.session_state.studyai.load_flashcards()
    if not flashcards:
        st.info("No saved flashcards yet. Generate some in Chat and hit 'Save to study later'.")
    else:
        st.write(f"{len(flashcards)} flashcard(s) saved.")
        st.table(flashcards)

with tab_quiz:
    quizzes = st.session_state.studyai.load_quizzes()
    if not quizzes:
        st.info("No saved quizzes yet.")
    else:
        st.write(f"{len(quizzes)} quiz question(s) saved.")
        for i, q in enumerate(quizzes):
            with st.expander(f"Question {i + 1}"):
                st.markdown(q.get("question", ""))
                st.markdown(f"**Answer:** {q.get('answer', '')}")

with tab_study_plans:
    plans = st.session_state.studyai.load_study_plans()
    if not plans:
        st.info("No saved study plans yet.")
    else:
        st.write(f"{len(plans)} study plan(s) saved.")
        for i, p in enumerate(plans):
            with st.expander(f"{p.get('topic','Plan')} — {p.get('days','')} days (created {p.get('created','')})"):
                for day_info in p.get('plan',[]):
                    st.markdown(f"**Day {day_info['day']}: {day_info.get('focus','')}**")
                    for task in day_info.get('tasks',[]):
                        st.write(f"• {task}")

with tab_concept_maps:
    maps = st.session_state.studyai.load_concept_maps()
    if not maps:
        st.info("No saved concept maps yet.")
    else:
        st.write(f"{len(maps)} concept map(s) saved.")
        for i, m in enumerate(maps):
            with st.expander(f"Concept Map {i + 1}"):
                dot = m.get("dot", "")
                st.graphviz_chart(dot)