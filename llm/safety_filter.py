import re

FORBIDDEN_PHRASES = [
    "should be administered",
    "recommended dose",
    "prescribe",
    "give to the patient",
    "effective treatment for",
    "proven to treat",
    "will cure",
]

DOSAGE_PATTERN = r"\d+\s*(mg|mcg|g|IU)"

def scan_for_safety_violations(text: str) -> bool:
    """Returns True if any forbidden clinical recommendation language is found."""
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text.lower():
            return True
    if re.search(DOSAGE_PATTERN, text):
        return True
    return False

def sanitize_response(text: str) -> str:
    """
    Scans and potentially flags text for rewriting.
    In the full implementation, this triggers a second LLM call.
    """
    if scan_for_safety_violations(text):
        # Trigger rewrite logic (omitted in skeleton)
        return "[REWRITTEN FOR SAFETY] " + text 
    return text
