import hashlib

def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())

def generate_content_hash(meeting, state):
    """
    Generates a SHA-256-based hash to detect any content change
    based on state-specific relevant fields.
    """
    if state == "B":
        parts = [
            clean(meeting.get("Enter the seminar topic:", "")),
            clean(meeting.get("Enter speaker name here:", "")),
            clean(meeting.get("Choose the DATE when the seminar will be held:", "")),
            clean(meeting.get("Seminar START time:", "")),
        ]
    elif state == "C":
        parts = [
            clean(meeting.get("Enter the seminar topic:", "")),
            clean(meeting.get("Enter speaker name here:", "")),
            clean(meeting.get("Please upload a PHOTO of the speaker here:", "")),  # use URL only
            clean(meeting.get("Enter the abstract of the seminar: (in 150 words)", "")),
        ]
    else:
        return None  # No hash for state A

    base_str = "|".join(parts)
    return hashlib.sha256(base_str.encode()).hexdigest()[:16]  # 64-bit hash
