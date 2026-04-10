import pytest
from src.extractors.txt_extractor import TXTExtractor
import os

def test_txt_extractor_success(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World!")
    
    extractor = TXTExtractor()
    content = extractor.extract_text(str(test_file))
    assert content == "Hello World!"

def test_txt_extractor_not_found():
    extractor = TXTExtractor()
    with pytest.raises(FileNotFoundError):
        extractor.extract_text("non_existent.txt")
