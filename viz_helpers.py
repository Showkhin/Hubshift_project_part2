from io import BytesIO
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from PIL import Image
from wordcloud import WordCloud

# =====================
# Helpers
# =====================

def _na(df, col) -> bool:
    """Check if column exists and is non-empty."""
    return col in df.columns and not df[col].dropna().empty


def _grid_fig(fig, title: str):
    """Apply consistent layout to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=30, r=20, t=50, b=30),
        title=dict(text=title, x=0.02, xanchor="left", y=0.95, font=dict(size=16)),
    )
    return fig


def wordcloud_from_text(df: pd.DataFrame, text_col: str = "description") -> Optional[Image.Image]:
    """Generate a WordCloud image from a text column."""
    text = " ".join([str(t) for t in df[text_col].dropna().tolist()]) if _na(df, text_col) else ""
    if not text.strip():
        return None
    wc = WordCloud(width=800, height=400, background_color="black").generate(text)
    img = wc.to_image()
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf)

# =====================
# Visualizations
# =====================

# 1
def q1_incident_types(df: pd.DataFrame) -> Tuple[List, Optional[Image.Image]]:
    figs = []
    wc = None
    if _na(df, "incident_type"):
        s = df["incident_type"].astype(str).value_counts().reset_index()
        s.columns = ["incident_type", "count"]
        figs.append(_grid_fig(px.bar(s, x="incident_type", y="count"), "Incident types (count)"))
        figs.append(_grid_fig(px.pie(s, names="incident_type", values="count"), "Incident types (share)"))
        if _na(df, "severity_norm"):
            t = df.groupby(["incident_type", "severity_norm"]).size().reset_index(name="count")
            figs.append(
                _grid_fig(
                    px.bar(t, x="incident_type", y="count", color="severity_norm", barmode="stack"),
                    "Incident type × severity",
                )
            )
    if _na(df, "month"):
        ts = df.groupby("month").size().reset_index(name="count")
        figs.append(_grid_fig(px.line(ts, x="month", y="count"), "Incidents per month"))
    wc = wordcloud_from_text(df, "description")
    return figs, wc


# 2
def q2_client_groups(df: pd.DataFrame) -> List:
    figs = []
    if _na(df, "client_name"):
        s = df["client_name"].astype(str).value_counts().head(20).reset_index()
        s.columns = ["client_name", "count"]
        figs.append(_grid_fig(px.bar(s, x="client_name", y="count"), "Incidents by client (Top 20)"))
        if _na(df, "ndis_id"):
            rate = df.groupby(["client_name", "ndis_id"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.scatter(rate, x="ndis_id", y="count", color="client_name"), "Rate by NDIS ID"))
    if _na(df, "recurrence") and _na(df, "client_name"):
        bx = _grid_fig(px.box(df.dropna(subset=["recurrence"]), x="client_name", y="recurrence"), "Recurrence by client")
        figs.append(bx)
    if _na(df, "age_group") and _na(df, "incident_type"):
        ct = df.groupby(["age_group", "incident_type"]).size().reset_index(name="count")
        figs.append(
            _grid_fig(
                px.density_heatmap(ct, x="age_group", y="incident_type", z="count", nbinsx=6),
                "Age group × incident type (heatmap)",
            )
        )
    return figs


# 3
def q3_when(df: pd.DataFrame) -> List:
    figs = []
    if _na(df, "incident_hour"):
        h = df["incident_hour"].dropna().astype(int)
        hh = pd.DataFrame({"hour": h})
        figs.append(_grid_fig(px.histogram(hh, x="hour", nbins=24), "Time of day (hour)"))
        if _na(df, "severity_norm"):
            t = df.dropna(subset=["incident_hour"]).copy()
            t["incident_hour"] = t["incident_hour"].astype(int)
            figs.append(_grid_fig(px.density_heatmap(t, x="incident_hour", y="severity_norm"), "Severity over time of day"))
    if _na(df, "dow"):
        s = (
            df["dow"]
            .astype(str)
            .value_counts()
            .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            .fillna(0)
            .reset_index()
        )
        s.columns = ["dow", "count"]
        figs.append(_grid_fig(px.bar(s, x="dow", y="count"), "Day of week"))
    if _na(df, "month"):
        ts = df.groupby("month").size().reset_index(name="count")
        figs.append(_grid_fig(px.line(ts, x="month", y="count"), "Monthly pattern"))
    return figs


# 4
def q4_resolution(df: pd.DataFrame) -> List:
    figs = []
    if "resolution_hours" not in df.columns:
        return figs
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce").fillna(0)
    figs.append(_grid_fig(px.histogram(df, x="resolution_hours", nbins=20), "Distribution of Resolution Time (hours)"))
    figs.append(_grid_fig(px.box(df, x="resolution_hours"), "Resolution Time Spread"))
    return figs


# 5
def q5_org_rates(df: pd.DataFrame) -> List:
    figs = []
    if _na(df, "organization"):
        s = df["organization"].astype(str).value_counts().reset_index()
        s.columns = ["organization", "count"]
        figs.append(_grid_fig(px.bar(s, x="organization", y="count"), "Incidents per organization"))
        if _na(df, "severity_norm"):
            t = df.groupby(["organization", "severity_norm"]).size().reset_index(name="count")
            figs.append(
                _grid_fig(
                    px.bar(t, x="organization", y="count", color="severity_norm", barmode="stack"),
                    "Severity by organization",
                )
            )
        if _na(df, "month"):
            tt = df.groupby(["month", "organization"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.line(tt, x="month", y="count", color="organization"), "Org trend over time"))
        if _na(df, "emotion_norm"):
            e = df.groupby(["organization", "emotion_norm"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.density_heatmap(e, x="organization", y="emotion_norm", z="count"), "Emotion by organization"))
    return figs


# 6
def q6_emotions(df: pd.DataFrame) -> List:
    figs = []
    col = "emotion_norm" if "emotion_norm" in df.columns else "emotion"
    if _na(df, col):
        s = df[col].astype(str).value_counts().reset_index()
        s.columns = [col, "count"]
        figs.append(_grid_fig(px.pie(s, names=col, values="count"), "Emotion distribution"))
        if _na(df, "incident_type"):
            t = df.groupby([col, "incident_type"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.bar(t, x="incident_type", y="count", color=col, barmode="stack"), "Emotion × incident type"))
        if _na(df, "organization"):
            e = df.groupby(["organization", col]).size().reset_index(name="count")
            figs.append(_grid_fig(px.density_heatmap(e, x="organization", y=col, z="count"), "Emotion × organization"))
        if _na(df, "month"):
            tt = df.groupby(["month", col]).size().reset_index(name="count")
            figs.append(_grid_fig(px.line(tt, x="month", y="count", color=col), "Emotion trend over time"))
    return figs


# 7
def q7_reporters(df: pd.DataFrame) -> List:
    figs = []
    if _na(df, "reporter"):
        s = df["reporter"].astype(str).value_counts().head(30).reset_index()
        s.columns = ["reporter", "count"]
        figs.append(_grid_fig(px.bar(s, x="reporter", y="count"), "Reporter activity (Top 30)"))
        if _na(df, "organization"):
            t = df.groupby(["reporter", "organization"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.bar(t, x="reporter", y="count", color="organization", barmode="stack"), "Reporter × organization"))
        if _na(df, "severity_norm"):
            t = df.groupby(["reporter", "severity_norm"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.bar(t, x="reporter", y="count", color="severity_norm", barmode="stack"), "Reporter × severity"))
    return figs


# 8
def q8_recurrence(df: pd.DataFrame) -> List:
    figs = []
    if _na(df, "recurrence") and _na(df, "incident_type"):
        t = df.groupby("incident_type")["recurrence"].sum().reset_index()
        figs.append(_grid_fig(px.bar(t, x="incident_type", y="recurrence"), "Recurrence count by type"))
        if _na(df, "severity_norm"):
            ht = df.groupby(["recurrence", "severity_norm"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.density_heatmap(ht, x="recurrence", y="severity_norm", z="count"), "Recurrence × severity"))
        if _na(df, "client_name"):
            c = (
                df.groupby("client_name")["recurrence"]
                .sum()
                .reset_index()
                .sort_values("recurrence", ascending=False)
                .head(30)
            )
            figs.append(_grid_fig(px.bar(c, x="client_name", y="recurrence"), "Recurrence by client (Top 30)"))
        if _na(df, "month"):
            ts = df.groupby("month")["recurrence"].sum().reset_index()
            figs.append(_grid_fig(px.line(ts, x="month", y="recurrence"), "Recurrence over time"))
    return figs


# 9
def q9_actions(df: pd.DataFrame) -> List:
    figs = []
    col = "actions_taken_norm_llm" if "actions_taken_norm_llm" in df.columns else "actions_taken"
    if _na(df, col):
        s = df[col].astype(str).value_counts().head(25).reset_index()
        s.columns = [col, "count"]
        figs.append(_grid_fig(px.bar(s, x=col, y="count"), "Actions taken (Top 25)"))
        if _na(df, "incident_type"):
            t = df.groupby([col, "incident_type"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.bar(t, x=col, y="count", color="incident_type", barmode="stack"), "Actions × incident type"))
        if _na(df, "severity_norm"):
            t = df.groupby([col, "severity_norm"]).size().reset_index(name="count")
            figs.append(_grid_fig(px.bar(t, x=col, y="count", color="severity_norm", barmode="stack"), "Actions × severity"))
        if _na(df, "resolution_hours"):
            d = df.groupby(col)["resolution_hours"].median().reset_index()
            figs.append(_grid_fig(px.bar(d, x=col, y="resolution_hours"), "Median resolution (by action)"))
    return figs


# 10
def q10_text_patterns(df: pd.DataFrame) -> List:
    figs = []
    if "description" not in df.columns:
        return figs
    text_series = df["description"].dropna().astype(str)
    if text_series.empty:
        return figs

    # Keyword frequency
    words = " ".join(text_series).split()
    freq = pd.Series(words).value_counts().reset_index()
    freq.columns = ["word", "freq"]
    figs.append(_grid_fig(px.bar(freq.head(30), x="word", y="freq"), "Keyword frequency (top 30)"))

    # WordCloud image
    text = " ".join(text_series)
    wc = WordCloud(width=800, height=400, background_color="black", colormap="viridis").generate(text)
    img = wc.to_image()
    figs.append(img)

    return figs
