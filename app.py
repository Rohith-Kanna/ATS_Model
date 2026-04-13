from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
import uvicorn

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from extractor import extract_text
from resume_parser import parse_resume
from scorer import score

app = FastAPI(title="ATS Resume Scorer API", version="1.0.0")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/parse")
async def parse(resume: UploadFile):
    """
    Input: multipart/form-data with 'resume' PDF file
    Output: parsed resume dict
    """
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    # Save temp, extract, delete
    tmp_path = os.path.join(_HERE, "tmp_resume.pdf")
    with open(tmp_path, "wb") as f:
        f.write(await resume.read())

    try:
        text = extract_text(tmp_path)
        parsed = parse_resume(text)
        # Don't send raw_sections to API consumer — too heavy
        parsed.pop("raw_sections", None)
        return JSONResponse(content=parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/score")
async def score_resume(resume: UploadFile, job_description: str = Form(...)):
    """
    Input: multipart/form-data
        - 'resume': PDF file
        - 'job_description': string (form field)
    Output: ATS score + recommendations
    """
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is empty")

    tmp_path = os.path.join(_HERE, "tmp_resume.pdf")
    with open(tmp_path, "wb") as f:
        f.write(await resume.read())

    try:
        text = extract_text(tmp_path)
        parsed = parse_resume(text)
        result = score(parsed, job_description)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)