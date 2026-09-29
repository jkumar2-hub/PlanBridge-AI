"""Extractor Interface and Pydantic Schemas for Structured Progress Events."""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8]}")
    activity_description: str = Field(description="Descriptive activity or task extracted from the field text")
    discipline: Optional[str] = Field(default=None, description="Discipline: Civil, Piping, Electrical, Instrumentation, Mechanical, or HSE")
    event_date: Optional[str] = Field(default=None, description="ISO Date string YYYY-MM-DD or extracted date")
    action_type: str = Field(default="in-progress", description="Execution status: started, in-progress, completed, progress, or blocked")
    location: Optional[str] = Field(default=None, description="Physical site location, unit, or battery limit")
    quantity_done: Optional[float] = Field(default=0.0, description="Measured physical progress quantity (e.g. m3, joints, meters)")
    crew_size: Optional[int] = Field(default=0, description="Reported workforce / crew count")
    delay_reason: Optional[str] = Field(default=None, description="Reported bottleneck, hold point, or delay cause")
    raw_snippet: Optional[str] = Field(default=None, description="Supporting text snippet from source report")
    source_language: Optional[str] = Field(default="en", description="Detected language / dialect (en, hi, hinglish)")


class ExtractionResult(BaseModel):
    report_id: str
    events: List[ExtractedEvent] = Field(default_factory=list)
