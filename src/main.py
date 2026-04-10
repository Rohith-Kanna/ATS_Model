import argparse
import sys
import json
from pathlib import Path

# Add project root to python path to allow absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.txt_extractor import TXTExtractor
from src.extractors.docx_extractor import DocxExtractor
from src.nlp.cleaner import clean_text
from src.nlp.entity_extractor import EntityExtractor
from src.scoring.similarity import ScoringEngine
from src.utils.logger import get_logger

logger = get_logger("ats_main")

def get_extractor(file_path: str):
    """Factory function to get the appropriate extractor based on file extension."""
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        return PDFExtractor()
    elif ext == 'txt':
        return TXTExtractor()
    elif ext == 'docx':
        return DocxExtractor()
    else:
        logger.error(f"Unsupported file format: {ext}")
        raise ValueError(f"Unsupported file format: {ext}")

def main():
    parser = argparse.ArgumentParser(description="Offline ATS Resume Evaluator")
    parser.add_argument("--resume", required=True, help="Path to the resume file (PDF, TXT, DOCX)")
    parser.add_argument("--jd", required=True, help="Path to the job description file (PDF, TXT, DOCX)")
    parser.add_argument("--output", default="json", choices=["json", "text"], help="Output format")
    
    args = parser.parse_args()

    try:
        # 1. Extraction
        logger.info("Extracting text from documents...")
        resume_extractor = get_extractor(args.resume)
        jd_extractor = get_extractor(args.jd)
        
        raw_resume = resume_extractor.extract_text(args.resume)
        raw_jd = jd_extractor.extract_text(args.jd)
        
        # 2. Cleaning
        logger.info("Cleaning and normalizing text...")
        clean_resume = clean_text(raw_resume)
        clean_jd = clean_text(raw_jd)
        
        # 3. NLP Extraction
        logger.info("Extracting keywords and entities (this might take a moment)...")
        nlp_engine = EntityExtractor()
        resume_keywords = nlp_engine.extract_keywords(clean_resume)
        jd_keywords = nlp_engine.extract_keywords(clean_jd)
        
        # 4. Scoring
        logger.info("Calculating ATS Score...")
        scoring_engine = ScoringEngine()
        report = scoring_engine.generate_report(clean_jd, clean_resume, jd_keywords, resume_keywords)
        
        # 5. Output
        if args.output == "json":
            print(json.dumps(report, indent=4))
        else:
            print("\n" + "="*40)
            print("         ATS EVALUATION REPORT")
            print("="*40)
            print(f"Final ATS Score  : {report['final_ats_score']}%")
            print(f"TF-IDF Match     : {report['tf_idf_similarity_score']}%")
            print(f"Keyword Coverage : {report['keyword_match_percentage']}%")
            print("-" * 40)
            print(f"MATCHED KEYWORDS ({len(report['matched_keywords'])}):")
            print(", ".join(report['matched_keywords']) if report['matched_keywords'] else "None")
            print("-" * 40)
            print(f"MISSING REQUIREMENTS ({len(report['missing_keywords'])}):")
            print(", ".join(report['missing_keywords']) if report['missing_keywords'] else "None")
            print("="*40 + "\n")
            
    except Exception as e:
        logger.critical(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
