"""End-to-End Pipeline for Processing Field Reports.
Step 1 Skeleton: Ingestion -> Extraction -> Matching -> DB/Audit Store.
"""
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BASELINE_SCHEDULE_PATH, DB_PATH
from src.database.db_manager import DatabaseManager
from src.extraction.extractor_interface import ExtractedEvent, ExtractionResult
from src.ingestion.text_adapter import TextAdapter


class Pipeline:
    def __init__(self, db_path: Optional[str] = None):
        self.db = DatabaseManager(db_path or str(DB_PATH))
        self.text_adapter = TextAdapter()
        # Seed schedule if empty
        acts = self.db.get_all_activities()
        if not acts:
            self.db.seed_schedule(BASELINE_SCHEDULE_PATH)

    def _crude_extract(self, report: Dict[str, Any]) -> ExtractionResult:
        """Crude Step 1 extractor to verify pipeline wiring."""
        raw_text = report["raw_text"]
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # Simple date extraction
        date_match = re.search(r"(?:Date|Dated):\s*([0-9]{1,4}[-/][0-9]{1,2}[-/][0-9]{1,4}|[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4})", raw_text, re.IGNORECASE)
        event_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

        # Pick key sentences as candidate events
        events: List[ExtractedEvent] = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["complete", "started", "fit-up", "weld", "pour", "curing", "laying", "erect", "mounted"]):
                # Determine action type
                action = "in-progress"
                if any(w in lower for w in ["complete", "completed", "cured", "finished", "ready"]):
                    action = "completed"
                elif any(w in lower for w in ["started", "commenced", "mobilized"]):
                    action = "started"
                elif any(w in lower for w in ["cannot start", "incomplete", "stopped", "blocked"]):
                    action = "blocked"

                # Determine discipline
                disc = report.get("discipline_hint")
                if "civil" in lower:
                    disc = "Civil"
                elif "piping" in lower or "weld" in lower or "spool" in lower:
                    disc = "Piping"
                elif "elect" in lower or "cable" in lower or "tray" in lower:
                    disc = "Electrical"
                elif "instrument" in lower or "jb-" in lower or "transmitter" in lower:
                    disc = "Instrumentation"
                elif "scaffold" in lower or "hse" in lower or "safety" in lower:
                    disc = "HSE"

                events.append(
                    ExtractedEvent(
                        event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                        activity_description=line,
                        discipline=disc or "General",
                        event_date=event_date,
                        action_type=action,
                        location="Unit 3 Pump House",
                        raw_snippet=line,
                    )
                )

        if not events:
            # Fallback single event
            events.append(
                ExtractedEvent(
                    event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                    activity_description=lines[0] if lines else "General site update",
                    discipline=report.get("discipline_hint") or "General",
                    event_date=event_date,
                    action_type="in-progress",
                    location="Unit 3 Pump House",
                    raw_snippet=raw_text[:100],
                )
            )

        return ExtractionResult(report_id=report["report_id"], events=events)

    def _crude_match(self, event: ExtractedEvent, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crude Step 1 keyword matcher to find closest schedule activity."""
        evt_words = set(re.findall(r"\w+", event.activity_description.lower()))
        best_act = activities[0]
        best_overlap = -1

        for act in activities:
            act_words = set(re.findall(r"\w+", (act["name"] + " " + act["discipline"]).lower()))
            overlap = len(evt_words.intersection(act_words))
            if event.discipline and event.discipline.lower() == act["discipline"].lower():
                overlap += 2
            if overlap > best_overlap:
                best_overlap = overlap
                best_act = act

        confidence = min(0.95, max(0.40, (best_overlap / 6.0)))
        decision = "auto_updated" if confidence >= 0.70 else "queued_for_review"

        return {
            "match_id": f"MAT-{uuid.uuid4().hex[:8]}",
            "candidate_activity_id": best_act["activity_id"],
            "candidate_name": best_act["name"],
            "semantic_score": round(confidence, 3),
            "discipline_score": 1.0 if event.discipline == best_act["discipline"] else 0.0,
            "date_score": 0.8,
            "confidence_score": round(confidence, 3),
            "decision": decision,
        }

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Runs the complete ingestion -> extraction -> matching -> DB flow for a file."""
        report = self.text_adapter.parse_file(file_path)
        return self.process_report(report)

    def process_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Ingestion: Save report
        self.db.save_field_report(
            report_id=report["report_id"],
            source_format=report["source_format"],
            raw_text=report["raw_text"],
            discipline_hint=report.get("discipline_hint"),
            reported_by=report.get("reported_by"),
            timestamp_received=report.get("timestamp_received"),
        )

        # 2. Extraction
        extraction = self._crude_extract(report)

        # 3. Matching & Schedule Update
        activities = self.db.get_all_activities()
        processed_events = []

        for evt in extraction.events:
            self.db.save_extracted_event(
                event_id=evt.event_id,
                report_id=report["report_id"],
                activity_description=evt.activity_description,
                discipline=evt.discipline,
                event_date=evt.event_date,
                action_type=evt.action_type,
                location=evt.location,
            )

            match_res = self._crude_match(evt, activities)

            self.db.save_match_result(
                match_id=match_res["match_id"],
                event_id=evt.event_id,
                candidate_activity_id=match_res["candidate_activity_id"],
                semantic_score=match_res["semantic_score"],
                discipline_score=match_res["discipline_score"],
                date_score=match_res["date_score"],
                confidence_score=match_res["confidence_score"],
                decision=match_res["decision"],
                top_candidates=[{"activity_id": match_res["candidate_activity_id"], "name": match_res["candidate_name"]}],
            )

            # 4. Schedule and Audit Update (if auto_updated)
            if match_res["decision"] == "auto_updated":
                self.db.apply_schedule_update(
                    activity_id=match_res["candidate_activity_id"],
                    action_type=evt.action_type,
                    event_date=evt.event_date or datetime.now().strftime("%Y-%m-%d"),
                    decision_maker="system",
                    match_id=match_res["match_id"],
                    notes=f"Auto-matched to '{evt.activity_description}' (Confidence: {match_res['confidence_score']})",
                )

            processed_events.append({
                "event": evt.model_dump(),
                "match": match_res,
            })

        return {
            "report_id": report["report_id"],
            "reported_by": report["reported_by"],
            "events_count": len(processed_events),
            "results": processed_events,
        }


if __name__ == "__main__":
    print("=== Testing Step 1 Skeleton Pipeline ===")
    pipeline = Pipeline()
    sample_path = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt")
    print(f"Ingesting: {sample_path}")
    output = pipeline.process_file(sample_path)
    print(f"Pipeline Result for Report ID: {output['report_id']}")
    for idx, item in enumerate(output["results"], 1):
        print(f"\n[Event {idx}] {item['event']['activity_description']}")
        print(f"  Discipline: {item['event']['discipline']} | Action: {item['event']['action_type']}")
        print(f"  Matched Activity: {item['match']['candidate_activity_id']} - {item['match']['candidate_name']}")
        print(f"  Confidence: {item['match']['confidence_score']} | Decision: {item['match']['decision']}")
    
    print("\nVerifying Audit Trail:")
    for log in pipeline.db.get_audit_trail()[:3]:
        print(f"  [{log['timestamp']}] Activity: {log['activity_id']} | Maker: {log['decision_maker']} | {log['notes']}")
    print("\n=== Step 1 Skeleton Execution Successful! ===")
