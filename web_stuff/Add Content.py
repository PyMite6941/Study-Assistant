# Module to create a streamlit UI
import streamlit as st
# Modules to process files
from PIL import Image
import pytesseract
import pypdf
import io
import uuid
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

st.title("Add content")

source_choice = st.radio("Source:",["File Upload","Camera Snapshot"])
if source_choice == "File Upload":
    file = st.file_uploader("Upload files to process [Image, MD, or PDF]",type=['png','jpg','md','pdf'])
elif source_choice == "Camera Snapshot":
    file = st.camera_input("Upload an image from the Camera")

if file:
    with st.status("Processing ...",expanded=True) as status:
        name = getattr(file, "name", "snapshot.png")
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext in ("png", "jpg", "jpeg") or source_choice == "Camera Snapshot":
            img = Image.open(file)
            raw_text = pytesseract.image_to_string(img)
        elif ext == "pdf":
            reader = pypdf.PdfReader(io.BytesIO(file.read()))
            raw_text = " ".join(p.extract_text() for p in reader.pages if p.extract_text())
        elif ext == "md":
            raw_text = file.read().decode("utf-8")
        else:
            st.error(f"Unsupported file type: {ext}")
            raw_text = ""
        chunks = [c.strip() for c in raw_text.split("\n\n") if len(c.strip()) > 20]
        if chunks and st.button("Commit to memory"):
            ids = [str(uuid.uuid4()) for _ in chunks]
            st.session_state.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=[{"source": name}] * len(chunks)
            )
            status.update(label="Memory saved!",state="complete")
            st.success(f"Added {len(chunks)} chunks to the Study Assistant.")