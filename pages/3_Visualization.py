# pages/3_Visualization.py
import streamlit as st
import plotly.graph_objs as go
from PIL import Image

from ui_helpers import top_nav, show_csv, sidebar_question_picker, QUESTIONS
from oci_helpers import load_cloud_csv
from prep_helpers import DST_PREP, DST_UPLOAD
from viz_helpers import (
    q1_incident_types, q2_client_groups, q3_when, q4_resolution,
    q5_org_rates, q6_emotions, q7_reporters, q8_recurrence,
    q9_actions, q10_text_patterns
)

# =========================
# Page Config
# =========================
st.set_page_config(page_title="Questions & Plots", page_icon="📊", layout="wide")
top_nav()
st.title("📊 Questions & Plots")

# =========================
# Load Data
# =========================
use_uploaded = st.session_state.get("use_uploaded", False)
csv_name = DST_UPLOAD if use_uploaded else DST_PREP
df = load_cloud_csv(csv_name)
if df.empty:
    st.error(f"{csv_name} not found or empty. Please complete previous steps.")
    st.stop()

st.caption(f"Using: **{csv_name}**")
show_csv(df.head(20), "Preview")

# =========================
# Question Picker
# =========================
q_idx = sidebar_question_picker()
short, full = QUESTIONS[q_idx]
st.subheader(f"Question: {short}")
st.caption(full)

# =========================
# Generate Figures
# =========================
figs, wc_img = [], None
if q_idx == 0:
    figs, wc_img = q1_incident_types(df)
elif q_idx == 1:
    figs = q2_client_groups(df)
elif q_idx == 2:
    figs = q3_when(df)
elif q_idx == 3:
    figs = q4_resolution(df)
elif q_idx == 4:
    figs = q5_org_rates(df)
elif q_idx == 5:
    figs = q6_emotions(df)
elif q_idx == 6:
    figs = q7_reporters(df)
elif q_idx == 7:
    figs = q8_recurrence(df)
elif q_idx == 8:
    figs = q9_actions(df)
elif q_idx == 9:
    figs = q10_text_patterns(df)

# =========================
# Show Figures
# =========================
cols = st.columns(2)
saved_figs = []

for i, fig in enumerate(figs[:4]):
    with cols[i % 2]:
        if isinstance(fig, go.Figure):
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_{i}")
        elif hasattr(fig, "savefig"):  # Matplotlib figure
            st.pyplot(fig, key=f"matplotlib_{i}")
        elif isinstance(fig, Image.Image):  # PIL WordCloud
            st.image(fig, caption="Word Cloud", use_column_width=True)

    saved_figs.append((f"fig_{i:02d}.png", fig))

if wc_img is not None:
    st.image(wc_img, caption="Word Cloud", use_column_width=True)
    saved_figs.append(("wordcloud.png", wc_img))

# =========================
# Pass Context to Recommendations Page
# =========================
st.session_state["viz_csv_used"] = csv_name
st.session_state["viz_question_idx"] = q_idx
st.session_state["viz_figs"] = saved_figs

# =========================
# Navigation
# =========================
st.divider()
st.page_link("pages/4_Recommendations.py", label="🧠 Recommendation", use_container_width=True)
