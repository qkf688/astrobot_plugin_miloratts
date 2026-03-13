import re

_ISO_UTC_TS_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
)


_UNICODE_EMOJI_RANGES: tuple[tuple[int, int], ...] = (
    (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols (flags)
    (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x1F700, 0x1F77F),  # Alchemical Symbols (rare but safe)
    (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
    (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
    (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
    (0x1FA00, 0x1FA6F),  # Chess Symbols, etc.
    (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
    (0x2600, 0x26FF),  # Misc symbols
    (0x2700, 0x27BF),  # Dingbats
    (0x2300, 0x23FF),  # Misc Technical (contains emoji like ⏰)
    (0x2B00, 0x2BFF),  # Misc symbols and arrows (⬆️ etc.)
)

_UNICODE_EMOJI_SINGLETONS: frozenset[int] = frozenset(
    {
        0x00A9,  # ©
        0x00AE,  # ®
        0x203C,  # ‼
        0x2049,  # ⁉
        0x2122,  # ™
        0x2139,  # ℹ
        0x3030,  # 〰
        0x3297,  # ㊗
        0x3299,  # ㊙
    }
)

_VS16 = 0xFE0F
_ZWJ = 0x200D
_KEYCAP = 0x20E3
_SKIN_TONE_RANGE = (0x1F3FB, 0x1F3FF)


def _in_ranges(codepoint: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    for start, end in ranges:
        if start <= codepoint <= end:
            return True
    return False


def _is_skin_tone_modifier(codepoint: int) -> bool:
    return _SKIN_TONE_RANGE[0] <= codepoint <= _SKIN_TONE_RANGE[1]


def _is_emoji_base(codepoint: int) -> bool:
    if codepoint in _UNICODE_EMOJI_SINGLETONS:
        return True
    return _in_ranges(codepoint, _UNICODE_EMOJI_RANGES)


def extract_unicode_emojis(text: str) -> tuple[str, str]:
    """尽力而为从文本中抽取 Unicode emoji。

    Returns:
        tuple[str, str]: (emoji_text, remaining_text)

    Notes:
        - 对 ZWJ/VS16/肤色修饰符/国旗等常见组合做基础支持。
        - remaining_text 会用单个空格替换 emoji，避免英文单词被直接拼接。
    """
    if not text:
        return "", ""

    emoji_parts: list[str] = []
    remaining_parts: list[str] = []

    i = 0
    n = len(text)

    def peek(offset: int = 0) -> int | None:
        idx = i + offset
        if idx >= n:
            return None
        return ord(text[idx])

    while i < n:
        cp = ord(text[i])

        # Keycap sequence: [0-9#*] (VS16)? KEYCAP
        if text[i] in "0123456789#*":
            cp1 = peek(1)
            cp2 = peek(2)
            if cp1 == _VS16 and cp2 == _KEYCAP:
                emoji_parts.append(text[i : i + 3])
                remaining_parts.append(" ")
                i += 3
                continue
            if cp1 == _KEYCAP:
                emoji_parts.append(text[i : i + 2])
                remaining_parts.append(" ")
                i += 2
                continue

        # Flags: two regional indicators
        if 0x1F1E6 <= cp <= 0x1F1FF:
            cp1 = peek(1)
            if cp1 is not None and 0x1F1E6 <= cp1 <= 0x1F1FF:
                emoji_parts.append(text[i : i + 2])
                remaining_parts.append(" ")
                i += 2
                continue

        if not _is_emoji_base(cp):
            remaining_parts.append(text[i])
            i += 1
            continue

        # General emoji sequence with optional VS16 / skin tone and optional ZWJ joins
        start = i
        i += 1

        # Optional VS16
        if peek(0) == _VS16:
            i += 1

        # Optional skin tone modifier
        cp_mod = peek(0)
        if cp_mod is not None and _is_skin_tone_modifier(cp_mod):
            i += 1

        # Optional keycap (rare for non-digit but keep safe)
        if peek(0) == _KEYCAP:
            i += 1

        # Handle ZWJ sequences: (ZWJ emoji_base ...)*
        while peek(0) == _ZWJ:
            # Must have another emoji base after ZWJ, otherwise stop
            cp_after = peek(1)
            if cp_after is None or not _is_emoji_base(cp_after):
                break
            i += 2  # consume ZWJ + next emoji base char

            if peek(0) == _VS16:
                i += 1
            cp_mod = peek(0)
            if cp_mod is not None and _is_skin_tone_modifier(cp_mod):
                i += 1
            if peek(0) == _KEYCAP:
                i += 1

        emoji_parts.append(text[start:i])
        remaining_parts.append(" ")

    emoji_text = "".join(emoji_parts).strip()
    remaining_text = "".join(remaining_parts)
    remaining_text = re.sub(r"[ \t]+", " ", remaining_text)
    return emoji_text, remaining_text


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


def is_command_triggered(event_extras) -> bool:
    if not isinstance(event_extras, dict):
        return False
    handlers_parsed_params = event_extras.get("handlers_parsed_params")
    if not isinstance(handlers_parsed_params, dict):
        return False
    return len(handlers_parsed_params) > 0
