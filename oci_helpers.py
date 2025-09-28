# oci_helpers.py
import io
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import streamlit as st
import oci
from oci.exceptions import ServiceError

def _config_from_secrets_or_env():
    # Prefer Streamlit secrets
    if "OCI_USER_OCID" in st.secrets:
        return {
            "user": st.secrets["OCI_USER_OCID"],
            "tenancy": st.secrets["OCI_TENANCY_OCID"],
            "region": st.secrets["OCI_REGION"],
            "fingerprint": st.secrets["OCI_FINGERPRINT"],
            "key_content": st.secrets["OCI_KEY_CONTENT"],
        }
    # Fallback to env vars with key_file
    key_file = os.getenv("OCI_KEY_FILE", os.path.expanduser("~/.oci/oci_api_key.pem"))
    return {
        "user": os.getenv("OCI_USER_OCID"),
        "tenancy": os.getenv("OCI_TENANCY_OCID"),
        "region": os.getenv("OCI_REGION", "ap-sydney-1"),
        "fingerprint": os.getenv("OCI_FINGERPRINT"),
        "key_file": key_file,
    }

def _ns_bucket_region():
    ns = st.secrets.get("OCI_NAMESPACE", os.getenv("OCI_NAMESPACE"))
    b  = st.secrets.get("OCI_BUCKET", os.getenv("OCI_BUCKET"))
    r  = st.secrets.get("OCI_REGION", os.getenv("OCI_REGION", "ap-sydney-1"))
    if not ns or not b:
        raise RuntimeError("Set OCI_NAMESPACE and OCI_BUCKET in secrets.toml")
    return ns, b, r

def _get_object_client():
    cfg = _config_from_secrets_or_env()
    return oci.object_storage.ObjectStorageClient(cfg)

# ---------- basic ops ----------
def download_blob(name: str) -> bytes:
    ns, b, _ = _ns_bucket_region()
    oc = _get_object_client()
    try:
        resp = oc.get_object(ns, b, name)
        return resp.data.content
    except ServiceError as e:
        if e.status == 404:
            raise FileNotFoundError(f"Object not found: {name}")
        raise

def upload_blob(name: str, content: bytes, content_type: str = "application/octet-stream"):
    ns, b, _ = _ns_bucket_region()
    oc = _get_object_client()
    oc.put_object(ns, b, name, content, content_type=content_type)

# ---------- CSV helpers ----------
def load_cloud_csv(name: str, columns: Optional[list] = None) -> pd.DataFrame:
    try:
        raw = download_blob(name)
        df = pd.read_csv(io.BytesIO(raw))
        if columns:
            for c in columns:
                if c not in df.columns:
                    df[c] = pd.NA
            df = df[columns]
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=columns or [])
    except Exception:
        return pd.DataFrame(columns=columns or [])

def upload_cloud_csv(name: str, df: pd.DataFrame):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_blob(name, csv_bytes, content_type="text/csv")

# ---------- PAR for charts ----------
def create_par_url(object_name: str, hours_valid: int = 48) -> Optional[str]:
    """
    Create a Pre-Authenticated Request for a single object (read-only).
    If policy forbids, return None (recommendations will use text-only fallback).
    """
    ns, b, region = _ns_bucket_region()
    oc = _get_object_client()
    details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=f"par_{int(time.time())}_{object_name.replace('/', '_')}",
        access_type="ObjectRead",
        time_expires=datetime.now(timezone.utc) + timedelta(hours=hours_valid),
        bucket_listing_action=None,
        object_name=object_name,
    )
    try:
        resp = oc.create_preauthenticated_request(ns, b, details)
        base = f"https://objectstorage.{region}.oraclecloud.com"
        return base + resp.data.access_uri
    except Exception:
        return None
