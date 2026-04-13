import os
import sys
import streamlit as st
import plotly.graph_objects as go

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from extractor import extract_text
from resume_parser import parse_resume
from scorer import score, SAMPLE_JD

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Resume Scorer",
    page_icon="🎯",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container { padding: 2rem 3rem; }

/* Score card */
.score-label {
    text-align: center;
    font-size: 1rem;
    font-weight: 600;
    color: #6b7280;
    margin-top: -1rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Section header */
h3 { color: #111827; font-weight: 700; margin-bottom: 0.5rem; }

/* Skill chip */
.chip-green {
    display: inline-block;
    background: #dcfce7;
    color: #15803d;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 3px 3px;
}
.chip-red {
    display: inline-block;
    background: #fee2e2;
    color: #b91c1c;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 3px 3px;
}

/* Recommendation card */
.rec-card {
    background: #f8fafc;
    border-left: 4px solid #6366f1;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.9rem;
    color: #1e293b;
}

/* Divider */
hr { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }

/* Breakdown bar label */
.bar-label {
    font-size: 0.82rem;
    font-weight: 500;
    color: #374151;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def score_color(s: float) -> str:
    if s >= 75: return "#16a34a"
    if s >= 50: return "#d97706"
    return "#dc2626"

def gauge_chart(score: float) -> go.Figure:
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": color, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9ca3af",
                     "tickfont": {"size": 11}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#f3f4f6",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "#fef2f2"},
                {"range": [50, 75], "color": "#fffbeb"},
                {"range": [75, 100],"color": "#f0fdf4"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
    )
    return fig

def breakdown_bar(label: str, val: float, max_val: int):
    pct = int((val / max_val) * 100)
    color = score_color(val / max_val * 100)
    st.markdown(f'<div class="bar-label">{label} &nbsp;<span style="color:{color};font-weight:700">{val}/{max_val}</span></div>', unsafe_allow_html=True)
    st.progress(pct)

def chips(skills: list, kind: str):
    cls = "chip-green" if kind == "matched" else "chip-red"
    html = "".join(f'<span class="{cls}">{s}</span>' for s in skills)
    st.markdown(html, unsafe_allow_html=True)


# ── Layout ────────────────────────────────────────────────────────────────────
st.title("🎯 ATS Resume Scorer")
st.caption("Upload your resume + paste a Job Description → get your ATS score instantly.")
st.markdown("<hr>", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📄 Resume")
    uploaded = st.file_uploader("Upload PDF resume", type=["pdf"], label_visibility="collapsed")

with right:
    st.subheader("📋 Job Description")
    jd_text = st.text_area(
        "Paste JD here",
        value=SAMPLE_JD.strip(),
        height=280,
        label_visibility="collapsed",
        placeholder="Paste the job description here...",
    )

st.markdown("<br>", unsafe_allow_html=True)
analyze = st.button("⚡ Analyze Resume", use_container_width=True, type="primary")

# ── Run scorer ────────────────────────────────────────────────────────────────
if analyze:
    if not uploaded:
        st.error("Upload a resume PDF first.")
        st.stop()
    if not jd_text.strip():
        st.error("Paste a job description first.")
        st.stop()

    with st.spinner("Extracting resume & scoring... (first run may take ~30s to load AI model)"):
        # Save uploaded to temp
        tmp_path = os.path.join(_HERE, "_tmp_resume.pdf")
        with open(tmp_path, "wb") as f:
            f.write(uploaded.read())

        try:
            raw_text = extract_text(tmp_path)
            parsed   = parse_resume(raw_text)
            result   = score(parsed, jd_text)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Results layout ─────────────────────────────────────────────────────
    col_gauge, col_break = st.columns([1, 1.4], gap="large")

    with col_gauge:
        st.subheader("ATS Score")
        st.plotly_chart(gauge_chart(result["total_score"]), use_container_width=True)
        st.markdown(f'<div class="score-label">Overall Match</div>', unsafe_allow_html=True)

        # Grade label
        s = result["total_score"]
        if s >= 80:   grade, gcolor = "Excellent ✅", "#16a34a"
        elif s >= 60: grade, gcolor = "Good 🟡",      "#d97706"
        elif s >= 40: grade, gcolor = "Fair 🟠",       "#ea580c"
        else:         grade, gcolor = "Weak ❌",       "#dc2626"

        st.markdown(f'<div style="text-align:center;font-size:1.1rem;font-weight:700;color:{gcolor};margin-top:0.5rem">{grade}</div>', unsafe_allow_html=True)

    with col_break:
        st.subheader("Score Breakdown")
        bd = result["breakdown"]

        MAXES = {
            "skills_match (40)":     40,
            "hot_skills_bonus (10)": 10,
            "experience (20)":       20,
            "education (10)":        10,
            "projects (10)":         10,
            "completeness (10)":     10,
        }
        LABELS = {
            "skills_match (40)":     "Skills Match",
            "hot_skills_bonus (10)": "Hot Skills Bonus",
            "experience (20)":       "Experience",
            "education (10)":        "Education",
            "projects (10)":         "Projects",
            "completeness (10)":     "Completeness",
        }

        for key, label in LABELS.items():
            breakdown_bar(f"{label}", bd[key], MAXES[key])
            st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Skills ─────────────────────────────────────────────────────────────
    sk_col1, sk_col2 = st.columns(2, gap="large")

    with sk_col1:
        st.subheader(f"✅ Matched Skills ({len(result['matched_skills'])})")
        if result["matched_skills"]:
            chips(result["matched_skills"], "matched")
        else:
            st.caption("No skills matched.")

    with sk_col2:
        st.subheader(f"❌ Missing Skills ({len(result['missing_skills'])})")
        if result["missing_skills"]:
            chips(result["missing_skills"], "missing")
        else:
            st.caption("You have all JD skills! 🎉")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Recommendations ────────────────────────────────────────────────────
    st.subheader("💡 Recommendations")
    for rec in result["recommendations"]:
        st.markdown(f'<div class="rec-card">{rec}</div>', unsafe_allow_html=True)
