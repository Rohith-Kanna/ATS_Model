# ATS Resume Scorer & Analyzer

A technical tool to parse PDF resumes, extract key sections and technical skills, and score them against job descriptions using a combination of deterministic keyword overlap (Jaccard similarity) and semantic vector embeddings (Cosine similarity via SentenceTransformers).

This project exposes both a **Streamlit Web UI** for interactive analysis and a **FastAPI REST API** for programmatical integration.

---

## Architecture & Project Structure

```
ATS_Model/
├── app.py               # FastAPI backend exposing scoring & parsing endpoints
├── streamlit_app.py     # Streamlit interactive frontend dashboard
├── extractor.py         # PDF text extraction utilizing PyMuPDF (fitz)
├── resume_parser.py     # Text segmenter and regex contact/skill extractor
├── scorer.py            # Main scoring engine and recommendation generator
├── skill_loader.py      # Technical taxonomy loader (filters, caches, and parses datasets)
├── requirements.txt     # Python package dependencies
└── skills_dataset/      # Structured directories containing technical skill taxonomies
    ├── skills.csv
    └── Technology Skills.xlsx
```

### Components

1. **`extractor.py`**: Reads raw PDF files using `PyMuPDF (fitz)`.
2. **`skill_loader.py`**: Loads and normalizes technical terms from the datasets.
   - Combines a general skills list (`skills.csv`) and O*NET technology skills (`Technology Skills.xlsx`).
   - Normalizes terms to lowercase, strips trailing spaces, and filters out common stop-words (`SKILL_STOPWORDS` like "data", "software", "engineering", etc.) to prevent false-positive matching.
   - Caches the dataset in memory to minimize I/O overhead.
3. **`resume_parser.py`**: Identifies key sections (`skills`, `experience`, `education`, `projects`, `certifications`, `summary`) using regex headers (constrained by length/boundaries) and parses contact info (email/phone).
4. **`scorer.py`**: Evaluates the extracted sections against the target job description. Implements the scoring logic (detailed below) and generates action-oriented optimization recommendations.
5. **`app.py`**: A FastAPI application providing `/health`, `/parse` (for structural extraction), and `/score` (full ATS evaluation) endpoints.
6. **`streamlit_app.py`**: A front-end interface built with Streamlit and Plotly. Visualizes the ATS score breakdown, details matched/missing skills using UI chips, and displays structured recommendations.

---

## Scoring System & Algorithm (100 Points Total)

The total ATS score is computed as the sum of six distinct component metrics:

### 1. Skills Match (40 Points Max)
Calculates the intersection of skills detected in the resume ($R$) against the skills extracted from the job description ($J$).
- **Formula**:
  $$x = \frac{|R \cap J|}{|J|}$$
  $$\text{Score} = \text{min}\left(\left(\frac{2}{1 + e^{-4x}} - 1\right) \times 40, 40\right)$$
  - Uses a **sigmoid scaling function** rather than a linear ratio. This rewards early/partial keyword matches and prevents severe scoring drops when the job description contains a high volume of niche skills.

### 2. Hot Skills Bonus (10 Points Max)
Evaluates if the candidate possesses in-demand or "hot" technical skills specified in the job description (flagged as `Hot Technology` in `Technology Skills.xlsx`).
- **Formula**:
  $$\text{Score} = \text{min}\left(\frac{|R_{hot} \cap J_{hot}|}{|J_{hot}|} \times 10, 10\right)$$
  - *Fallback*: If the job description does not contain any classified hot skills, a neutral score of **5.0 points** is automatically awarded.

### 3. Experience Relevance (20 Points Max)
Calculates the semantic similarity between the candidate's experience section and the job description using vector embeddings.
- **Model**: SentenceTransformers `all-MiniLM-L6-v2` (cosine similarity on the generated vectors).
- **Fallback**: If the resume lacks an "experience" section, it automatically falls back to embedding the "projects" section (optimized for student profiles).
- **Quantification Bonus**: Adds a **+1.5 point bonus** (capped at 20.0 max) if regular expressions detect numeric metrics, duration units, or percentage markers (e.g., `3 years`, `15%`, `50ms`, `2x`) within the experience description to reward quantifiable impact.

### 4. Education Alignment (10 Points Max)
A rule-based evaluation of academic credentials.
- **Section Presence**: 4 points for having an education section.
- **Degree Level Match**: Up to 3 points if the degree level (Bachelors, Masters, PhD) in the resume matches the requirements mentioned in the job description.
- **Field of Study Match**: Up to 3 points if keywords indicate a computer science, engineering, or related technical field (e.g., `CS`, `IT`, `ECE`, `B.Tech`, etc.).

### 5. Projects Alignment (10 Points Max)
Measures the semantic relevance of the candidate's projects to the job description.
- **Model**: Cosine similarity of `all-MiniLM-L6-v2` embeddings of the `projects` section text vs. job description.

### 6. Profile Completeness (10 Points Max)
Checks for structural presence of essential resume components. Awards **2 points** for each of the following properties detected:
- Skills list
- Experience or Projects section
- Education section
- Valid contact info (email)
- Professional summary or header

---

## Technical Dependencies

The core environment requires Python 3.8+ and the following packages:
- **`PyMuPDF` (`fitz`)**: For raw text extraction from PDF files.
- **`sentence-transformers`**: Pre-trained transformer models for text embeddings (`all-MiniLM-L6-v2`).
- **`scikit-learn`**: Efficient computation of cosine similarity between embeddings.
- **`streamlit` & `plotly`**: For rendering the visual web application.
- **`fastapi` & `uvicorn`**: High-performance ASGI server for hosting REST endpoints.
- **`pandas` & `openpyxl`**: For tabular parsing of the skill databases.

---

## Installation & Setup

### Prerequisites
Make sure you have Python installed (3.9 - 3.11 recommended).

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd ATS_Model
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Interface
```bash
streamlit run streamlit_app.py
```
This launches the application locally. Navigate to the local address outputted in the shell (typically `http://localhost:8501`).

### 5. Run the FastAPI REST Server
```bash
python app.py
```
The API server starts by default on `http://localhost:5000`.

#### API Endpoint Documentation

##### `GET /health`
Returns system status.
- **Response**: `{"status": "ok"}`

##### `POST /parse`
Extracts structured sections from a resume file.
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `resume`: PDF File
- **Response**: Structured JSON containing contact information, detected sections, parsed skills, and hot skills.

##### `POST /score`
Scores a resume against a target job description.
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `resume`: PDF File
  - `job_description`: Plain text string
- **Response**: Full breakdown of the 100-point score, lists of matched/missing skills, and detailed feedback recommendations.
