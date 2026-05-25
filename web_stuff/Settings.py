import streamlit as st
import os
import sys
import shutil
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

# --- Config / API Keys ---
st.subheader("Configuration")
config = st.session_state.studyai.load_config()

with st.expander("API Keys", expanded=False):
    st.caption("Leave blank to use Ollama locally.")
    groq    = st.text_input("Groq API Key",    value=config["api_keys"].get("groq",""),    type="password")
    openai  = st.text_input("OpenAI API Key",  value=config["api_keys"].get("openai",""),  type="password")
    gemini  = st.text_input("Gemini API Key",  value=config["api_keys"].get("gemini",""),  type="password")
    anthropic = st.text_input("Anthropic API Key", value=config["api_keys"].get("anthropic",""), type="password")

with st.expander("Model Settings", expanded=False):
    provider = st.selectbox("Provider", ["ollama","groq","openai","gemini","anthropic"],
        index=["ollama","groq","openai","gemini","anthropic"].index(config["models"].get("provider","ollama")))
    chat_model = st.text_input("Chat model", value=config["models"].get("chat_model","llama3.1"))
    embedding_model = st.text_input("Embedding model", value=config["models"].get("embedding_model","nomic-embed-text"))

current_provider = config["models"].get("provider","ollama")
if provider != current_provider:
    st.warning("Switching providers changes the embedding model. **Reset your Knowledge Base** after saving to avoid dimension mismatch errors.")

if st.button("Save Configuration", type="primary"):
    config["api_keys"]["groq"] = groq
    config["api_keys"]["openai"] = openai
    config["api_keys"]["gemini"] = gemini
    config["api_keys"]["anthropic"] = anthropic
    config["models"]["provider"] = provider
    config["models"]["chat_model"] = chat_model
    config["models"]["embedding_model"] = embedding_model
    st.session_state.studyai.save_config(config)
    st.session_state.studyai.asking_model = chat_model
    st.success("Configuration saved.")

st.divider()

# --- Session ---
st.subheader("Session")

col_a, col_b = st.columns(2)
with col_a:
    if st.button("Clear Cache"):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        deleted = 0
        for dirpath, dirnames, _ in os.walk(root):
            for d in dirnames:
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
                    deleted += 1
        st.session_state.clear()
        st.success(f"Cleared {deleted} __pycache__ folder(s) and reset session state.")
        st.rerun()
with col_b:
    if st.button("Reset Session State"):
        st.session_state.clear()
        st.rerun()

st.divider()

# --- Updates ---
st.subheader("Updates")
st.caption(f"Current version: **{st.session_state.studyai.__version__}**")
if st.button("Check for Updates"):
    with st.spinner("Checking..."):
        st.session_state.update_info = st.session_state.studyai._check_for_updates()

if "update_info" in st.session_state:
    info = st.session_state.update_info
    if info["error"]:
        st.error(f"Could not check: {info['error']}")
    elif info["up_to_date"]:
        st.success(f"You're up to date ({info['current']}).")
    else:
        st.warning(f"Update available: {info['latest']} (you have {info['current']})")
        if st.button("Update Now"):
            with st.spinner("Pulling latest version..."):
                msg = st.session_state.studyai.update_program()
            st.info(msg)
            del st.session_state.update_info
