import re

_ISO_UTC_TS_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
)


def normalize_tts_text(text: str, *, strip_timestamps: bool = True) -> str:
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in normalized.split("\n")]

    cleaned: list[str] = []
    for line in lines:
        if not line:
            continue
        if strip_timestamps and _ISO_UTC_TS_LINE_RE.match(line):
            continue
        cleaned.append(line)

    return " ".join(cleaned).strip()

