"""Single controlled-text catalog shared by the frontend and PDF renderer."""

import json
import re
from pathlib import Path

RU: dict[str, str] = json.loads((Path(__file__).parent / "ru.json").read_text(encoding="utf-8"))
RANKING_TEMPLATE = (
    "{severity} severity; urgency {urgency}/3; observed relevance {relevance}/2; "
    "{confidence} evidence. Ties use newest issue observation, then stable fingerprint. "
    "These are ordering labels, not a risk score."
)
RANKING_PATTERN = (
    r"(High|Medium|Low|Info) severity; urgency ([0-3])/3; observed relevance ([0-2])/2; "
    r"(conclusive|contextual) evidence\. Ties use newest issue observation, "
    r"then stable fingerprint\. These are ordering labels, not a risk score\."
)


def translate(text: str, locale: str) -> str:
    if locale != "ru":
        return text
    key = " ".join(text.split())
    if key in RU:
        return RU[key]
    match = re.fullmatch(RANKING_PATTERN, key)
    if not match:
        return text
    return RU[RANKING_TEMPLATE].format(
        severity=translate(match[1].lower(), locale),
        urgency=match[2],
        relevance=match[3],
        confidence=translate(match[4], locale),
    )
