import pytest
from src.scoring.similarity import ScoringEngine

def test_calculate_similarity():
    engine = ScoringEngine()
    
    # Identical texts should be 100%
    assert engine.calculate_similarity("Hello World", "Hello World") == 100.0
    
    # Disjoint texts should be 0%
    assert engine.calculate_similarity("Apple Banana", "Computer Mouse") == 0.0

def test_evaluate_keywords():
    engine = ScoringEngine()
    jd = {"python", "machine learning", "docker"}
    resume = {"python", "docker", "c++"}
    
    matched, missing = engine.evaluate_keywords(jd, resume)
    
    assert "python" in matched
    assert "docker" in matched
    assert "machine learning" in missing
    assert "c++" not in matched
    assert "c++" not in missing
