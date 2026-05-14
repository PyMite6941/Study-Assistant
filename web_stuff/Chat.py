# Module to create a streamlit UI
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

st.title("Chat with your notes")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.collection.count() == 0:
    st.warning("Your knowledge base is empty. Go to **Add Content** to upload your notes first.")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message['sources']:
                    st.info(source)

prompt = st.chat_input("What can I do to help?")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.status("Searching for results ...",expanded=False) as status:
        msg_type,data = st.session_state.studyai.designate_function(prompt)
        status.update(label="Done!",state="complete")
    with st.chat_message("assistant"):    
        if msg_type == 'quiz':
            st.write("Time for a challenge!")
            st.table(data)
        elif msg_type == 'flashcards':
            st.write("Some flashcards on the topic:")
            st.table(data)
        else:
            st.markdown(data)
    st.session_state.messages.append({'role':'assistant','content':data})