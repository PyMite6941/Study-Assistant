# Module for properly importing stuff
import streamlit as st
# Modules for using the Study Assistant
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

upload_page = st.Page("Add Content.py", title="Add Content")
chat_page = st.Page("Chat.py", title="Chat")
description_page = st.Page("Description.py", title="Description",default=True)
artifacts_page = st.Page("Artifacts.py", title="Artifacts")
settings_page = st.Page("Settings.py", title="Settings")
st.sidebar.text("Hack America 2026")
pg = st.navigation([upload_page, chat_page, artifacts_page, description_page, settings_page])
st.sidebar.divider()
pg.run()