from app.core.settings import Settings


def normalized_admin_emails(settings: Settings) -> set[str]:
    raw = (settings.admin_emails or "").strip() or (settings.factor_db_admin_emails or "").strip()
    if not raw.strip():
        return set()

    # Support common deployment formats:
    # - Comma-separated: "a@x.com,b@y.com"
    # - Semicolon-separated: "a@x.com; b@y.com"
    # - Whitespace/newline-separated (some secret managers emit multiline values)
    # - JSON-ish list strings: '["a@x.com","b@y.com"]'
    cleaned = raw.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    cleaned = cleaned.replace('"', "").replace("'", "")

    parts: list[str] = []
    token = ""
    for ch in cleaned:
        if ch in {",", ";", "\n", "\r", "\t", " "}:
            if token.strip():
                parts.append(token.strip())
            token = ""
            continue
        token += ch
    if token.strip():
        parts.append(token.strip())

    return {part.lower() for part in parts if part}
