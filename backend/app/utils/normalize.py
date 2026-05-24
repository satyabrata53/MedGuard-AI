import re
import unicodedata


def normalize_drug_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9+/-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def interaction_key(a: str, b: str) -> str:
    left, right = sorted([normalize_drug_name(a), normalize_drug_name(b)])
    return f"{left}::{right}"
