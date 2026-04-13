import pandas as pd
import re
import os


# Stopwords — generic words that slip through skill matching
SKILL_STOPWORDS = {
    "it", "sc", "bonus", "contribute", "reviews", "queries", "protocols",
    "design", "training", "software", "engineering", "programming", "databases",
    "skills", "code", "data", "learning", "pipelines", "version control",
    "communication", "communication skills", "agile environment"
}
# Singleton cache
_cache = {}



# Anchor paths to THIS file's directory, so it works from any CWD
_HERE = os.path.dirname(os.path.abspath(__file__))

def load_skill_set(skills_csv_path, tech_xlsx_path):
    key = (skills_csv_path, tech_xlsx_path)
    if key in _cache:
        return _cache[key]

    # --- skills.csv ---
    df_skills = pd.read_csv(skills_csv_path)
    df_skills.columns = ["skill"]
    df_skills["skill"] = df_skills["skill"].str.strip().str.lower()
    df_skills = df_skills[df_skills["skill"].str.len() > 1]
    general_skills = set(df_skills["skill"].dropna().tolist())

    # --- Technology_Skills.xlsx ---
    df_tech = pd.read_excel(tech_xlsx_path, sheet_name="Technology Skills")
    df_tech["Example"] = df_tech["Example"].str.strip().str.lower()
    tech_skills = set(df_tech["Example"].dropna().tolist())

    # hot tech only (optional — Y = in-demand)
    hot_skills = set(
        df_tech[df_tech["Hot Technology"] == "Y"]["Example"]
        .str.lower().dropna().tolist()
    )

    all_skills = general_skills | tech_skills



    # Filter stopwords
    all_skills = (general_skills | tech_skills) - SKILL_STOPWORDS
    hot_skills = hot_skills - SKILL_STOPWORDS
    
    _cache[key] = (all_skills, hot_skills)
    return all_skills, hot_skills


