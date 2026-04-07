import fitz
import os

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
        print(f"Extracted: {filename}")
        return text
    else:
        print(f"Error: File '{filename}' not found in {folder_path}")
        return None

def extract_all_resumes(folder_path):
    results = {}
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            path = os.path.join(folder_path, file)
            results[file] = extract_text(path)
            print(f"Extracted: {file}")
    return results

def list_available_resumes(folder_path):
    resumes = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    return resumes

if __name__ == "__main__":
    folder = "Resume Samples"
    
    # Extract Rohith Kanna's resume
    rohith_text = extract_single_resume(folder, "RohithKanna_Resume.pdf")
    if rohith_text:
        print(f"\n--- RohithKanna_Resume.pdf ---\n")
        print(rohith_text)