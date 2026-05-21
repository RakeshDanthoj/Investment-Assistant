from app.core.cors_config import parse_cors_origins


def test_parse_exact_origins() -> None:
    exact, regex = parse_cors_origins("http://localhost:3000,http://127.0.0.1:3000")
    assert exact == ["http://localhost:3000", "http://127.0.0.1:3000"]
    assert regex is None


def test_parse_wildcard_vercel() -> None:
    exact, regex = parse_cors_origins("http://localhost:3000,https://*.vercel.app")
    assert exact == ["http://localhost:3000"]
    assert regex is not None
    assert re_match(regex, "https://investment-assistant.vercel.app")
    assert re_match(regex, "https://finnwise-git-main-user.vercel.app")
    assert not re_match(regex, "https://evil.com")


def re_match(pattern: str, origin: str) -> bool:
    import re

    return re.fullmatch(pattern, origin) is not None
