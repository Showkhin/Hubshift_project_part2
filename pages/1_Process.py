# pages/1_Process.py
import streamlit as st
from ui_helpers import top_nav, show_csv
from oci_helpers import load_cloud_csv
from prep_helpers import DST_MERGED, manual_prepare, ollama_prepare, write_prepared

st.set_page_config(page_title="Process", page_icon="⚙️", layout="wide")

top_nav()
st.title("⚙️ Process Merged Data")

merged = load_cloud_csv(DST_MERGED)
if merged.empty:
    st.error("merged_data.csv not found or empty. Go back to Home to build it.")
    st.stop()

show_csv(merged.head(500), "Merged data preview")

st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("🧠 Prepare by Ollama", help="Use BakLLaVA-7B to normalize categories", use_container_width=True, key="prep_ollama"):
        with st.spinner("Preparing with Ollama..."):
            df = ollama_prepare(merged)
            which = write_prepared(df, "ollama")
            st.session_state["prep_variant"] = "ollama"
        st.success(f"Saved {which} and updated prep.csv in cloud.")
with c2:
    if st.button("🧹 Prepare without Ollama", help="Deterministic cleanup only", use_container_width=True, key="prep_manual"):
        with st.spinner("Preparing manually..."):
            df = manual_prepare(merged)
            which = write_prepared(df, "manual")
            st.session_state["prep_variant"] = "manual"
        st.success(f"Saved {which} and updated prep.csv in cloud.")

st.divider()
st.page_link("pages/2_Prepared.py", label="➡️ Next", use_container_width=True)
