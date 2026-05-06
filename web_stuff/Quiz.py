# Module to create a streamlit UI
import streamlit as st

st.title("Quiz on Material")

topic = st.text_input("Enter a topic to get quizzed on.")
if st.button("Generate Question"):
    with st.spinner("Consulting your notes ..."):
        quiz_data = st.session_state.studyai.quiz_stuff(topic)
        if quiz_data:
            st.session_state.current_quiz = quiz_data
            st.session_state.user_submitted = False
        else:
            st.error("Couldn't find enough data in the submitted notes to generate a question.")
        
if st.session_state.current_quiz:
    quiz = st.session_state.current_quiz
    st.divider()
    st.markdown(quiz['question'])
    user_choice = st.radio("Choose your answer:",options=['A','B','C','D'],index=None)
    if st.button("Submit Answer"):
        if user_choice == None:
            st.warning("Select an answer choice before submitting")
        else:
            if user_choice == quiz['answer']:
                st.success("Correct!")
            else:
                st.error(f"Incorrect, the correct answer is {quiz['answer']}.")