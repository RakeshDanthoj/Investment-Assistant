from app.core.settings import Settings


def normalized_admin_emails(settings: Settings) -> set[str]:
    raw = settings.admin_emails.strip() or settings.factor_db_admin_emails.strip()
    if not raw:
        return set()
    return {part.strip().lower() for part in raw.split(",") if part.strip()}
