# Module to create a streamlit UI
import streamlit as st
import re
# Modules for using the Study Assistant
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

def _triples_to_dot(triples):
    dot = "digraph {\n  rankdir=LR;\n  node [shape=box style=rounded];\n"
    for triple in triples:
        if len(triple) == 3:
            a = triple[0].replace('"',"'")
            rel = triple[1].replace('"',"'")
            b = triple[2].replace('"',"'")
            dot += f'  "{a}" -> "{b}" [label="{rel}"];\n'
    dot += "}"
    return dot

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

chat_ready, chat_msg = st.session_state.studyai.check_chat_ready()
if not chat_ready:
    st.error(f"Chat unavailable: {chat_msg}")
    st.stop()

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
    msg_type, data, sources = st.session_state.studyai.designate_function(prompt,stream=True)
    with st.chat_message("assistant"):
        if msg_type == 'quiz':
            st.write("Time for a challenge!")
            st.markdown(data['question'])
            st.session_state.current_quiz = data
            answer = st.radio("Your answer:",["A","B","C","D"],index=None,key=f"quiz_{len(st.session_state.messages)}")
            if st.button("Submit answer") and answer:
                correct = answer == data['answer']
                topic = st.session_state.studyai._clean_topic(re.sub(r'(quiz me on|create quiz|generate quiz|make quiz)','',prompt,flags=re.IGNORECASE).strip())
                st.session_state.studyai.save_stats(topic,correct=correct)
                if correct:
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect — the answer was {data['answer']}")
            if st.button("Save to study later"):
                st.session_state.studyai.save_quizzes(data)
                st.success("Saved the question to review later")
            saved_text = str(data)
        elif msg_type == 'flashcards':
            st.write("Here are your flashcards:")
            st.table(data)
            if st.button("Save to study later"):
                st.session_state.studyai.save_flashcards(data)
                st.success("Saved flashcards to review later")
            saved_text = str(data)
        elif msg_type == 'study_plan':
            if data:
                st.write(f"Study plan for **{data['topic']}** — {data['days']} days")
                for day_info in data['plan']:
                    with st.expander(f"Day {day_info['day']}: {day_info.get('focus','')}"):
                        for task in day_info.get('tasks',[]):
                            st.checkbox(task,key=f"plan_{day_info['day']}_{task}")
                if st.button("Save plan"):
                    st.session_state.studyai.save_study_plan(data)
                    st.success("Plan saved!")
            else:
                st.warning("Could not generate a study plan. Try adding more notes on this topic first.")
            saved_text = str(data)
        elif msg_type == 'concept_map':
            if data:
                st.write("Concept map:")
                st.graphviz_chart(_triples_to_dot(data))
                if st.button("Save map"):
                    st.session_state.studyai.save_concept_map({"dot":_triples_to_dot(data)})
                    st.success("Concept map saved!")
            else:
                st.warning("Could not generate a concept map. Try adding more notes on this topic first.")
            saved_text = str(data)
        else:
            if msg_type == 'chat_stream':
                saved_text = st.write_stream(data)
            else:
                st.markdown(data)
                saved_text = data
        if sources:
            with st.expander("View sources"):
                for s in sources:
                    st.info(s)
    st.session_state.messages.append({'role':'assistant','content':saved_text})