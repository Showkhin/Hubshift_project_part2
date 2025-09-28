# prep_helpers.py
from typing import List
import numpy as np
import pandas as pd
from dateutil import parser
# viz_helpers.py

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from oci_helpers import load_cloud_csv, upload_cloud_csv
from ollama_helpers import ask_for_category_mapping

# Cloud object names
SRC_FINAL  = "final_emotion_ensemble.csv"
SRC_MAIN   = "main.csv"
SRC_REP    = "reporter.csv"
DST_MERGED = "merged_data.csv"
DST_OLLAMA = "ollama_prepared.csv"
DST_MANUAL = "manual_prepared.csv"
DST_PREP   = "prep.csv"
DST_UPLOAD = "upload_prep.csv"

# ---------- helpers ----------
def _best_key(df: pd.DataFrame, candidates: List[str]) -> List[str]:
    return [c for c in candidates if c in df.columns]

def _safe_dt(x):
    """Robust date parser with fuzzy matching."""
    if pd.isna(x):
        return pd.NaT
    try:
        return parser.parse(str(x), dayfirst=False, yearfirst=True, fuzzy=True)
    except Exception:
        return pd.NaT

def _to_naive(x):
    """Force a single datetime to tz-naive if it has tzinfo."""
    if pd.isna(x):
        return pd.NaT
    try:
        return x.tz_convert(None) if hasattr(x, "tzinfo") and x.tzinfo else x
    except Exception:
        try:
            return x.tz_localize(None)
        except Exception:
            return x

# ---------- merge the three CSVs ----------
def merge_three_sources() -> pd.DataFrame:
    f = load_cloud_csv(SRC_FINAL)
    m = load_cloud_csv(SRC_MAIN)
    r = load_cloud_csv(SRC_REP)

    # rename common variants
    rename_map = {
        "organisation": "organization",
        "organization name": "organization",
        "org_name": "organization",
        "client": "client_name",
        "report_date": "reported_date",
        "incident_datetime": "incident_date",
    }
    for df in [f, m, r]:
        inter = {k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns}
        if inter:
            df.rename(columns=inter, inplace=True)

    # join strategy
    df = f.copy()
    if not m.empty:
        on = list(set(_best_key(m, ["filename","client_name","ndis_id"])) & set(df.columns))
        if on:
            df = df.merge(m, on=on, how="left", suffixes=("", "_m"))
        elif "client_name" in m.columns and "client_name" in df.columns:
            df = df.merge(m, on="client_name", how="left", suffixes=("", "_m"))

    if not r.empty:
        on_r = list(set(_best_key(r, ["reporter","client_name"])) & set(df.columns))
        if on_r:
            df = df.merge(r, on=on_r, how="left", suffixes=("", "_r"))
        elif "reporter" in r.columns and "reporter" in df.columns:
            df = df.merge(r, on="reporter", how="left", suffixes=("", "_r"))

    # ensure columns exist
    for col in [
        "incident_date","incident_time","incident_type","severity","description",
        "client_name","organization","reporter","emotion","actions_taken",
        "dob","ndis_id","recurrence","resolution_time"
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    upload_cloud_csv(DST_MERGED, df)
    return df

# ---------- manual deterministic preparation ----------
def manual_prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["incident_dt"] = out["incident_date"].apply(_safe_dt)
    out["reported_dt"] = out.get("reported_date", pd.Series([pd.NaT]*len(out))).apply(_safe_dt)

    def _hour(x):
        try:
            s = str(x)
            if pd.isna(x) or s.strip() == "":
                return np.nan
            return int(s.strip().split(":")[0])
        except Exception:
            return np.nan
    out["incident_hour"] = out["incident_time"].apply(_hour)

    out["year"]  = out["incident_dt"].dt.year
    out["month"] = out["incident_dt"].dt.to_period("M").astype(str)
    out["dow"]   = out["incident_dt"].dt.day_name()

    # --- Age calculation (force everything tz-naive) ---
    if "dob" in out.columns:
        dob = out["dob"].apply(_safe_dt)
        dob = pd.to_datetime(dob, errors="coerce")
        dob = dob.apply(_to_naive)

        now = pd.Timestamp.utcnow().tz_localize(None).normalize()
        age = (now - dob).dt.days / 365.25

        out["age_years"] = age
        bins = [0,12,18,30,45,60,200]
        labels = ["0-12","13-18","19-30","31-45","46-60","60+"]
        out["age_group"] = pd.cut(age, bins=bins, labels=labels, right=False).astype("object")
    else:
        out["age_years"] = np.nan
        out["age_group"] = pd.NA

    # severity normalization
    sev_map = {
        "low":"Low","medium":"Medium","med":"Medium","moderate":"Medium",
        "high":"High","critical":"Critical","crit":"Critical"
    }
    out["severity_norm"] = (
        out["severity"].astype(str).str.strip().str.lower().map(sev_map).fillna(out["severity"])
    )

    # recurrence calc if missing
    if "recurrence" not in out.columns or out["recurrence"].isna().all():
        grp = out.groupby(["client_name","incident_type"], dropna=False)["incident_type"].transform("count")
        out["recurrence"] = grp
    out["recurrence"] = pd.to_numeric(out["recurrence"], errors="coerce").fillna(0).astype(int)

    # resolution time
    if "resolution_time" in out.columns and not out["resolution_time"].isna().all():
        def _to_hours(x):
            try:
                s = str(x).lower()
                if "h" in s and "m" in s:
                    h = int(s.split("h")[0].strip())
                    m = int(s.split("h")[1].split("m")[0].strip())
                    return h + m/60.0
                return float(s)
            except Exception:
                return np.nan
        out["resolution_hours"] = out["resolution_time"].apply(_to_hours)
    else:
        out["resolution_hours"] = (
            (out["reported_dt"] - out["incident_dt"]).dt.total_seconds() / 3600.0
        )

    # ✅ enforce numeric resolution_hours
    out["resolution_hours"] = pd.to_numeric(out["resolution_hours"], errors="coerce").fillna(0)

    # emotion normalization
    emo_map = {
        "joy":"Happy","happiness":"Happy","sadness":"Sad","anger":"Anger","fear":"Fear",
        "neutral":"Neutral","calm":"Calm","surprise":"Surprised","disgust":"Disgust"
    }
    out["emotion_norm"] = (
        out["emotion"].astype(str).str.strip().str.lower().map(emo_map).fillna(out["emotion"])
    )

    return out

# ---------- Ollama-assisted preparation ----------
def ollama_prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = manual_prepare(df)
    for col in ["incident_type","actions_taken","severity"]:
        uniq = sorted([str(v) for v in out[col].dropna().unique()][:120])
        mapping = ask_for_category_mapping(col, uniq)
        out[col + "_norm_llm"] = out[col].astype(str).map(lambda x: mapping.get(x, x)) if mapping else out[col]
    return out

# ---------- orchestration ----------
def ensure_merged_in_cloud() -> pd.DataFrame:
    return merge_three_sources()

def write_prepared(df: pd.DataFrame, variant: str) -> str:
    if variant == "ollama":
        upload_cloud_csv(DST_OLLAMA, df)
        upload_cloud_csv(DST_PREP, df)
        return DST_OLLAMA
    else:
        upload_cloud_csv(DST_MANUAL, df)
        upload_cloud_csv(DST_PREP, df)
        return DST_MANUAL
