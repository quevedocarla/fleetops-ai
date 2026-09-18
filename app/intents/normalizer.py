import re
import unicodedata


TYPO_REPLACEMENTS = {
    "sstatus": "status",
    "staus": "status",
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    normalized = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )
    normalized = normalized.lower().strip()
    return re.sub(r"\s+", " ", normalized)


def normalize_user_message(text: str) -> str:
    normalized = normalize_text(text)
    for wrong, right in TYPO_REPLACEMENTS.items():
        normalized = re.sub(
            rf"\b{re.escape(wrong)}\b",
            right,
            normalized,
        )
    return normalized


def extract_service_order_id(message: str) -> int | None:
    text = normalize_user_message(message)
    match = re.search(
        r"\b(?:os|ordem(?:\s+de\s+servico)?)\s*[:#-]?\s*(\d+)\b",
        text,
        flags=re.IGNORECASE,
    )
    return int(match.group(1)) if match else None
