import streamlit as st
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.collection = st.session_state.studyai.collection
    st.session_state.messages = []
    st.session_state.initialized = True

st.title("Settings")

# --- Knowledge Base ---
st.subheader("Knowledge Base")
count = st.session_state.collection.count()
st.write(f"Documents stored: **{count}**")
if st.button("Reset Knowledge Base", type="primary"):
    st.session_state.studyai.chroma_client.reset()
    st.session_state.collection = st.session_state.studyai.chroma_client.get_or_create_collection(
        name="study_stuff",
        embedding_function=st.session_state.studyai.collection._embedding_function
    )
    st.session_state.studyai.collection = st.session_state.collection
    st.success("Knowledge base cleared. Upload new notes in Add Content.")

st.divider()

# --- Saved Artifacts ---
st.subheader("Saved Artifacts")
col1, col2 = st.columns(2)
with col1:
    if st.button("Clear Saved Flashcards"):
        path = "saved_data/flashcards.json"
        if os.path.exists(path):
            os.remove(path)
            st.success("Flashcards cleared.")
        else:
            st.info("No saved flashcards to clear.")
with col2:
    if st.button("Clear Saved Quizzes"):
        path = "saved_data/quizzes.json"
        if os.path.exists(path):
            os.remove(path)
            st.success("Quizzes cleared.")
        else:
            st.info("No saved quizzes to clear.")

st.divider()

# --- Model Settings ---
st.subheader("Model Settings")
chat_model = st.selectbox(
    "Chat model",
    ["llama3.1", "llama3.2", "phi3:mini", "mistral"],
    index=["llama3.1", "llama3.2", "phi3:mini", "mistral"].index(st.session_state.studyai.asking_model)
    if st.session_state.studyai.asking_model in ["llama3.1", "llama3.2", "phi3:mini", "mistral"] else 0
)
if st.button("Apply Model"):
    st.session_state.studyai.asking_model = chat_model
    st.success(f"Chat model set to {chat_model}.")

st.divider()

# --- Session ---
st.subheader("Session")
if st.button("Reset Session State"):
    st.session_state.clear()
    st.rerun()
