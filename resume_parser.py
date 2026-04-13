import re
import os
from skill_loader import load_skill_set

_HERE = os.path.dirname(os.path.abspath(__file__))

# Load once at module level
SKILLS, HOT_SKILLS = load_skill_set(
    os.path.join(_HERE, "skills_dataset", "skills.csv"),
    os.path.join(_HERE, "skills_dataset", "Technology Skills.xlsx")
)

# --- Section Headers ---
SECTION_PATTERNS = {
    "skills":      r"\b(skills|technical skills|core competencies|technologies)\b",
    "experience":  r"\b(experience|work experience|employment|internships?)\b",
    "education":   r"\b(education|academic background|qualifications)\b",
    "projects":    r"\b(projects|personal projects|academic projects)\b",
    "certifications": r"\b(certifications?|courses?|training)\b",
    "summary":     r"\b(summary|objective|profile|about me)\b",
}

def detect_sections(text):
    """Split raw resume text into labelled sections."""
    lines = text.splitlines()
    sections = {}
    current_section = "header"
    buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            buffer.append("")
            continue

        matched = None
        for label, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, stripped, re.IGNORECASE) and len(stripped) < 60:
                matched = label
                break

        if matched:
            # Save previous buffer
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = matched
            buffer = []
        else:
            buffer.append(stripped)

    # Save last section
    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def extract_skills_from_text(text):
    """Match skill set against a block of text."""
    text_lower = text.lower()
    found = set()
    for skill in SKILLS:
        # word boundary match to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)
    return found


def extract_contact(text):
    """Pull email and phone from header section."""
    email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone = re.findall(r'[\+\(]?[0-9][0-9\s\-\(\)]{7,}[0-9]', text)
    return {
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None
    }


def parse_resume(text):
    """Full parse. Returns structured dict."""
    sections = detect_sections(text)

    # Skills: check skills section + projects + experience (skills hide everywhere)
    skill_text = " ".join([
        sections.get("skills", ""),
        sections.get("projects", ""),
        sections.get("experience", ""),
    ])
    found_skills = extract_skills_from_text(skill_text)
    hot_found = found_skills & HOT_SKILLS

    contact = extract_contact(sections.get("header", ""))

    return {
        "contact": contact,
        "sections_detected": list(sections.keys()),
        "skills": list(found_skills),
        "hot_skills": list(hot_found),
        "raw_sections": sections
    }

