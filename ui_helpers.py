import streamlit as st
import pandas as pd

QUESTIONS = [
    ("Common incident types",
     "What are the most common types of incidents across all clients? Bar, pie, stacked by severity; trend over time; severity heatmap; word cloud."),
    ("Client groups with more incidents",
     "Which client groups face more incidents? Client counts; rate by NDIS ID; recurrence by client; age group × type."),
    ("When do incidents occur?",
     "When do incidents typically occur? Time-of-day histogram; day-of-week; monthly pattern; severity over time of day."),
    ("How quickly resolved?",
     "How quickly are incidents resolved? Distribution of resolution time; by type; by org; by severity."),
    ("Organizations with higher rates",
     "Which organizations have higher incident rates? Incidents per org; severity per org; trend; emotion by org."),
    ("Emotional impact detected",
     "What emotional impact is detected? Distribution; by type; by org; trend over time."),
    ("Key reporters",
     "Who are the key reporters? Activity; reporter × org; reporter × severity."),
    ("What tends to recur?",
     "What types of incidents recur? Recurrence by type; recurrence × severity; by client; over time."),
    ("Actions taken patterns",
     "Which actions are most common? Distribution; actions × type; actions × severity; resolution by action."),
    ("Text pattern insights",
     "What patterns emerge from text? Keyword frequency; clustering; co-occurrence."),
]

def top_nav():
    st.markdown("### Navigation")
    cols = st.columns(5)
    with cols[0]:
        st.page_link("app.py", label="🏠 Home", use_container_width=True)
    with cols[1]:
        st.page_link("pages/1_Process.py", label="⚙️ Process", use_container_width=True)
    with cols[2]:
        st.page_link("pages/2_Prepared.py", label="🧹 Prepared", use_container_width=True)
    with cols[3]:
        st.page_link("pages/3_Visualization.py", label="📊 Questions & Plots", use_container_width=True)
    with cols[4]:
        st.page_link("pages/4_Recommendations.py", label="🧠 Recommendations", use_container_width=True)

def show_csv(df: pd.DataFrame, caption: str = ""):
    if caption:
        st.caption(caption)
    st.dataframe(df, use_container_width=True, hide_index=True)

def sidebar_question_picker():
    st.sidebar.markdown("### 🧭 Pick a question")
    chosen = st.session_state.get("current_question", 0)
    for i, (short, full) in enumerate(QUESTIONS):
        if st.sidebar.button(short, key=f"qbtn_{i}", help=full, use_container_width=True):
            chosen = i
    st.session_state["current_question"] = chosen
    st.sidebar.markdown("<div class='hover-help'>Hover a button for the full question</div>", unsafe_allow_html=True)
    return chosen
