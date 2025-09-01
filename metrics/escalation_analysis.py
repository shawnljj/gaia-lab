"""
Custom metric for evaluating escalation decision-making in support responses.
"""

import re
from typing import Dict, Any


def evaluate_escalation_decision(prediction: str, target: str) -> Dict[str, Any]:
    """
    Evaluate if the response correctly identifies when to escalate issues.
    
    Args:
        prediction: The LLM's response
        target: The expected response (for reference)
    
    Returns:
        Dict with score and details
    """
    score = 0.0
    feedback = []
    
    # Check if escalation is mentioned when needed
    escalation_keywords = [
        "escalate", "specialist", "technical team", "supervisor",
        "manager", "expert", "advanced support", "tier 2"
    ]
    
    # Determine if target suggests escalation
    target_suggests_escalation = any(keyword in target.lower() for keyword in escalation_keywords)
    prediction_suggests_escalation = any(keyword in prediction.lower() for keyword in escalation_keywords)
    
    # Score based on escalation appropriateness
    if target_suggests_escalation and prediction_suggests_escalation:
        score += 0.4
        feedback.append("✓ Correctly identified escalation need")
    elif not target_suggests_escalation and not prediction_suggests_escalation:
        score += 0.4
        feedback.append("✓ Correctly handled without escalation")
    elif target_suggests_escalation and not prediction_suggests_escalation:
        feedback.append("✗ Missed required escalation")
    else:
        feedback.append("✗ Unnecessary escalation suggested")
    
    # Check for proper escalation process
    if prediction_suggests_escalation:
        process_indicators = [
            "connect you", "transfer", "forward", "specialist",
            "technical team", "next level", "appropriate team"
        ]
        proper_process = any(indicator in prediction.lower() for indicator in process_indicators)
        if proper_process:
            score += 0.3
            feedback.append("✓ Proper escalation process")
        else:
            feedback.append("✗ Unclear escalation process")
    
    # Check for information gathering before escalation
    info_gathering = [
        "details", "information", "tell me", "could you",
        "what", "when", "how", "which", "account", "system"
    ]
    gathers_info = any(phrase in prediction.lower() for phrase in info_gathering)
    if gathers_info:
        score += 0.3
        feedback.append("✓ Gathers relevant information")
    else:
        feedback.append("✗ Doesn't gather sufficient information")
    
    return {
        "score": min(score, 1.0),
        "feedback": "; ".join(feedback),
        "details": {
            "escalation_needed": target_suggests_escalation,
            "escalation_identified": prediction_suggests_escalation,
            "gathers_information": gathers_info
        }
    }
