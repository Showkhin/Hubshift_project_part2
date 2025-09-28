# pages/2_Prepared.py
import pandas as pd
import streamlit as st

from ui_helpers import top_nav, show_csv
from oci_helpers import load_cloud_csv, upload_cloud_csv
from prep_helpers import DST_PREP, DST_UPLOAD

st.set_page_config(page_title="Prepared", page_icon="🧹", layout="wide")

top_nav()
st.title("🧹 Prepared Dataset")

df = load_cloud_csv(DST_PREP)
if df.empty:
    st.warning("prep.csv not found. Please run Process first.")
else:
    show_csv(df.head(500), "Current 'prep.csv'")

st.divider()
st.subheader("Upload a manually-edited prepared CSV (optional)")
upl = st.file_uploader("Upload CSV to override at visualization time", type=["csv"])
if upl is not None:
    try:
        df_up = pd.read_csv(upl)
        upload_cloud_csv(DST_UPLOAD, df_up)
        st.session_state["use_uploaded"] = True
        st.success("Saved as 'upload_prep.csv' in cloud. Visualization will use this file.")
    except Exception as e:
        st.error(f"Upload failed: {e}")

st.divider()
st.page_link("pages/3_Visualization.py", label="📊 Visualization", use_container_width=True)
