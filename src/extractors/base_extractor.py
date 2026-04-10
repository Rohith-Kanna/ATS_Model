from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """
    Abstract base class for all file extractors.
    Enforces the implementation of the extract_text method.
    """
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extracts and returns text from a given file.
        
        Args:
            file_path (str): The path to the file.
            
        Returns:
            str: The extracted text.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If there is an issue parsing the file.
        """
        pass
