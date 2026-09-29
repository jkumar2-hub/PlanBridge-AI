"""LLM Extractor for transforming unstructured site text into structured events."""
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config import GEMINI_API_KEY, LLM_PROVIDER, OPENAI_API_KEY
from src.extraction.extractor_interface import ExtractedEvent, ExtractionResult

EXTRACTION_SYSTEM_PROMPT = """You are an expert infrastructure project controls engineer for Oil India Limited capex projects.
Your objective is to extract distinct field execution events from unstructured daily progress reports, site diaries, and logs.

For each distinct work activity mentioned in the text, extract:
1. "activity_description": Clear, concise summary of the specific physical work item done or attempted.
2. "discipline": Exactly one of ["Civil", "Piping", "Electrical", "Instrumentation", "HSE"].
3. "event_date": Date of work in YYYY-MM-DD format (if ambiguous or relative, extrapolate from report header date).
4. "action_type": Exactly one of:
   - "started" (commenced, initiated, mobilized)
   - "in-progress" (ongoing, fit-up, continuous work)
   - "completed" (poured, cured, finished, erected, tested, done)
   - "blocked" (stopped, cannot start, delayed, incomplete predecessor)
5. "location": Physical location/area mentioned (e.g., "Unit 3 Pump House", "Unit 3 Manifold Area", "Unit 3 Pipe Rack").
6. "raw_snippet": The exact sentence or fragment from the report providing evidence.

Respond strictly with valid JSON conforming to:
{
  "events": [
    {
      "activity_description": "string",
      "discipline": "Civil|Piping|Electrical|Instrumentation|HSE",
      "event_date": "YYYY-MM-DD",
      "action_type": "started|in-progress|completed|blocked",
      "location": "string",
      "raw_snippet": "string"
    }
  ]
}
"""


class LLMExtractor:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or LLM_PROVIDER
        self.gemini_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        self.openai_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
        self._init_client()

    def _init_client(self) -> None:
        self.client_type = None
        if self.provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json"},
                )
                self.client_type = "gemini"
            except Exception as e:
                print(f"[LLMExtractor] Gemini init warning: {e}")
        elif self.provider == "openai" and self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.client_type = "openai"
            except Exception as e:
                print(f"[LLMExtractor] OpenAI init warning: {e}")

    def extract(self, report_id: str, raw_text: str, discipline_hint: Optional[str] = None) -> ExtractionResult:
        """Main extraction entrypoint: uses live LLM API if key is available, else structured fallback."""
        if self.client_type == "gemini":
            try:
                return self._extract_gemini(report_id, raw_text)
            except Exception as e:
                print(f"[LLMExtractor] Gemini API call failed ({e}), falling back to structured extractor.")
        elif self.client_type == "openai":
            try:
                return self._extract_openai(report_id, raw_text)
            except Exception as e:
                print(f"[LLMExtractor] OpenAI API call failed ({e}), falling back to structured extractor.")

        # Deterministic structured extraction fallback
        return self._extract_structured_fallback(report_id, raw_text, discipline_hint)

    def _extract_gemini(self, report_id: str, raw_text: str) -> ExtractionResult:
        prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nReport Text to Extract:\n\"\"\"\n{raw_text}\n\"\"\""
        response = self.gemini_model.generate_content(prompt)
        data = json.loads(response.text)
        return self._parse_json_payload(report_id, data)

    def _extract_openai(self, report_id: str, raw_text: str) -> ExtractionResult:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Report Text to Extract:\n\"\"\"\n{raw_text}\n\"\"\""},
            ],
            temperature=0.0,
        )
        data = json.loads(response.choices[0].message.content)
        return self._parse_json_payload(report_id, data)

    def _extract_structured_fallback(self, report_id: str, raw_text: str, discipline_hint: Optional[str] = None) -> ExtractionResult:
        """Structured fallback that parses text into the exact same JSON schema."""
        # Extract date
        date_match = re.search(r"(?:Date|Dated):\s*([0-9]{1,4}[-/][0-9]{1,2}[-/][0-9]{1,4}|[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4})", raw_text, re.IGNORECASE)
        raw_date_str = date_match.group(1) if date_match else "2026-10-03"
        
        # Standardize date format to YYYY-MM-DD
        std_date = "2026-10-03"
        try:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y"):
                try:
                    dt = datetime.strptime(raw_date_str, fmt)
                    std_date = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
        except Exception:
            pass

        # Extract location
        loc = "Unit 3 Pump House"
        if re.search(r"manifold", raw_text, re.IGNORECASE):
            loc = "Unit 3 Manifold Area"
        elif re.search(r"pipe rack", raw_text, re.IGNORECASE):
            loc = "Unit 3 Pipe Rack"
        elif re.search(r"battery limit", raw_text, re.IGNORECASE):
            loc = "Unit 3 Battery Limit"

        sentences = [s.strip() for s in re.split(r"[.\n]+", raw_text) if len(s.strip()) > 15]
        events: List[ExtractedEvent] = []

        for s in sentences:
            s_lower = s.lower()
            if any(k in s_lower for k in [
                "complete", "curing", "pour", "foundation", "pedestal", "tray", "cable",
                "spool", "fitup", "fit-up", "weld", "welding", "ndt", "junction box",
                "transmitter", "scaffold", "tagging", "barricade", "cannot start", "incomplete"
            ]):
                # Action determination
                action = "in-progress"
                if any(w in s_lower for w in ["cannot start", "incomplete", "stopped", "unaligned"]):
                    action = "blocked"
                elif any(w in s_lower for w in ["complete", "completed", "cured", "finished", "ready", "signed"]):
                    action = "completed"
                elif any(w in s_lower for w in ["started", "commenced", "mobilized"]):
                    action = "started"

                # Discipline determination
                disc = discipline_hint or "Civil"
                if any(w in s_lower for w in ["elect", "cable", "tray", "motor", "switchgear", "substation"]):
                    disc = "Electrical"
                elif any(w in s_lower for w in ["piping", "spool", "weld", "welder", "fitup", "fit-up", "ndt"]):
                    disc = "Piping"
                elif any(w in s_lower for w in ["transmitter", "junction box", "jb-", "instrument", "dcs"]):
                    disc = "Instrumentation"
                elif any(w in s_lower for w in ["scaffold", "tag", "extinguisher", "fire", "permit", "safety", "hse"]):
                    disc = "HSE"
                elif any(w in s_lower for w in ["concrete", "pour", "pedestal", "civil", "shuttering", "excavation"]):
                    disc = "Civil"

                events.append(
                    ExtractedEvent(
                        event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                        activity_description=s,
                        discipline=disc,
                        event_date=std_date,
                        action_type=action,
                        location=loc,
                        raw_snippet=s,
                    )
                )

        if not events:
            events.append(
                ExtractedEvent(
                    event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                    activity_description=sentences[0] if sentences else raw_text[:80],
                    discipline=discipline_hint or "Civil",
                    event_date=std_date,
                    action_type="in-progress",
                    location=loc,
                    raw_snippet=raw_text[:80],
                )
            )

        return ExtractionResult(report_id=report_id, events=events)

    def _parse_json_payload(self, report_id: str, data: Dict[str, Any]) -> ExtractionResult:
        events_raw = data.get("events", [])
        events: List[ExtractedEvent] = []
        for e in events_raw:
            events.append(
                ExtractedEvent(
                    event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                    activity_description=e.get("activity_description", "Unknown activity"),
                    discipline=e.get("discipline"),
                    event_date=e.get("event_date"),
                    action_type=e.get("action_type", "in-progress"),
                    location=e.get("location"),
                    raw_snippet=e.get("raw_snippet"),
                )
            )
        return ExtractionResult(report_id=report_id, events=events)
