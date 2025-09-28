# pages/4_Recommendations.py
import os
import tempfile
from typing import List

import plotly.io as pio
import streamlit as st

from ui_helpers import top_nav
from oci_helpers import upload_blob, create_par_url, load_cloud_csv
from ollama_helpers import ollama_generate
from prep_helpers import DST_PREP

st.set_page_config(page_title="Recommendations", page_icon="🧠", layout="wide")

top_nav()
st.title("🧠 Recommendations")

csv_name = st.session_state.get("viz_csv_used", DST_PREP)
q_idx = st.session_state.get("viz_question_idx", 0)
saved_figs = st.session_state.get("viz_figs", [])

df = load_cloud_csv(csv_name)
if df.empty:
    st.error("Prepared dataset missing. Please go back and run previous steps.")
    st.stop()

st.caption(f"Using: **{csv_name}** | Question index: {q_idx}")

image_urls: List[str] = []
tmpdir = tempfile.mkdtemp(prefix="plots_")
for name, obj in saved_figs[:4]:
    try:
        local = os.path.join(tmpdir, name)
        if hasattr(obj, "to_dict"):  # plotly fig
            pio.write_image(obj, local, format="png", width=1200, height=700, scale=2)
        else:  # PIL
            obj.save(local)
        with open(local, "rb") as f:
            upload_blob(f"plots/{name}", f.read(), content_type="image/png")
        url = create_par_url(f"plots/{name}")
        if url: image_urls.append(url)
    except Exception:
        pass  # fallback to text-only if needed

def quick_stats_str(d):
    parts=[]
    if "incident_type" in d.columns:
        parts.append("Top incident types: " + ", ".join(f"{k}({v})" for k,v in d["incident_type"].value_counts().head(10).to_dict().items()))
    if "severity_norm" in d.columns:
        parts.append("Severity mix: " + ", ".join(f"{k}({v})" for k,v in d["severity_norm"].value_counts().to_dict().items()))
    if "organization" in d.columns:
        parts.append("Top orgs: " + ", ".join(f"{k}({v})" for k,v in d["organization"].value_counts().head(10).to_dict().items()))
    if "emotion_norm" in d.columns:
        parts.append("Emotions: " + ", ".join(f"{k}({v})" for k,v in d["emotion_norm"].value_counts().to_dict().items()))
    return "\n".join(parts)

summary_txt = quick_stats_str(df)

prompt = (
    "You are advising an NDIS service provider. "
    "Analyze ONLY the provided charts (use image URLs if available) and the fallback data summary. "
    "For EACH chart, provide:\n"
    "1) 3–5 MOST IMPORTANT insights (prefix each with [HIGH])\n"
    "2) 2–4 less important but useful notes (prefix each with [LOW])\n"
    "3) A concise recommendations section: staffing, risk mitigation, scheduling, training, follow-up actions.\n"
    "Be specific and actionable.\n\n"
)

if image_urls:
    prompt += "Charts (public URLs):\n" + "\n".join(image_urls) + "\n\n"
else:
    prompt += "(No chart image URLs available; use the fallback data summary.)\n\n"

prompt += "Fallback data summary:\n" + summary_txt

with st.spinner("Calling Ollama for recommendations..."):
    resp = ollama_generate(prompt, images=image_urls if image_urls else None)

def highlight(text: str) -> str:
    return (text
            .replace("[HIGH]", "<span style='color:#22c55e;font-weight:600'>[HIGH]</span>")
            .replace("[LOW]", "<span style='color:#eab308;font-weight:600'>[LOW]</span>"))

st.markdown(highlight(resp), unsafe_allow_html=True)

st.divider()
cols = st.columns(2)
with cols[0]:
    st.page_link("pages/3_Visualization.py", label="⬅️ Back to Questions", use_container_width=True)
with cols[1]:
    st.page_link("app.py", label="🏠 Home", use_container_width=True)
