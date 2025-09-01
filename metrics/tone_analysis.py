"""
Custom metric for evaluating professional tone in support responses.
"""

import re
from typing import Dict, Any


def evaluate_professional_tone(prediction: str, target: str) -> Dict[str, Any]:
    """
    Evaluate if the response maintains professional, empathetic tone.
    
    Args:
        prediction: The LLM's response
        target: The expected response (for reference)
    
    Returns:
        Dict with score and details
    """
    score = 0.0
    feedback = []
    
    # Check for empathy indicators
    empathy_phrases = [
        "understand", "apologize", "sorry", "frustrating", 
        "appreciate", "help", "assist", "concern"
    ]
    empathy_found = any(phrase in prediction.lower() for phrase in empathy_phrases)
    if empathy_found:
        score += 0.3
        feedback.append("✓ Shows empathy")
    else:
        feedback.append("✗ Lacks empathetic language")
    
    # Check for professional language (no slang, casual terms)
    unprofessional_terms = [
        "yeah", "nope", "gonna", "wanna", "kinda", "sorta",
        "hey", "yo", "sup", "lol", "omg", "wtf"
    ]
    unprofessional_found = any(term in prediction.lower() for term in unprofessional_terms)
    if not unprofessional_found:
        score += 0.2
        feedback.append("✓ Professional language")
    else:
        feedback.append("✗ Contains unprofessional terms")
    
    # Check for solution-oriented approach
    solution_indicators = [
        "let me", "i can", "we can", "try", "step", "solution",
        "resolve", "fix", "help you", "assist you"
    ]
    solution_found = any(indicator in prediction.lower() for indicator in solution_indicators)
    if solution_found:
        score += 0.3
        feedback.append("✓ Solution-oriented")
    else:
        feedback.append("✗ Not solution-focused")
    
    # Check for appropriate length (not too brief, not too verbose)
    word_count = len(prediction.split())
    if 20 <= word_count <= 150:
        score += 0.2
        feedback.append("✓ Appropriate response length")
    else:
        feedback.append(f"✗ Response length issue ({word_count} words)")
    
    return {
        "score": min(score, 1.0),
        "feedback": "; ".join(feedback),
        "details": {
            "empathy_found": empathy_found,
            "professional_language": not unprofessional_found,
            "solution_oriented": solution_found,
            "word_count": word_count
        }
    }
