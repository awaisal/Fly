import re
from typing import Optional

URL_RE = re.compile(r"(https?://\S+|t\.me/\S+|www\.\S+)", re.IGNORECASE)

def has_link(text: Optional[str]) -> bool:
    if not text:
        return False
    return bool(URL_RE.search(text))

def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())
