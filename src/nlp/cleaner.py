import re
import string

def clean_text(text: str) -> str:
    """
    Cleans raw text by removing non-alphanumeric characters (except basic punctuation),
    excessive whitespace, and converting to lowercase.
    
    Args:
        text (str): The raw text extracted from a document.
        
    Returns:
        str: Cleaned and normalized text.
    """
    if not text:
        return ""
        
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep basic punctuation like commas, periods, hyphens
    text = re.sub(r'[^a-zA-Z0-9\s,\.-]', ' ', text)
    
    # Remove extra spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
