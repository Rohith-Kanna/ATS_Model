import fitz
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def extract_single_resume(folder_path, filename):
    path = os.path.join(folder_path, filename)
    if os.path.exists(path):
        text = extract_text(path)
        return text
    else:
        return None

def extract_all_resumes(folder_path):
    results = {}
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            path = os.path.join(folder_path, file)
            results[file] = extract_text(path)
    return results

def list_available_resumes(folder_path):
    resumes = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    return resumes
