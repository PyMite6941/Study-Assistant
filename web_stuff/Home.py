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
study_plan_page = st.Page("Study Plan.py", title="Study Plan")
concept_map_page = st.Page("Concept Map.py", title="Concept Map")
settings_page = st.Page("Settings.py", title="Settings")

pg = st.navigation([description_page, upload_page, chat_page, artifacts_page, study_plan_page, concept_map_page, settings_page])

info = st.session_state.studyai.get_level_info()
st.sidebar.markdown(f"**Lv.{info['level']} — {info['title']}**")
st.sidebar.metric("Total XP", info['xp'])
if info['xp_to_next'] > 0:
    st.sidebar.progress(info['progress'], text=f"{info['xp_to_next']} XP to Level {info['level'] + 1}")
else:
    st.sidebar.progress(1.0, text="Max Level!")
st.sidebar.divider()
st.sidebar.caption("HackMars 3.0")

pg.run()