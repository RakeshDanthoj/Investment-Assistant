"""Onboarding session endpoint — stores mode + profile fields; never persists amount."""

from __future__ import annotations

from typing import Literal
from uuid import UUID, uuid4

import http
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.mode_detection import detect_mode
from app.services.session_profile_store import persist_session_profile

router = APIRouter()


class OnboardingSessionRequest(BaseModel):
    """Amount is accepted for client echo only — it is not written to the database."""

    investment_status: Literal["starting_fresh", "has_investments", "curious"]
    horizon: Literal["under_1y", "1_3y", "3_7y", "7_plus"]
    cadence: Literal["monthly", "one_time"]
    session_id: UUID | None = Field(
        default=None,
        description="Client-generated id; server creates one if omitted.",
    )
    amount_rupees: int | None = Field(
        default=None,
        description="Session-only rupee amount for UI echo — never stored server-side.",
        ge=0,
    )


class OnboardingSessionResponse(BaseModel):
    mode: Literal["portfolio_builder", "portfolio_protector", "curious"]
    starting_surface: Literal["map", "pulse"]
    rationale: str
    session_id: UUID
    amount_echo: int | None = Field(
        description="Echo of request.amount_rupees when provided — not persisted."
    )


@router.post("/session", response_model=OnboardingSessionResponse)
def create_onboarding_session(body: OnboardingSessionRequest) -> OnboardingSessionResponse:
    mode, surface, rationale = detect_mode(body.investment_status, body.horizon)
    sid = body.session_id or uuid4()

    persist_session_profile(
        session_id=sid,
        user_id=None,
        status=body.investment_status,
        horizon=body.horizon,
        cadence=body.cadence,
        mode=mode,
    )

    return OnboardingSessionResponse(
        mode=mode,
        starting_surface=surface,
        rationale=rationale,
        session_id=sid,
        amount_echo=body.amount_rupees,
    )
