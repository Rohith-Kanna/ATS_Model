import spacy
from typing import Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EntityExtractor:
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initializes the SpaCy model for NLP tasks.
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.debug(f"Successfully loaded SpaCy model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load SpaCy model '{model_name}'. Is it installed? Try running 'python -m spacy download {model_name}'")
            raise e

    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extracts important noun chunks, named entities, and proper nouns from the text
        to represent technical skills or key requirements.
        
        Args:
            text (str): The cleaned text.
            
        Returns:
            Set[str]: A set of extracted keywords/phrases in lowercase.
        """
        doc = self.nlp(text)
        keywords = set()
        
        # Extract predefined entities (like ORG, PERSON, GPE, PRODUCT)
        # But for tech resumes, we often care more about noun chunks and specific technical nouns.
        
        # 1. Add Noun Chunks (e.g., "machine learning", "cloud infrastructure")
        for chunk in doc.noun_chunks:
            # Filter out very short or purely stopword chunks
            words = [token for token in chunk if not token.is_stop and not token.is_punct]
            if words:
                phrase = " ".join([w.text.lower() for w in words])
                # Only add if it's somewhat substantive
                if len(phrase) > 2:
                    keywords.add(phrase)
                    
        # 2. Add Proper Nouns and key nouns that might not be captured purely in chunks
        for token in doc:
            if not token.is_stop and not token.is_punct and len(token.text) > 2:
                if token.pos_ in ['PROPN', 'NOUN']:
                    keywords.add(token.text.lower())
                    
        return keywords
