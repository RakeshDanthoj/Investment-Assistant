"""Connection string normalization for Supabase + external hosts."""

from __future__ import annotations

from app.db.connection import _connect_kwargs, prepare_db_url


def test_prepare_db_url_adds_sslmode_for_supabase_direct() -> None:
    url = "postgresql://postgres:secret@db.example.supabase.co:5432/postgres"
    out = prepare_db_url(url)
    assert "sslmode=require" in out


def test_prepare_db_url_strips_wrapping_quotes() -> None:
    url = '"postgresql://postgres:secret@db.example.supabase.co:5432/postgres"'
    out = prepare_db_url(url)
    assert out.startswith("postgresql://")
    assert "sslmode=require" in out


def test_prepare_db_url_preserves_existing_query_params() -> None:
    url = "postgresql://postgres:secret@db.example.supabase.co:5432/postgres?connect_timeout=15"
    out = prepare_db_url(url)
    assert "connect_timeout=15" in out
    assert "sslmode=require" in out


def test_connect_kwargs_disables_prepared_statements_on_transaction_pooler() -> None:
    url = "postgresql://postgres:secret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    kwargs = _connect_kwargs(url)
    assert kwargs["prepare_threshold"] is None
    assert kwargs["connect_timeout"] == 10


def test_connect_kwargs_default_port_uses_prepared_statements() -> None:
    url = "postgresql://postgres:secret@db.example.supabase.co:5432/postgres"
    kwargs = _connect_kwargs(url)
    assert "prepare_threshold" not in kwargs
