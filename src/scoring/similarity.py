from typing import Set, Tuple, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ScoringEngine:
    def __init__(self):
        # We define common english stop words for the vectorizer just in case.
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculates the Cosine Similarity between two texts representing the overall match.
        
        Args:
            text1 (str): e.g., Job Description.
            text2 (str): e.g., Resume.
            
        Returns:
            float: Similarity score between 0.0 and 100.0.
        """
        if not text1.strip() or not text2.strip():
            logger.warning("One of the text contents is empty, returning similarity 0.0")
            return 0.0
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            score = round(similarity * 100, 2)
            logger.debug(f"Calculated TF-IDF similarity score: {score}%")
            return score
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def evaluate_keywords(self, jd_keywords: Set[str], resume_keywords: Set[str]) -> Tuple[Set[str], Set[str]]:
        """
        Finds the matched and missing keywords.
        
        Args:
            jd_keywords (Set[str]): Target skills.
            resume_keywords (Set[str]): Candidate skills.
            
        Returns:
            Tuple[Set[str], Set[str]]: (matched_keywords, missing_keywords)
        """
        matched = jd_keywords.intersection(resume_keywords)
        missing = jd_keywords.difference(resume_keywords)
        
        logger.debug(f"Found {len(matched)} matching keywords and {len(missing)} missing keywords.")
        return matched, missing

    def generate_report(self, jd_text: str, resume_text: str, jd_keywords: Set[str], resume_keywords: Set[str]) -> Dict[str, Any]:
        """
        Generates a comprehensive structured report combining similarity score and keyword matching.
        """
        similarity_score = self.calculate_similarity(jd_text, resume_text)
        matched, missing = self.evaluate_keywords(jd_keywords, resume_keywords)
        
        # Penalize overall score if a large percentage of keywords are missing?
        # A simple hybrid approach could be:
        # Final Score = (0.5 * TFIDF Score) + (0.5 * Keyword Match Percentage)
        
        keyword_match_pct = 0.0
        if jd_keywords:
            keyword_match_pct = (len(matched) / len(jd_keywords)) * 100
            
        hybrid_score = round((similarity_score * 0.4) + (keyword_match_pct * 0.6), 2)
        
        return {
            "tf_idf_similarity_score": similarity_score,
            "keyword_match_percentage": round(keyword_match_pct, 2),
            "final_ats_score": hybrid_score,
            "matched_keywords": sorted(list(matched)),
            "missing_keywords": sorted(list(missing))
        }
