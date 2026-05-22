from app.core.settings import Settings, normalize_supabase_url


def test_normalize_supabase_url_bare_project_ref() -> None:
    assert normalize_supabase_url("coqihzykxemmyewakasj") == (
        "https://coqihzykxemmyewakasj.supabase.co"
    )


def test_settings_normalizes_bare_supabase_url() -> None:
    settings = Settings(supabase_url="my-project-ref")
    assert settings.supabase_url == "https://my-project-ref.supabase.co"
