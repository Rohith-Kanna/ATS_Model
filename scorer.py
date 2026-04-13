"""
scorer.py — ATS Resume Scorer
==============================
Inputs : parsed_resume (dict from resume_parser.parse_resume)
         job_description (str)
Output : dict → total_score, breakdown, matched_skills, missing_skills, recommendations

Scoring breakdown (100 pts total):
  40  Skills Match        — Jaccard-weighted keyword overlap on shared skill vocabulary
  10  Hot Skills Bonus    — In-demand skill coverage from JD
  20  Experience          — Sentence-transformer cosine similarity (resume exp vs JD)
  10  Education           — Rule-based degree + field matching
  10  Projects Relevance  — Sentence-transformer cosine similarity (projects vs JD)
  10  Completeness        — Section presence check
"""

import os
import re
import sys
import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from skill_loader import load_skill_set

# ── Load skill knowledge base once ───────────────────────────────────────────
SKILLS, HOT_SKILLS = load_skill_set(
    os.path.join(_HERE, "skills_dataset", "skills.csv"),
    os.path.join(_HERE, "skills_dataset", "Technology Skills.xlsx"),
)

# ── Lazy-load sentence-transformer (heavy, load once) ────────────────────────
_EMBED_MODEL = None

def _get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_skills_from_text(text: str) -> set:
    """Match all known skills against a block of text using word-boundary regex."""
    text_lower = text.lower()
    found = set()
    for skill in SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found.add(skill)
    return found


def _semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Cosine similarity between two texts using sentence-transformers.
    Returns float in [0, 1]. Returns 0 if either text is empty.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    model = _get_embed_model()
    embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
    sim = sk_cosine([embeddings[0]], [embeddings[1]])[0][0]
    return float(np.clip(sim, 0.0, 1.0))


# Degree keyword buckets for rule-based education scoring
_DEGREE_LEVELS = {
    "bachelors": ["b.tech", "b.e", "b.sc", "bachelor", "btech", "be,", "undergraduate"],
    "masters":   ["m.tech", "m.sc", "m.s", "master", "mtech", "postgraduate"],
    "phd":       ["phd", "ph.d", "doctorate"],
}
_CS_FIELDS = [
    "computer science", "information technology", "software engineering",
    "electronics", "electrical", "cse", "ece", "ise", "it,", "cs,",
]


# ─────────────────────────────────────────────────────────────────────────────
# COMPONENT SCORERS
# ─────────────────────────────────────────────────────────────────────────────

def _score_skills(resume: dict, jd_text: str) -> tuple:
    """
    Skills match: 40 pts.

    Formula:
      Let R = resume skills, J = JD skills
      matched = R ∩ J
      score = sigmoid_scaled(|matched| / |J|) * 40

    We use a soft sigmoid scaling instead of raw ratio to:
      - reward partial match more fairly
      - avoid cliff at 0 when JD has many niche skills

    sigmoid_scaled(x) = 2 / (1 + exp(-4x)) - 1   → maps [0,1] → [0,1]
    (steeper than standard sigmoid near 0, fair for sparse matches)
    """
    resume_skills = set(resume.get("skills", []))
    jd_skills = _extract_skills_from_text(jd_text)

    if not jd_skills:
        return 20.0, resume_skills, set(), jd_skills  # neutral

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    ratio = len(matched) / len(jd_skills)

    # Sigmoid scaling: smoother reward curve
    scaled = 2.0 / (1.0 + math.exp(-4.0 * ratio)) - 1.0
    score = round(min(scaled * 40.0, 40.0), 2)

    return score, matched, missing, jd_skills


def _score_hot_skills(resume: dict, jd_skills: set) -> float:
    """
    Hot skills bonus: 10 pts.

    hot_in_jd  = JD skills that are also "hot" (in-demand)
    hot_resume = resume hot skills
    matched_hot = hot_resume ∩ hot_in_jd

    If JD has no hot skills → neutral score 5.
    Else: score = (|matched_hot| / |hot_in_jd|) * 10
    """
    hot_in_jd = jd_skills & HOT_SKILLS
    resume_hot = set(resume.get("hot_skills", []))
    hot_matched = resume_hot & hot_in_jd

    if not hot_in_jd:
        return 5.0  # JD doesn't specify hot skills → neutral

    ratio = len(hot_matched) / len(hot_in_jd)
    return round(min(ratio * 10.0, 10.0), 2)


def _score_experience(resume: dict, jd_text: str) -> float:
    """
    Experience relevance: 20 pts.
    Semantic cosine similarity between resume experience/projects text and JD.
    For students who lack formal experience, projects are used as fallback.

    score = sim * 20
    Bonus: +2 if years/duration mentions found in experience (shows depth)
    """
    raw = resume.get("raw_sections", {})
    exp_text = raw.get("experience", "").strip()

    # Student fallback: no experience → use projects
    if not exp_text:
        exp_text = raw.get("projects", "").strip()

    sim = _semantic_similarity(exp_text, jd_text)
    score = sim * 20.0

    # Small bonus for quantified experience (numbers/years/metrics)
    if exp_text and re.search(r'\d+\s*(year|month|%|users|ms|x\b)', exp_text, re.I):
        score = min(score + 1.5, 20.0)

    return round(score, 2)


def _score_education(resume: dict, jd_text: str) -> tuple:
    """
    Education: 10 pts. Rule-based.

    Points breakdown:
      4 pts — has an education section at all
      3 pts — degree level mentioned in resume matches JD expectation
      3 pts — CS/Engineering field detected in resume
    """
    raw = resume.get("raw_sections", {})
    edu_text = raw.get("education", "").lower().strip()
    jd_lower = jd_text.lower()

    if not edu_text:
        return 0.0, "No education section"

    score = 4.0  # base for having education section
    notes = []

    # Degree level match (3 pts)
    degree_score = 0
    for level, kws in _DEGREE_LEVELS.items():
        in_resume = any(kw in edu_text for kw in kws)
        in_jd = any(kw in jd_lower for kw in kws)
        if in_resume and in_jd:
            degree_score = 3
            notes.append(f"degree level match ({level})")
            break
        elif in_resume:
            degree_score = 2  # has degree, JD doesn't restrict
            notes.append("has degree (JD has no level requirement)")
            break

    # CS field match (3 pts)
    field_score = 0
    resume_has_cs = any(kw in edu_text for kw in _CS_FIELDS)
    jd_wants_cs = any(kw in jd_lower for kw in _CS_FIELDS)

    if resume_has_cs:
        field_score = 3
        notes.append("CS/engineering field detected")
    elif jd_wants_cs and not resume_has_cs:
        notes.append("JD prefers CS field — not found in resume")

    total = min(score + degree_score + field_score, 10.0)
    return round(total, 2), "; ".join(notes) or "education present"


def _score_projects(resume: dict, jd_text: str) -> float:
    """
    Projects relevance: 10 pts.
    Cosine similarity between projects section and JD.
    """
    proj_text = resume.get("raw_sections", {}).get("projects", "").strip()
    sim = _semantic_similarity(proj_text, jd_text)
    return round(min(sim * 10.0, 10.0), 2)


def _score_completeness(resume: dict) -> tuple:
    """
    Completeness: 10 pts. 2 pts per required section.

    Required: skills, experience OR projects, education, contact email, summary/objective
    """
    sections = set(resume.get("sections_detected", []))
    checks = {
        "skills":              bool(resume.get("skills")),
        "experience/projects": ("experience" in sections or "projects" in sections),
        "education":           "education" in sections,
        "contact":             bool(resume.get("contact", {}).get("email")),
        "summary":             ("summary" in sections or "header" in sections),
    }
    missing = [k for k, ok in checks.items() if not ok]
    score = sum(2 for ok in checks.values() if ok)
    return float(score), missing


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _build_recommendations(
    skills_score, hot_score, exp_score, edu_score, proj_score, comp_score,
    matched_skills, missing_skills, jd_skills, missing_sections,
    resume: dict, jd_text: str
) -> list:
    recs = []

    # Skills
    if skills_score < 16:  # < 40% of 40
        top_missing = sorted(missing_skills)[:8]
        recs.append(
            f"Critical: Only {len(matched_skills)}/{len(jd_skills)} JD skills matched. "
            f"Add these skills to your resume: {', '.join(top_missing)}."
        )
    elif skills_score < 28:  # < 70% of 40
        top_missing = sorted(missing_skills)[:5]
        if top_missing:
            recs.append(
                f"Moderate skills match. Consider adding: {', '.join(top_missing)}."
            )

    # Hot skills
    hot_in_jd = jd_skills & HOT_SKILLS
    resume_hot = set(resume.get("hot_skills", []))
    hot_missing = hot_in_jd - resume_hot
    if hot_score < 5 and hot_in_jd:
        recs.append(
            f"Missing in-demand skills that JD wants: {', '.join(sorted(hot_missing)[:6])}. "
            "These carry extra weight in ATS ranking."
        )
    elif hot_score == 5.0 and not hot_in_jd:
        recs.append(
            "JD has no specific hot-skill requirement, but adding trending skills "
            f"(e.g., {', '.join(sorted(HOT_SKILLS)[:5])}) boosts general ATS rank."
        )

    # Experience
    if exp_score < 8:
        recs.append(
            "Experience section scores low. Quantify impact: use numbers, %, durations. "
            "Mirror JD keywords in your experience bullet points."
        )
    elif exp_score < 14:
        recs.append(
            "Experience partially matches JD. Add more role-specific keywords from the JD."
        )

    # Education
    if edu_score < 5:
        recs.append(
            "Education section is weak or missing. Add your degree, institution, GPA, "
            "and relevant coursework."
        )

    # Projects
    if proj_score < 4:
        jd_tech = sorted(jd_skills & SKILLS)[:6]
        recs.append(
            f"Projects don't align with JD. Build or highlight projects that use: "
            f"{', '.join(jd_tech if jd_tech else ['technologies mentioned in JD'])}."
        )

    # Completeness
    if comp_score < 8:
        recs.append(
            f"Resume missing sections: {', '.join(missing_sections)}. "
            "Add them — ATS systems penalise incomplete resumes."
        )

    if not recs:
        recs.append(
            "Strong match! Tailor your summary/objective directly to this JD for max impact."
        )

    return recs


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCORER
# ─────────────────────────────────────────────────────────────────────────────

def score(parsed_resume: dict, job_description: str) -> dict:
    """
    ATS scoring entry point.

    Parameters
    ----------
    parsed_resume   : dict — output of resume_parser.parse_resume()
    job_description : str  — raw JD text

    Returns
    -------
    dict with keys:
        total_score     : float  (0–100)
        breakdown       : dict   (per-category scores)
        matched_skills  : list
        missing_skills  : list   (in JD, not in resume)
        jd_skills_found : list   (all skills extracted from JD)
        recommendations : list[str]
    """
    jd = job_description.strip()

    # Component scores
    skills_score, matched, missing, jd_skills = _score_skills(parsed_resume, jd)
    hot_score    = _score_hot_skills(parsed_resume, jd_skills)
    exp_score    = _score_experience(parsed_resume, jd)
    edu_score, _ = _score_education(parsed_resume, jd)
    proj_score   = _score_projects(parsed_resume, jd)
    comp_score, missing_sections = _score_completeness(parsed_resume)

    total = round(
        min(skills_score + hot_score + exp_score + edu_score + proj_score + comp_score, 100.0),
        1
    )

    breakdown = {
        "skills_match (40)":       skills_score,
        "hot_skills_bonus (10)":   hot_score,
        "experience (20)":         exp_score,
        "education (10)":          edu_score,
        "projects (10)":           proj_score,
        "completeness (10)":       comp_score,
    }

    recommendations = _build_recommendations(
        skills_score, hot_score, exp_score, edu_score, proj_score, comp_score,
        matched, missing, jd_skills, missing_sections,
        parsed_resume, jd
    )

    return {
        "total_score":     total,
        "breakdown":       breakdown,
        "matched_skills":  sorted(matched),
        "missing_skills":  sorted(missing),
        "jd_skills_found": sorted(jd_skills),
        "recommendations": recommendations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TEST / DEMO
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_JD = """
Software Engineering Intern — Backend & ML Platform

We are looking for a motivated software engineering intern to join our backend
and machine learning platform team.

Responsibilities:
- Design and implement RESTful APIs using Python (FastAPI or Django).
- Work with relational databases (PostgreSQL, MySQL) and write optimised SQL queries.
- Contribute to ML pipelines: data preprocessing, model training, evaluation.
- Containerise services using Docker and deploy on Kubernetes or AWS.
- Write unit tests and participate in code reviews via GitHub.
- Collaborate using Git for version control in an Agile environment.

Requirements:
- Pursuing a B.Tech / B.E. / B.Sc. in Computer Science, IT, or related field.
- Strong programming in Python and Java.
- Familiarity with SQL and NoSQL databases (PostgreSQL, MongoDB).
- Understanding of REST APIs and HTTP protocols.
- Experience with Git, GitHub.
- Bonus: Docker, Kubernetes, scikit-learn, PyTorch, NLP, computer vision.
- Good problem-solving and communication skills.
"""

