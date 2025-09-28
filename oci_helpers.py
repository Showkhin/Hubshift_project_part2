# oci_helpers.py
import os
import io
import time
import pandas as pd
import datetime as dt
from typing import Optional, Tuple, List
import streamlit as st
import oci
from oci.object_storage.models import CreatePreauthenticatedRequestDetails

# -----------------------
# Build OCI config
# -----------------------
@st.cache_resource(show_spinner=False)
def get_oci_client() -> Tuple[oci.object_storage.ObjectStorageClient, dict]:
    config = _build_oci_config()
    client = oci.object_storage.ObjectStorageClient(config)
    return client, config


def _build_oci_config() -> dict:
    """
    Build OCI config from Streamlit secrets (flat keys) or local ~/.oci/config.
    """
    if "OCI_USER_OCID" in st.secrets:
        return {
            "user": st.secrets["OCI_USER_OCID"],
            "tenancy": st.secrets["OCI_TENANCY_OCID"],
            "region": st.secrets["OCI_REGION"],
            "fingerprint": st.secrets["OCI_FINGERPRINT"],
            "key_content": st.secrets["OCI_KEY_CONTENT"],
        }

    # fallback to ~/.oci/config
    cfg_path = os.getenv("OCI_CONFIG_PATH", os.path.expanduser("~/.oci/config"))
    profile = os.getenv("OCI_PROFILE", "DEFAULT")
    return oci.config.from_file(cfg_path, profile_name=profile)


# -----------------------
# Namespace + Bucket
# -----------------------
NAMESPACE = os.getenv("OCI_NAMESPACE", st.secrets.get("OCI_NAMESPACE", "sdzbwxl65lpx"))
BUCKET = os.getenv("OCI_BUCKET", st.secrets.get("OCI_BUCKET", "incident-data-bucket"))


# -----------------------
# Object Storage Helpers
# -----------------------
def load_cloud_csv(object_name: str, columns: Optional[list] = None) -> pd.DataFrame:
    client, _ = get_oci_client()
    try:
        resp = client.get_object(NAMESPACE, BUCKET, object_name)
        df = pd.read_csv(io.BytesIO(resp.data.content))
        if columns:
            for c in columns:
                if c not in df.columns:
                    df[c] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=columns) if columns else pd.DataFrame()


def upload_cloud_csv(object_name: str, df: pd.DataFrame):
    client, _ = get_oci_client()
    bio = io.BytesIO()
    df.to_csv(bio, index=False)
    bio.seek(0)
    client.put_object(NAMESPACE, BUCKET, object_name, bio)


def list_objects(prefix: str = "") -> List[str]:
    client, _ = get_oci_client()
    names = []
    start = None
    while True:
        resp = client.list_objects(NAMESPACE, BUCKET, prefix=prefix, start=start, fields="name")
        for obj in resp.data.objects:
            names.append(obj.name)
        if not resp.data.next_start_with:
            break
        start = resp.data.next_start_with
    return sorted(names)


def create_share_link(object_name: str, days: int = 7) -> Optional[str]:
    try:
        client, cfg = get_oci_client()
        details = CreatePreauthenticatedRequestDetails(
            name=f"par-{object_name}-{int(time.time())}",
            access_type="ObjectRead",
            time_expires=(dt.datetime.utcnow() + dt.timedelta(days=days)),
            object_name=object_name,
        )
        par = client.create_preauthenticated_request(NAMESPACE, BUCKET, details).data
        return f"https://objectstorage.{cfg['region']}.oraclecloud.com{par.access_uri}"
    except Exception:
        return None
