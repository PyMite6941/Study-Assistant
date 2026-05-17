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

# --- diagnostics (remove once working) ---
ai = st.session_state.studyai
st.caption(f"Provider: `{ai._provider}` | Model: `{ai.asking_model}` | Base: `{ai._api_base}` | Docs: `{ai.collection.count()}`")
if st.button("Test API connection", key="test_api"):
    import traceback, requests as _req
    url = f"{ai._api_base}/chat/completions"
    st.write(f"URL: `{url}`")
    headers = {"Authorization": f"Bearer {ai._api_key[:8]}...", "Content-Type": "application/json"}
    payload = {"model": ai.asking_model, "messages": [{"role":"user","content":"Say hi."}], "max_tokens": 64}
    st.json({"model": payload["model"], "url": url})
    try:
        r = _req.post(url,
                      json=payload,
                      headers={"Authorization": f"Bearer {ai._api_key}", "Content-Type": "application/json"},
                      timeout=30)
        st.write(f"Status: `{r.status_code}`")
        st.code(r.text[:2000])
    except Exception as e:
        st.error(f"**{type(e).__name__}:** {e}")
        st.code(traceback.format_exc())
# --- end diagnostics ---

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
    saved_text = ""
    sources = []
    try:
        with st.spinner("Thinking..."):
            msg_type, data, sources = st.session_state.studyai.designate_function(prompt, stream=False)
        with st.chat_message("assistant"):
            if msg_type == 'quiz':
                if isinstance(data, str):
                    st.warning(data)
                    saved_text = data
                else:
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
                if isinstance(data, str):
                    st.warning(data)
                    saved_text = data
                else:
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
            elif msg_type == 'video':
                if data:
                    st.write("Videos found:")
                    for item in data:
                        st.markdown(f"[{item['title']}]({item['url']})")
                else:
                    st.warning("No videos found. Try a different search term.")
                saved_text = str(data)
            else:
                st.markdown(data)
                saved_text = data or ""
            if sources:
                with st.expander("View sources"):
                    for s in sources:
                        st.info(s)
    except Exception as e:
        import traceback
        with st.chat_message("assistant"):
            st.error(f"**Error:** {e}")
            st.code(traceback.format_exc())
        saved_text = f"[Error: {e}]"
    st.session_state.messages.append({'role':'assistant','content':saved_text})