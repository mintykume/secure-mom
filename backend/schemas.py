"""Pydantic models shared across the pipeline stages."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    medical = "medical"
    executive = "executive"
    administrative = "administrative"


class ActionItem(BaseModel):
    decision: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    evidence: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class ExtractionResult(BaseModel):
    meeting_summary: str
    action_items: list[ActionItem]


class TranscriptResult(BaseModel):
    text: str
    detected_language: Optional[str] = None
    segments: list[dict] = Field(default_factory=list)


class ProcessResponse(BaseModel):
    meeting_id: str
    meeting_type: MeetingType
    detected_language: Optional[str]
    mom_markdown: str
    action_items: list[ActionItem]
