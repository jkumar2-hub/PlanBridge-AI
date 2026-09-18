"""Database Manager for SQLite transactions, audit logs, and schedule tracking."""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import BASELINE_SCHEDULE_PATH, DB_PATH
from src.database.schema import CREATE_TABLES_SQL


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize database schema tables if they do not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)

    def seed_schedule(self, schedule_json_path: Optional[Path] = None, overwrite: bool = False) -> int:
        """Loads activities from baseline_schedule.json into schedule_activities."""
        path = schedule_json_path or BASELINE_SCHEDULE_PATH
        if not path.exists():
            raise FileNotFoundError(f"Baseline schedule not found at {path}")

        with open(path, "r", encoding="utf-8-sig") as f:
            activities = json.load(f)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if overwrite:
                cursor.execute("DELETE FROM schedule_activities")

            inserted = 0
            for act in activities:
                deps = json.dumps(act.get("dependency_ids", []))
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO schedule_activities 
                    (activity_id, name, discipline, planned_start, planned_end, location, dependency_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        act["activity_id"],
                        act["name"],
                        act["discipline"],
                        act["planned_start"],
                        act["planned_end"],
                        act["location"],
                        deps,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            conn.commit()
            return inserted

    def get_all_activities(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedule_activities ORDER BY planned_start ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedule_activities WHERE activity_id = ?", (activity_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_field_report(
        self,
        report_id: str,
        source_format: str,
        raw_text: str,
        discipline_hint: Optional[str] = None,
        reported_by: Optional[str] = None,
        timestamp_received: Optional[str] = None,
    ) -> str:
        ts = timestamp_received or datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO field_reports (report_id, source_format, raw_text, discipline_hint, reported_by, timestamp_received)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (report_id, source_format, raw_text, discipline_hint, reported_by, ts),
            )
            conn.commit()
        return report_id

    def save_extracted_event(
        self,
        event_id: str,
        report_id: str,
        activity_description: str,
        discipline: Optional[str],
        event_date: Optional[str],
        action_type: str,
        location: Optional[str],
    ) -> str:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO extracted_events (event_id, report_id, activity_description, discipline, event_date, action_type, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, report_id, activity_description, discipline, event_date, action_type, location),
            )
            conn.commit()
        return event_id

    def save_match_result(
        self,
        match_id: str,
        event_id: str,
        candidate_activity_id: str,
        semantic_score: float,
        discipline_score: float,
        date_score: float,
        confidence_score: float,
        decision: str,
        top_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        candidates_json = json.dumps(top_candidates or [])
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO match_results 
                (match_id, event_id, candidate_activity_id, semantic_score, discipline_score, date_score, confidence_score, decision, top_candidates)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    event_id,
                    candidate_activity_id,
                    semantic_score,
                    discipline_score,
                    date_score,
                    confidence_score,
                    decision,
                    candidates_json,
                ),
            )
            conn.commit()
        return match_id

    def log_audit(
        self,
        activity_id: str,
        decision_maker: str,
        previous_value: Optional[str],
        new_value: Optional[str],
        notes: str,
        match_id: Optional[str] = None,
    ) -> str:
        log_id = f"LOG-{uuid.uuid4().hex[:8]}"
        ts = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (log_id, match_id, activity_id, decision_maker, previous_value, new_value, timestamp, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, match_id, activity_id, decision_maker, previous_value, new_value, ts, notes),
            )
            conn.commit()
        return log_id

    def apply_schedule_update(
        self,
        activity_id: str,
        action_type: str,
        event_date: str,
        decision_maker: str = "system",
        match_id: Optional[str] = None,
        notes: str = "",
    ) -> bool:
        current = self.get_activity(activity_id)
        if not current:
            return False

        prev_status = current.get("status")
        prev_actual_start = current.get("actual_start")
        prev_actual_end = current.get("actual_end")

        new_status = prev_status
        new_actual_start = prev_actual_start
        new_actual_end = prev_actual_end

        norm_action = action_type.lower().strip()
        if norm_action in ("started", "start"):
            new_status = "IN_PROGRESS"
            if not new_actual_start:
                new_actual_start = event_date
        elif norm_action in ("in-progress", "in_progress", "ongoing"):
            new_status = "IN_PROGRESS"
            if not new_actual_start:
                new_actual_start = event_date
        elif norm_action in ("completed", "complete", "finished", "done"):
            new_status = "COMPLETED"
            if not new_actual_start:
                new_actual_start = event_date
            new_actual_end = event_date

        prev_repr = f"status={prev_status}, start={prev_actual_start}, end={prev_actual_end}"
        new_repr = f"status={new_status}, start={new_actual_start}, end={new_actual_end}"

        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE schedule_activities 
                SET status = ?, actual_start = ?, actual_end = ?
                WHERE activity_id = ?
                """,
                (new_status, new_actual_start, new_actual_end, activity_id),
            )
            conn.commit()

        self.log_audit(
            activity_id=activity_id,
            decision_maker=decision_maker,
            previous_value=prev_repr,
            new_value=new_repr,
            notes=notes or f"Updated via event action '{action_type}'",
            match_id=match_id,
        )
        return True

    def save_contradiction_flag(
        self,
        activity_id_a: str,
        activity_id_b: str,
        discipline_a: str,
        discipline_b: str,
        description: str,
    ) -> str:
        flag_id = f"FLAG-{uuid.uuid4().hex[:8]}"
        ts = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO contradiction_flags (flag_id, activity_id_a, activity_id_b, discipline_a, discipline_b, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
                """,
                (flag_id, activity_id_a, activity_id_b, discipline_a, discipline_b, description, ts),
            )
            conn.commit()
        return flag_id

    def get_review_queue(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mr.*, ee.activity_description, ee.discipline as extracted_discipline, 
                       ee.event_date, ee.action_type, ee.location as event_location,
                       fr.raw_text, fr.reported_by, sa.name as candidate_name
                FROM match_results mr
                JOIN extracted_events ee ON mr.event_id = ee.event_id
                JOIN field_reports fr ON ee.report_id = fr.report_id
                JOIN schedule_activities sa ON mr.candidate_activity_id = sa.activity_id
                WHERE mr.decision = 'queued_for_review'
                ORDER BY mr.confidence_score DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT al.*, sa.name as activity_name, sa.discipline
                FROM audit_log al
                LEFT JOIN schedule_activities sa ON al.activity_id = sa.activity_id
                ORDER BY al.timestamp DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_contradictions(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contradiction_flags ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def resolve_review_item(self, match_id: str, selected_activity_id: str, planner_name: str, notes: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mr.*, ee.action_type, ee.event_date 
                FROM match_results mr
                JOIN extracted_events ee ON mr.event_id = ee.event_id
                WHERE mr.match_id = ?
                """,
                (match_id,),
            )
            item = cursor.fetchone()
            if not item:
                return False

            cursor.execute(
                "UPDATE match_results SET decision = 'resolved_by_planner', candidate_activity_id = ? WHERE match_id = ?",
                (selected_activity_id, match_id),
            )
            conn.commit()

        return self.apply_schedule_update(
            activity_id=selected_activity_id,
            action_type=item["action_type"],
            event_date=item["event_date"],
            decision_maker=planner_name,
            match_id=match_id,
            notes=f"Planner manual resolution: {notes}",
        )

    def reset_and_reseed(self, schedule_json_path: Optional[Path] = None) -> int:
        """Completely cleans transactional tables and reseeds schedule activities."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM contradiction_flags")
            conn.execute("DELETE FROM audit_log")
            conn.execute("DELETE FROM match_results")
            conn.execute("DELETE FROM extracted_events")
            conn.execute("DELETE FROM field_reports")
            conn.execute("DELETE FROM schedule_activities")
            conn.commit()
        return self.seed_schedule(schedule_json_path, overwrite=True)

    def update_contradiction_status(self, flag_id: str, new_status: str) -> bool:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE contradiction_flags SET status = ? WHERE flag_id = ?",
                (new_status, flag_id),
            )
            conn.commit()
        return True

