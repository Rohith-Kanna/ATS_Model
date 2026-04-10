import os
from src.extractors.base_extractor import BaseExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TXTExtractor(BaseExtractor):
    def extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"No such file: '{file_path}'")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            logger.debug(f"Successfully extracted {len(text)} characters from TXT: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to parse TXT {file_path}: {e}")
            raise Exception(f"Failed to parse TXT: {e}")
