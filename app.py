# app.py
import streamlit as st
from ui_helpers import top_nav, show_csv
from oci_helpers import load_cloud_csv
from prep_helpers import ensure_merged_in_cloud, SRC_FINAL, SRC_MAIN, SRC_REP, DST_MERGED

st.set_page_config(page_title="NDIS Incident Insights", page_icon="📊", layout="wide")

with open("theme.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

top_nav()
st.title("NDIS Incident Insights — Home")

with st.spinner("Merging the three data sources from Oracle Cloud..."):
    combined = ensure_merged_in_cloud()

st.success(f"Fresh merge saved as '{DST_MERGED}' in your bucket.")
st.subheader("Combined (top)")
show_csv(combined.head(500), f"First 500 rows of {DST_MERGED}")

st.divider()
st.subheader("Source tables (from Oracle Cloud)")
col1, col2, col3 = st.columns([1,1,1])
with col1:
    show_csv(load_cloud_csv(SRC_FINAL), f"Cloud: {SRC_FINAL}")
with col2:
    show_csv(load_cloud_csv(SRC_MAIN), f"Cloud: {SRC_MAIN}")
with col3:
    show_csv(load_cloud_csv(SRC_REP), f"Cloud: {SRC_REP}")

st.divider()
st.page_link("pages/1_Process.py", label="➡️ Process", use_container_width=True)
