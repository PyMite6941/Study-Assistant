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

tab_file, tab_text = st.tabs(["File / Camera", "Type or Paste Text"])

with tab_file:
    source_choice = st.radio("Source:", ["File Upload", "Camera Snapshot"])
    if source_choice == "File Upload":
        file = st.file_uploader("Upload files to process [Image, MD, PDF, or TXT]", type=['png','jpg','jpeg','md','pdf','txt','rst'])
    else:
        file = st.camera_input("Upload an image from the Camera")

    if file:
        with st.status("Processing ...", expanded=True) as status:
            name = getattr(file, "name", "snapshot.png")
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            raw_text = ""
            if ext in ("png", "jpg", "jpeg") or source_choice == "Camera Snapshot":
                img = Image.open(file)
                raw_text = pytesseract.image_to_string(img)
            elif ext == "pdf":
                reader = pypdf.PdfReader(io.BytesIO(file.read()))
                raw_text = " ".join(p.extract_text() for p in reader.pages if p.extract_text())
            elif ext in ("md", "txt", "rst"):
                raw_text = file.read().decode("utf-8")
            else:
                st.error(f"Unsupported file type: {ext}")

            if raw_text:
                chunks = [c.strip() for c in raw_text.split("\n\n") if len(c.strip()) > 20]
                if not chunks:
                    chunks = [raw_text.strip()]
                st.write(f"Extracted {len(chunks)} chunk(s) from **{name}**.")
                if st.button("Commit to memory", key="commit_file"):
                    ids = [str(uuid.uuid4()) for _ in chunks]
                    st.session_state.collection.add(
                        documents=chunks,
                        ids=ids,
                        metadatas=[{"source": name}] * len(chunks)
                    )
                    status.update(label="Memory saved!", state="complete")
                    st.success(f"Added {len(chunks)} chunk(s) to the knowledge base.")

with tab_text:
    st.caption("Type or paste notes, lecture summaries, definitions — anything you want the AI to study from.")
    label = st.text_input("Label (e.g. 'Chapter 4 notes')", placeholder="manual input")
    text_input = st.text_area("Your notes", height=300, placeholder="Paste or type your content here...")
    if st.button("Commit to memory", key="commit_text"):
        if text_input.strip():
            source = label.strip() or "manual input"
            count = st.session_state.studyai.add_text(text_input, source_name=source)
            st.success(f"Added {count} chunk(s) under '{source}'.")
        else:
            st.warning("Nothing to add — the text box is empty.")
