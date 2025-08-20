"""
Custom metric: JSON validity checker.

Exposes a score(prediction, reference) -> dict that returns
{"score": 0|1, "reason": "..."} depending on whether the prediction is
valid JSON. The reference is unused but accepted for API consistency.
"""

from __future__ import annotations

import json
from typing import Any, Dict


def score(prediction: str, reference: Any = None) -> Dict[str, Any]:
    """Return 1 if prediction parses as JSON, else 0.

    Parameters
    ----------
    prediction: str
        The model output string to validate.
    reference: Any
        Unused placeholder for API parity with other metrics.
    """
    try:
        json.loads(prediction)
        return {"score": 1, "reason": "Valid JSON."}
    except Exception as e:  # noqa: BLE001
        return {"score": 0, "reason": f"Invalid JSON: {e}"}

