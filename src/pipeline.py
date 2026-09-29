"""Unified End-to-End Pipeline for SIH PS 26122 (PlanBridge AI).
Ingestion (DPR Text, Spreadsheets, Voice Time Agent, P6) ->
LLM/Heuristic Extraction -> Embedding & Terminology Matching ->
Physical Precedence & Contradiction Shield -> Cryptographic Audit Hash-Chain -> Auto-Update.
"""

import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BASELINE_SCHEDULE_PATH, CONFIDENCE_THRESHOLD, DB_PATH
from src.contradiction.detector import ContradictionDetector
from src.database.db_manager import DatabaseManager
from src.extraction.extractor_interface import ExtractedEvent, ExtractionResult
from src.extraction.llm_extractor import LLMExtractor
from src.ingestion.spreadsheet_adapter import SpreadsheetAdapter
from src.ingestion.text_adapter import TextAdapter
from src.matching.confidence_scorer import ConfidenceScorer
from src.matching.embedding_engine import EmbeddingEngine
from src.matching.fuzzy_matcher import FuzzyMatcher
from src.voice_agent.time_agent import VoiceTimeAgent


class Pipeline:
    def __init__(
        self,
        db_path: Optional[str] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        embedding_engine: Optional[EmbeddingEngine] = None,
        llm_provider: Optional[str] = None,
        enable_contradiction_detection: bool = True,
    ):
        self.db = DatabaseManager(db_path or str(DB_PATH))
        self.text_adapter = TextAdapter()
        self.spreadsheet_adapter = SpreadsheetAdapter()
        self.extractor = LLMExtractor(provider=llm_provider)
        self.voice_agent = VoiceTimeAgent()

        # Shared embedding engine with warm cache
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.scorer = ConfidenceScorer(threshold=confidence_threshold)
        self.matcher = FuzzyMatcher(self.embedding_engine, self.scorer)

        # Seed baseline schedule if empty
        activities = self.db.get_all_activities()
        if not activities:
            self.db.seed_schedule(BASELINE_SCHEDULE_PATH)
            activities = self.db.get_all_activities()

        # Warm up embedding index
        self.embedding_engine.index_activities(activities)

        self.enable_contradiction_detection = enable_contradiction_detection
        if self.enable_contradiction_detection:
            self.contradiction_detector = ContradictionDetector(self.db)
        else:
            self.contradiction_detector = None

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Processes text daily reports, CSV/Excel spreadsheets, or voice transcripts."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        if path.suffix.lower() in [".csv", ".xlsx", ".xls"]:
            return self.process_spreadsheet(file_path)
        else:
            return self.process_text_file(file_path)

    def process_text_file(self, file_path: str) -> Dict[str, Any]:
        report = self.text_adapter.parse_file(file_path)
        return self.process_text_report(
            raw_text=report["raw_text"],
            report_id=report["report_id"],
            reported_by=report.get("reported_by"),
            discipline_hint=report.get("discipline_hint"),
            source_format="free_text",
            filename=report.get("filename"),
        )

    def process_voice_audio(
        self,
        audio_bytes: bytes,
        supervisor_name: str = "Field Supervisor",
        site_location: Optional[str] = None,
        language: str = "hi-IN",
    ) -> Dict[str, Any]:
        """Transcribes audio bytes and processes the extracted field update."""
        transcript = self.voice_agent.transcribe_audio_bytes(audio_bytes, language=language)
        result = self.process_voice_transcript(
            transcript_text=transcript,
            supervisor_name=supervisor_name,
            site_location=site_location,
        )
        result["transcription_raw"] = transcript
        return result

    def process_voice_transcript(
        self,
        transcript_text: str,
        supervisor_name: str = "Field Supervisor",
        site_location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes supervisor audio or natural language chat via the Multilingual Voice Time Agent."""
        start_time = time.perf_counter()
        parsed = self.voice_agent.parse_voice_log(
            voice_transcript=transcript_text,
            supervisor_name=supervisor_name,
            site_location=site_location
        )
        evt: ExtractedEvent = parsed["event"]
        rep_id = f"REP-VOICE-{uuid.uuid4().hex[:6]}"

        # 1. Save field report
        self.db.save_field_report(
            report_id=rep_id,
            source_format="voice_time_agent",
            raw_text=transcript_text,
            discipline_hint=evt.discipline,
            reported_by=supervisor_name,
            location=evt.location,
            timestamp_received=datetime.now().isoformat(),
        )

        # 2. Save extracted event
        self.db.save_extracted_events([evt], report_id=rep_id)

        # 3. Match against schedule activities
        activities = self.db.get_all_activities()
        match_res = self.matcher.match_event(evt, activities)
        match_id = self.db.save_match_result(
            event_id=evt.event_id,
            candidate_activity_id=match_res["candidate_activity_id"],
            semantic_score=match_res["semantic_score"],
            discipline_score=match_res["discipline_score"],
            date_score=match_res["date_score"],
            confidence_score=match_res["confidence_score"],
            decision=match_res["decision"],
            top_candidates=match_res["top_candidates"],
            terminology_score=match_res.get("terminology_score", 0.0),
        )

        # 4. Check for physical precedence contradictions
        contradictions = []
        if self.contradiction_detector:
            flags = self.contradiction_detector.scan_for_contradictions(
                event=evt,
                matched_activity_id=match_res["candidate_activity_id"],
            )
            if flags:
                contradictions.extend(flags)

        # 5. Apply schedule auto-update if high confidence
        auto_updated = False
        if match_res["decision"] == "auto_updated":
            auto_updated = self.db.apply_schedule_update(
                activity_id=match_res["candidate_activity_id"],
                action_type=evt.action_type,
                event_date=evt.event_date or datetime.now().strftime("%Y-%m-%d"),
                decision_maker=f"TimeAgent ({supervisor_name})",
                match_id=match_id,
                notes=f"Voice log: '{evt.activity_description[:60]}...' (Confidence: {match_res['confidence_score']:.2f})",
                quantity_done=evt.quantity_done,
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "report_id": rep_id,
            "source_format": "voice_time_agent",
            "supervisor_name": supervisor_name,
            "detected_language": parsed["detected_language"],
            "confirmation_message": parsed["confirmation_message"],
            "event": evt.model_dump(),
            "match": {
                "match_id": match_id,
                **match_res,
            },
            "auto_updated": auto_updated,
            "contradictions": contradictions,
            "latency_ms": elapsed_ms,
        }

    def process_text_report(
        self,
        raw_text: str,
        report_id: Optional[str] = None,
        reported_by: Optional[str] = None,
        discipline_hint: Optional[str] = None,
        source_format: str = "conversational",
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        rep_id = report_id or f"REP-{uuid.uuid4().hex[:8]}"

        # 1. Ingestion: Save report
        self.db.save_field_report(
            report_id=rep_id,
            source_format=source_format,
            raw_text=raw_text,
            discipline_hint=discipline_hint,
            reported_by=reported_by or "Field Supervisor",
            timestamp_received=datetime.now().isoformat(),
        )

        # 2. LLM / Heuristic Extraction
        extraction = self.extractor.extract(
            report_id=rep_id,
            raw_text=raw_text,
            discipline_hint=discipline_hint,
        )

        # 3. Matching, Contradiction Detection & Schedule Updates
        activities = self.db.get_all_activities()
        processed_events = []
        all_contradictions = []

        # Save all extracted events
        self.db.save_extracted_events(extraction.events, report_id=rep_id)

        for evt in extraction.events:
            match_res = self.matcher.match_event(evt, activities)
            match_id = self.db.save_match_result(
                event_id=evt.event_id,
                candidate_activity_id=match_res["candidate_activity_id"],
                semantic_score=match_res["semantic_score"],
                discipline_score=match_res["discipline_score"],
                date_score=match_res["date_score"],
                confidence_score=match_res["confidence_score"],
                decision=match_res["decision"],
                top_candidates=match_res["top_candidates"],
                terminology_score=match_res.get("terminology_score", 0.0),
            )

            # Auto-update if decision is auto_updated
            if match_res["decision"] == "auto_updated":
                self.db.apply_schedule_update(
                    activity_id=match_res["candidate_activity_id"],
                    action_type=evt.action_type,
                    event_date=evt.event_date or datetime.now().strftime("%Y-%m-%d"),
                    decision_maker="system",
                    match_id=match_id,
                    notes=f"Auto-linked from field text: '{evt.activity_description[:60]}...' (Score: {match_res['confidence_score']:.2f})",
                    quantity_done=evt.quantity_done,
                )

            # Check for cross-discipline contradictions
            if self.contradiction_detector:
                flags = self.contradiction_detector.scan_for_contradictions(
                    event=evt,
                    matched_activity_id=match_res["candidate_activity_id"],
                )
                if flags:
                    all_contradictions.extend(flags)

            processed_events.append({
                "event": evt.model_dump(),
                "match": {
                    "match_id": match_id,
                    **match_res,
                },
            })

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "report_id": rep_id,
            "source_format": source_format,
            "reported_by": reported_by or "Field Supervisor",
            "events_count": len(processed_events),
            "latency_ms": elapsed_ms,
            "contradictions": all_contradictions,
            "results": processed_events,
        }

    def process_spreadsheet(self, file_path: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        parsed = self.spreadsheet_adapter.parse_file(file_path)
        rep_id = parsed["report_id"]

        self.db.save_field_report(
            report_id=rep_id,
            source_format="spreadsheet",
            raw_text=parsed["raw_text"],
            discipline_hint=parsed.get("discipline_hint"),
            reported_by=parsed.get("reported_by"),
            timestamp_received=parsed.get("timestamp_received") or datetime.now().isoformat(),
        )

        activities = self.db.get_all_activities()
        processed_events = []
        all_contradictions = []

        # Convert rows to extracted events
        events: List[ExtractedEvent] = []
        for row in parsed["rows"]:
            desc = row.get("description") or row.get("activity_description") or "Field activity"
            disc = row.get("discipline") or parsed.get("discipline_hint") or "General"
            dt = row.get("date") or row.get("event_date") or row.get("report_date")
            act = row.get("action") or row.get("action_type") or "in-progress"
            loc = row.get("location") or row.get("area") or row.get("unit")
            qty_val = 0.0
            try:
                qty_val = float(row.get("quantity") or row.get("qty") or 0.0)
            except Exception:
                qty_val = 0.0

            ev = ExtractedEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8]}",
                activity_description=desc,
                discipline=disc,
                event_date=dt,
                action_type=act,
                location=loc,
                quantity_done=qty_val,
                raw_snippet=str(row),
            )
            events.append(ev)

        self.db.save_extracted_events(events, report_id=rep_id)

        for evt in events:
            match_res = self.matcher.match_event(evt, activities)
            match_id = self.db.save_match_result(
                event_id=evt.event_id,
                candidate_activity_id=match_res["candidate_activity_id"],
                semantic_score=match_res["semantic_score"],
                discipline_score=match_res["discipline_score"],
                date_score=match_res["date_score"],
                confidence_score=match_res["confidence_score"],
                decision=match_res["decision"],
                top_candidates=match_res["top_candidates"],
                terminology_score=match_res.get("terminology_score", 0.0),
            )

            if match_res["decision"] == "auto_updated":
                self.db.apply_schedule_update(
                    activity_id=match_res["candidate_activity_id"],
                    action_type=evt.action_type,
                    event_date=evt.event_date or datetime.now().strftime("%Y-%m-%d"),
                    decision_maker="system",
                    match_id=match_id,
                    notes=f"Auto-linked from spreadsheet log: '{evt.activity_description[:60]}...' (Score: {match_res['confidence_score']:.2f})",
                    quantity_done=evt.quantity_done,
                )

            if self.contradiction_detector:
                flags = self.contradiction_detector.scan_for_contradictions(
                    event=evt,
                    matched_activity_id=match_res["candidate_activity_id"],
                )
                if flags:
                    all_contradictions.extend(flags)

            processed_events.append({
                "event": evt.model_dump(),
                "match": {
                    "match_id": match_id,
                    **match_res,
                },
            })

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "report_id": rep_id,
            "source_format": "spreadsheet",
            "filename": parsed.get("filename"),
            "events_count": len(processed_events),
            "latency_ms": elapsed_ms,
            "contradictions": all_contradictions,
            "results": processed_events,
        }
