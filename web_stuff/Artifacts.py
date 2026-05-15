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

tab_flash, tab_quiz = st.tabs(["Flashcards", "Quizzes"])

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
