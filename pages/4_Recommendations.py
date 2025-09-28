# pages/4_Recommendations.py
import streamlit as st
import plotly.graph_objs as go
from PIL import Image

from ollama_helpers import ollama_generate
from oci_helpers import load_cloud_csv
from prep_helpers import DST_PREP
import viz_helpers
from ui_helpers import QUESTIONS

# =========================
# Page Config
# =========================
st.set_page_config(page_title="Recommendations", page_icon="🧠", layout="wide")
st.title("🧠 Recommendations")

# =========================
# Load Data
# =========================
df = load_cloud_csv(DST_PREP)
if df.empty:
    st.error("No prepared data found (prep.csv). Please run the Process step first.")
    st.stop()

st.caption(f"Using cloud file: {DST_PREP} | Records loaded: {len(df)}")

# =========================
# Sidebar Question Picker
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
# Generate Figures
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

# =========================
# Show Figures
# =========================
for i, fig in enumerate(figs):
    if isinstance(fig, go.Figure):
        st.plotly_chart(fig, use_container_width=True, key=f"plotly_{i}")
    elif hasattr(fig, "savefig"):  # Matplotlib
        st.pyplot(fig, key=f"matplotlib_{i}")
    elif isinstance(fig, Image.Image):  # PIL
        st.image(fig, caption="Word Cloud", use_column_width=True)

if wc is not None:  # extra wordcloud for Q1
    st.image(wc, caption="Word Cloud", use_column_width=True)

# =========================
# Styled Recommendation Helper
# =========================
def styled_recommendation(title: str, text: str, level: str = "medium"):
    colors = {
        "high": "#ffcccc",    # light red
        "medium": "#fff4cc",  # light yellow
        "low": "#ccffcc",     # light green
    }
    bg = colors.get(level, "#f0f0f0")

    st.markdown(
        f"""
        <div style="
            background-color: {bg};
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 15px;
            font-weight: bold;
            font-size: 16px;
            color: #222;
            line-height: 1.5;">
            <strong>{title}</strong><br>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================
# Button → Generate Recommendation
# =========================
if st.button("💡 Generate Recommendation", use_container_width=True):
    with st.spinner("Thinking with Ollama (bakllava:7b)..."):
        prompt = (
            f"Based only on the visualizations provided for the question:\n\n"
            f"'{full_q}'\n\n"
            "Give focused, actionable recommendations. "
            "Label them by priority: HIGH, MEDIUM, or LOW."
        )
        resp = ollama_generate(prompt)

    if resp.startswith("[Ollama error]"):
        st.error(
            f"Ollama returned an error:\n\n{resp}\n\n"
            "👉 If this is the first request after starting Ollama, wait ~1–2 minutes for the model to warm up."
        )
    else:
        st.subheader("💡 Recommendation")

        # Split response into lines and assign styles based on keywords
        for line in resp.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.lower().startswith(("high", "1.")):
                styled_recommendation("High Priority", l, "high")
            elif l.lower().startswith(("medium", "2.")):
                styled_recommendation("Medium Priority", l, "medium")
            elif l.lower().startswith(("low", "3.")):
                styled_recommendation("Low Priority", l, "low")
            else:
                # fallback: show as medium importance
                styled_recommendation("Info", l, "medium")

# =========================
# Navigation
# =========================
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/3_Visualization.py", label="⬅️ Back to Questions")
with col2:
    st.page_link("app.py", label="🏠 Home")
