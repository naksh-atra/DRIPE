"""
Safety filter for DRIPE v2 LLM output.
Scans structured explanations for forbidden clinical language.
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)

FORBIDDEN_PATTERNS = [
    r"should be (administered|prescribed|taken|used)",
    r"recommend(ed|ing|ation)?",
    r"dose of",
    r"dosage",
    r"clinical (trial|study) suggests",
    r"patient should",
    r"prescribe",
]


SYSTEM_PROMPTS = [
    r"you are (a|an) (helpful|AI|clinical|medical) assistant",
]


def scan_for_safety_violations(text: str) -> List[str]:
    """Scan text for forbidden clinical language patterns."""
    violations = []
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(f"Pattern matched: '{pattern}'")
    return violations


def sanitize_response(summary: str, violations: List[str]) -> str:
    """Remove or flag safety violations from summary text."""
    if not violations:
        return summary
    logger.warning(f"Safety violations detected: {violations}")
    return summary + " [Safety warning: contains clinical language detected]"
