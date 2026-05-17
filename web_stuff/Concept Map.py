import streamlit as st
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.initialized = True

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

st.title("Concept Map")

if st.session_state.studyai.collection.count() == 0:
    st.warning("Your knowledge base is empty. Go to **Add Content** to upload notes first.")
    st.stop()

topic = st.text_input("What topic should the concept map cover?")

if st.button("Generate Map", disabled=not topic):
    with st.spinner("Building concept map..."):
        triples = st.session_state.studyai.create_concept_map(topic)
    if triples:
        st.graphviz_chart(_triples_to_dot(triples))
        with st.expander("Raw relationships"):
            for t in triples:
                if len(t) == 3:
                    st.write(f"**{t[0]}** → {t[1]} → **{t[2]}**")
    else:
        st.warning("Could not extract concepts. Try a more specific topic or add more notes.")
