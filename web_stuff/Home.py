# Modules for properly importing stuff
import os
import sys
# Module to create a streamlit UI
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

st.title("Home")

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.collection = []
    st.session_state.messages = []
    st.session_state.processed_files = []
    st.session_state.initialized = True

home_page = st.Page("Home.py",title="Home",default=True)
upload_page = st.Page("Add Content.py",title="Add Content")
chat_page = st.Page("Chat.py",title="Chat")
description_page = st.Page("Description.py",title="Description")
st.sidebar.text("Hack America 2026")
pg = st.navigation([home_page,upload_page,chat_page,description_page])
st.sidebar.divider()
pg.run()