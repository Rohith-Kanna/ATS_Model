import os
import docx
from src.extractors.base_extractor import BaseExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DocxExtractor(BaseExtractor):
    def extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"No such file: '{file_path}'")
            
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            logger.debug(f"Successfully extracted {len(text)} characters from DOCX: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            raise Exception(f"Failed to parse DOCX: {e}")
