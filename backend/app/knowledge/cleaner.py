import re
import unicodedata
from typing import Tuple


class TranscriptCleaner:
    """
    Deterministic cleaner for podcast transcript dialogues.
    Preserves speaker turns and factual nuance while removing formatting anomalies.
    """

    # Sponsorship & ad boilerplate removal patterns
    AD_PATTERNS = [
        re.compile(r"\(sponsorship message.*?\)", re.IGNORECASE),
        re.compile(r"\[ad break.*?\]", re.IGNORECASE),
        re.compile(r"thank you to our sponsor.*?\n", re.IGNORECASE),
        re.compile(r"brought to you by.*?\n", re.IGNORECASE),
    ]

    @classmethod
    def clean(cls, raw_text: str) -> str:
        if not raw_text:
            return ""

        # 1. Normalize unicode characters (e.g. smart quotes, non-breaking spaces)
        text = unicodedata.normalize("NFKC", raw_text)

        # 2. Strip known sponsorship patterns
        for pattern in cls.AD_PATTERNS:
            text = pattern.sub("", text)

        # 3. Standardize dialogue line breaks (ensure blank line between speaker turns)
        # e.g., "Lenny: Hello\nRahul Vohra: Hi" -> "Lenny: Hello\n\nRahul Vohra: Hi"
        text = re.sub(r"\n([A-Z][A-Za-z\s]+:)", r"\n\n\1", text)

        # 4. Remove excessive consecutive blank lines (> 2 newlines -> 2 newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. Normalize trailing, leading, and multi-space whitespace on each line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        cleaned_text = "\n".join(lines).strip()

        return cleaned_text
