from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventCategory, LifecycleState, SignalState


class EventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: EventCategory
    source_url: str | None = None
    canonical_url: str = ""
    event_source: str = ""
    confidence_score: int = Field(ge=0, le=100)
    lifecycle_state: LifecycleState = LifecycleState.DRAFT
    prompt_version: str | None = None
    created_at: datetime
    draft_card_id: UUID | None = None


class SignalRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    signal_text: str
    state: SignalState = SignalState.PENDING
    triggered_at: datetime | None = None
    created_at: datetime


class InstrumentAssessmentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    version: int = 1
    instrument_id: str
    signal_type: str
    reasoning: str | None = None
    entry_conditions: list[str] = Field(default_factory=list)
    exit_conditions: list[str] = Field(default_factory=list)
    created_at: datetime


class UserPredictionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    card_id: UUID
    prediction_text: str
    logged_at: datetime
    mechanism_accuracy: str | None = None
    business_accuracy: str | None = None
    market_accuracy: str | None = None


class TrackRecordEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    payload: dict[str, Any] = Field(default_factory=dict)
    logged_at: datetime
