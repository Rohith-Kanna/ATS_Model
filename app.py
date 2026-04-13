from flask import Flask, request, jsonify
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from extractor import extract_text
from resume_parser import parse_resume
from scorer import score

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/parse", methods=["POST"])
def parse():
    """
    Input: multipart/form-data with 'resume' PDF file
    Output: parsed resume dict
    """
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files["resume"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400

    # Save temp, extract, delete
    tmp_path = os.path.join(_HERE, "tmp_resume.pdf")
    file.save(tmp_path)

    try:
        text = extract_text(tmp_path)
        parsed = parse_resume(text)
        # Don't send raw_sections to API consumer — too heavy
        parsed.pop("raw_sections", None)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/score", methods=["POST"])
def score_resume():
    """
    Input: multipart/form-data
        - 'resume': PDF file
        - 'job_description': string (form field)
    Output: ATS score + recommendations
    """
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    if "job_description" not in request.form:
        return jsonify({"error": "No job_description provided"}), 400

    file = request.files["resume"]
    jd = request.form["job_description"].strip()

    if not jd:
        return jsonify({"error": "job_description is empty"}), 400
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400

    tmp_path = os.path.join(_HERE, "tmp_resume.pdf")
    file.save(tmp_path)

    try:
        text = extract_text(tmp_path)
        parsed = parse_resume(text)
        result = score(parsed, jd)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)