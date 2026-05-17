import streamlit as st
import datetime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

if "initialized" not in st.session_state:
    st.session_state.studyai = StudyAssistant()
    st.session_state.initialized = True

st.title("Study Plan")

tab_create, tab_saved = st.tabs(["Create Plan", "Saved Plans"])

with tab_create:
    topic = st.text_input("What topic do you want to study?")
    target_date = st.date_input("Target date", value=datetime.date.today() + datetime.timedelta(days=7), min_value=datetime.date.today())
    days = (target_date - datetime.date.today()).days or 1
    st.caption(f"{days} day(s) until target date")
    if st.button("Generate Plan", disabled=not topic):
        with st.spinner("Generating your study plan..."):
            plan = st.session_state.studyai.create_study_plan(topic, days)
        if plan:
            for day_info in plan['plan']:
                with st.expander(f"Day {day_info['day']}: {day_info.get('focus','')}"):
                    for task in day_info.get('tasks', []):
                        st.checkbox(task, key=f"new_{day_info['day']}_{task}")
            if st.button("Save this plan"):
                st.session_state.studyai.save_study_plan(plan)
                st.success("Plan saved!")
        else:
            st.warning("Could not generate a plan. Try adding notes on this topic first.")

with tab_saved:
    plans = st.session_state.studyai.load_study_plans()
    if not plans:
        st.info("No saved plans yet. Create one above.")
    else:
        for i, plan in enumerate(plans):
            with st.expander(f"{plan['topic']} — {plan['days']} days (created {plan.get('created','')})"):
                for day_info in plan['plan']:
                    st.markdown(f"**Day {day_info['day']}: {day_info.get('focus','')}**")
                    for task in day_info.get('tasks', []):
                        st.checkbox(task, key=f"saved_{i}_{day_info['day']}_{task}")
