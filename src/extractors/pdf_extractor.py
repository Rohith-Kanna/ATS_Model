import os
from PyPDF2 import PdfReader
from src.extractors.base_extractor import BaseExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PDFExtractor(BaseExtractor):
    def extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"No such file: '{file_path}'")
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            logger.debug(f"Successfully extracted {len(text)} characters from PDF: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise Exception(f"Failed to parse PDF: {e}")
