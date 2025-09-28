# pages/4_Recommendations.py
import streamlit as st
import pandas as pd

from ollama_helpers import ollama_generate
from oci_helpers import load_cloud_csv
from prep_helpers import DST_PREP
import viz_helpers  # to regenerate the same plots
from ui_helpers import QUESTIONS  # shared questions list

# =========================
# Page Configuration
# =========================
st.set_page_config(page_title="Recommendations", page_icon="🧠", layout="wide")
st.title("🧠 Recommendations")

# =========================
# Load Data from Cloud
# =========================
df = load_cloud_csv(DST_PREP)
if df.empty:
    st.error("No prepared data found (prep.csv). Please run the Process step first.")
    st.stop()

st.caption(f"Using cloud file: {DST_PREP} | Records loaded: {len(df)}")

# =========================
# Navigation
# =========================
q_idx = st.session_state.get("q_idx", 0)

st.sidebar.header("Pick a question")
for i, (short, full) in enumerate(QUESTIONS):
    if st.sidebar.button(short, key=f"q{i}", help=full):
        st.session_state["q_idx"] = i
        q_idx = i
        st.rerun()

# =========================
# Display Question
# =========================
short_q, full_q = QUESTIONS[q_idx]
st.markdown(f"### Question:\n{full_q}")

# =========================
# Generate plots for this question only
# =========================
figs, wc = [], None
if q_idx == 0:
    figs, wc = viz_helpers.q1_incident_types(df)
elif q_idx == 1:
    figs = viz_helpers.q2_client_groups(df)
elif q_idx == 2:
    figs = viz_helpers.q3_when(df)
elif q_idx == 3:
    figs = viz_helpers.q4_resolution(df)
elif q_idx == 4:
    figs = viz_helpers.q5_org_rates(df)
elif q_idx == 5:
    figs = viz_helpers.q6_emotions(df)
elif q_idx == 6:
    figs = viz_helpers.q7_reporters(df)
elif q_idx == 7:
    figs = viz_helpers.q8_recurrence(df)
elif q_idx == 8:
    figs = viz_helpers.q9_actions(df)
elif q_idx == 9:
    figs = viz_helpers.q10_text_patterns(df)

# Show the figures
for fig in figs:
    st.plotly_chart(fig, use_container_width=True)
if wc is not None:
    st.image(wc, caption="Word Cloud")

# =========================
# Button → Get Recommendation from Ollama
# =========================
if st.button("💡 Generate Recommendation", use_container_width=True):
    with st.spinner("Thinking with Ollama (local gemma3)..."):
        # Build a prompt that references the question and shown charts
        prompt = (
            f"Based only on the visualizations provided for the question:\n\n"
            f"'{full_q}'\n\n"
            "Give focused, actionable recommendations. Do not describe charts "
            "that are not shown."
        )
        resp = ollama_generate(prompt)

    if resp.startswith("[Ollama error]"):
        st.error(resp)
    else:
        st.subheader("💡 Recommendation")
        st.write(resp)

# =========================
# Navigation Links
# =========================
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/3_Visualization.py", label="⬅️ Back to Questions")
with col2:
    st.page_link("app.py", label="🏠 Home")
