"""Single controlled-text catalog shared by the frontend and PDF renderer."""

import json
import re
from pathlib import Path

CATALOGS: dict[str, dict[str, str]] = {
    locale: json.loads((Path(__file__).parent / f"{locale}.json").read_text(encoding="utf-8"))
    for locale in ("en", "ru", "kk")
}
RU = CATALOGS["ru"]
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
    catalog = CATALOGS.get(locale, CATALOGS["en"])
    key = " ".join(text.split())
    if key in catalog:
        return catalog[key]
    match = re.fullmatch(RANKING_PATTERN, key)
    if not match:
        return text
    return catalog[RANKING_TEMPLATE].format(
        severity=translate(match[1].lower(), locale),
        urgency=match[2],
        relevance=match[3],
        confidence=translate(match[4], locale),
    )


def message(key: str, locale: str, **values: object) -> str:
    """Named placeholders only; never evaluate customer content as a template."""
    return translate(key, locale).format_map(values)
