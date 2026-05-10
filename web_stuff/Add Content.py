# Module to create a streamlit UI
import streamlit as st
# Modules to process files
from PIL import Image
import pytesseract
import numpy as np
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

if st.sidebar.button("Hard Reset AI"):
    st.session_state.clear()
    st.rerun()

st.title("Add content")

source_choice = st.radio("Source:",["File Upload","Camera Snapshot"])
if source_choice == "File Upload":
    file = st.file_uploader("Upload files to process [Image, MD, or PDF]",type=['png','jpg','md','pdf'])
elif source_choice == "Camera Snapshot":
    file = st.camera_input("Upload an image from the Camera")

if file:
    with st.status("Processing ...",expanded=True) as status:
        img = Image.open(file)
        raw_text = pytesseract.image_to_string(img)
        chunks = [c.strip() for c in raw_text.split("\n\n") if len(c.strip())> 20]
        if st.button("Commit to memory"):
            ids = [f"id_{i}" for i in range(len(chunks))]
            st.session_state.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=[{"source":file.name}]*len(chunks)
            )
            status.update(label="Memory saved!",status="complete")
            st.success(f"Added {len(chunks)} to the Study Assistant.")