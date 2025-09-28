# pages/3_Visualization.py
import streamlit as st

from ui_helpers import top_nav, show_csv, sidebar_question_picker, QUESTIONS
from oci_helpers import load_cloud_csv
from prep_helpers import DST_PREP, DST_UPLOAD
from viz_helpers import (
    q1_incident_types, q2_client_groups, q3_when, q4_resolution,
    q5_org_rates, q6_emotions, q7_reporters, q8_recurrence,
    q9_actions, q10_text_patterns
)

st.set_page_config(page_title="Questions & Plots", page_icon="📊", layout="wide")

top_nav()
st.title("📊 Questions & Plots")

use_uploaded = st.session_state.get("use_uploaded", False)
csv_name = DST_UPLOAD if use_uploaded else DST_PREP
df = load_cloud_csv(csv_name)
if df.empty:
    st.error(f"{csv_name} not found or empty. Please complete previous steps.")
    st.stop()

st.caption(f"Using: **{csv_name}**")
show_csv(df.head(20), "Preview")

q_idx = sidebar_question_picker()
short, full = QUESTIONS[q_idx]
st.subheader(f"Question: {short}")
st.caption(full)

figs = []; wc_img = None
if q_idx == 0:   figs, wc_img = q1_incident_types(df)
elif q_idx == 1: figs = q2_client_groups(df)
elif q_idx == 2: figs = q3_when(df)
elif q_idx == 3: figs = q4_resolution(df)
elif q_idx == 4: figs = q5_org_rates(df)
elif q_idx == 5: figs = q6_emotions(df)
elif q_idx == 6: figs = q7_reporters(df)
elif q_idx == 7: figs = q8_recurrence(df)
elif q_idx == 8: figs = q9_actions(df)
else:            figs = q10_text_patterns(df)

cols = st.columns(2)
saved_figs = []
for i, fig in enumerate(figs[:4]):
    with cols[i % 2]:
        st.plotly_chart(fig, use_container_width=True)
    saved_figs.append((f"fig_{i:02d}.png", fig))

if wc_img is not None:
    st.image(wc_img, caption="Word Cloud", use_column_width=True)
    saved_figs.append(("wordcloud.png", wc_img))

# pass context to Recommendations page
st.session_state["viz_csv_used"] = csv_name
st.session_state["viz_question_idx"] = q_idx
st.session_state["viz_figs"] = saved_figs

st.divider()
st.page_link("pages/4_Recommendations.py", label="🧠 Recommendation", use_container_width=True)
