"""Pydantic schemas for PlanBridge AI REST API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TextIngestRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured shift log, diary text, or supervisor note")
    reported_by: Optional[str] = Field("Field Supervisor", description="Name/title of the reporter")
    discipline_hint: Optional[str] = Field(None, description="Optional discipline hint (Civil, Piping, Electrical, etc.)")
    source_format: Optional[str] = Field("api", description="Source format: conversational, text_report, voice_agent, etc.")


class VoiceParseRequest(BaseModel):
    transcript_text: str = Field(..., description="Speech-to-text transcript or natural language voice note")
    supervisor_name: Optional[str] = Field("Field Supervisor", description="Name of the supervisor")
    site_location: Optional[str] = Field(None, description="Physical site unit or area")


class DebiasRequest(BaseModel):
    planned_days: int = Field(..., ge=1, description="Proposed baseline duration in days")
    discipline: str = Field(..., description="Discipline: Civil, Piping, Electrical, Instrumentation, Mechanical, HSE")
    activity_text: str = Field(..., description="Activity description or task keyword")


class IngestResponse(BaseModel):
    status: str
    report_id: str
    events_count: int
    auto_updated_count: int
    review_queued_count: int
    latency_ms: float
    contradictions_flagged: int


class ReviewResolveRequest(BaseModel):
    match_id: str = Field(..., description="ID of the match result item")
    selected_activity_id: str = Field(..., description="WBS activity ID confirmed by planner")
    planner_name: str = Field("Planning Engineer", description="Name of the resolving planner")
    notes: Optional[str] = Field("Verified and approved by planner", description="Audit resolution notes")


class ContradictionStatusRequest(BaseModel):
    status: str = Field(..., description="New status: open, stop_work_issued, buffer_adjusted, resolved")
    resolution_notes: Optional[str] = Field(None, description="Remediation or mitigation notes")


class AskAIRequest(BaseModel):
    query: str = Field(..., description="Natural language question about project execution or institutional memory")


class AskAIResponse(BaseModel):
    query: str
    answer: str
    key_metrics: Dict[str, Any]
    timestamp: str
