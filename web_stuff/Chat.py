# Module to create a streamlit UI
import streamlit as st

st.title("Chat with your notes")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message['sources']:
                    st.info(source)

prompt = st.chat_input("What would you like to know?")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message("assistant"):
        with st.spinner("Searching for results ..."):
            results = st.session_state.collection.query(query_texts=[prompt],n_results=5)
            context_chunks = results['documents'][0]
            source_metadata = results['metadatas'][0]