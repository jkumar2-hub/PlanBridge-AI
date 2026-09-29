"""Database Manager for SQLite transactions, audit logs, and schedule tracking.
Equipped with cryptographic SHA-256 tamper-evident audit hash chaining,
L1-L6 WBS support, EVM fields, and institutional memory repository integration.
"""
import hashlib
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
        """Initialize database schema tables if they do not exist, and migrate missing columns."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            cursor = conn.cursor()

            # Migrate field_reports
            cursor.execute("PRAGMA table_info(field_reports)")
            fr_cols = [r["name"] for r in cursor.fetchall()]
            if "location" not in fr_cols:
                cursor.execute("ALTER TABLE field_reports ADD COLUMN location TEXT")

            # Migrate extracted_events
            cursor.execute("PRAGMA table_info(extracted_events)")
            ee_cols = [r["name"] for r in cursor.fetchall()]
            if "quantity_done" not in ee_cols:
                cursor.execute("ALTER TABLE extracted_events ADD COLUMN quantity_done REAL DEFAULT 0.0")
            if "crew_size" not in ee_cols:
                cursor.execute("ALTER TABLE extracted_events ADD COLUMN crew_size INTEGER DEFAULT 0")
            if "delay_reason" not in ee_cols:
                cursor.execute("ALTER TABLE extracted_events ADD COLUMN delay_reason TEXT")
            if "raw_snippet" not in ee_cols:
                cursor.execute("ALTER TABLE extracted_events ADD COLUMN raw_snippet TEXT")

            # Migrate schedule_activities
            cursor.execute("PRAGMA table_info(schedule_activities)")
            sa_cols = [r["name"] for r in cursor.fetchall()]
            if "wbs_code" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN wbs_code TEXT DEFAULT '1.0'")
            if "planned_duration" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN planned_duration INTEGER DEFAULT 0")
            if "weightage" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN weightage REAL DEFAULT 1.0")
            if "planned_cost" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN planned_cost REAL DEFAULT 10000.0")
            if "actual_cost" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN actual_cost REAL DEFAULT 0.0")
            if "percent_complete" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN percent_complete REAL DEFAULT 0.0")
            if "unit_of_measure" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN unit_of_measure TEXT DEFAULT 'units'")
            if "planned_quantity" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN planned_quantity REAL DEFAULT 100.0")
            if "actual_quantity" not in sa_cols:
                cursor.execute("ALTER TABLE schedule_activities ADD COLUMN actual_quantity REAL DEFAULT 0.0")

            # Migrate match_results
            cursor.execute("PRAGMA table_info(match_results)")
            mr_cols = [r["name"] for r in cursor.fetchall()]
            if "terminology_score" not in mr_cols:
                cursor.execute("ALTER TABLE match_results ADD COLUMN terminology_score REAL DEFAULT 0.0")
            if "planner_status" not in mr_cols:
                cursor.execute("ALTER TABLE match_results ADD COLUMN planner_status TEXT DEFAULT 'approved'")
            if "planner_notes" not in mr_cols:
                cursor.execute("ALTER TABLE match_results ADD COLUMN planner_notes TEXT")

            # Migrate audit_log
            cursor.execute("PRAGMA table_info(audit_log)")
            al_cols = [r["name"] for r in cursor.fetchall()]
            if "action" not in al_cols:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN action TEXT DEFAULT 'UPDATE'")
            if "sha256_hash" not in al_cols:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN sha256_hash TEXT")
            if "prev_hash" not in al_cols:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN prev_hash TEXT")

            # Migrate contradiction_flags
            cursor.execute("PRAGMA table_info(contradiction_flags)")
            cf_cols = [r["name"] for r in cursor.fetchall()]
            if "contradiction_type" not in cf_cols:
                cursor.execute("ALTER TABLE contradiction_flags ADD COLUMN contradiction_type TEXT DEFAULT 'physical_precedence_violation'")
            if "severity" not in cf_cols:
                cursor.execute("ALTER TABLE contradiction_flags ADD COLUMN severity TEXT DEFAULT 'HIGH'")
            if "resolution_notes" not in cf_cols:
                cursor.execute("ALTER TABLE contradiction_flags ADD COLUMN resolution_notes TEXT")

            conn.commit()

    def seed_schedule(self, schedule_json_path: Optional[Path] = None, overwrite: bool = False) -> int:
        """Loads activities from baseline_schedule.json into schedule_activities with WBS & EVM metadata."""
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
            for idx, act in enumerate(activities, 1):
                deps = json.dumps(act.get("dependency_ids", []))
                wbs_code = act.get("wbs_code") or f"1.{act.get('discipline', 'GEN')[:3].upper()}.{idx}"
                weightage = act.get("weightage", 1.0)
                planned_cost = act.get("planned_cost", 25000.0)
                unit_of_measure = act.get("unit_of_measure", "units")
                planned_qty = act.get("planned_quantity", 100.0)

                # calculate planned duration
                p_start = act.get("planned_start")
                p_end = act.get("planned_end")
                p_dur = 5
                try:
                    if p_start and p_end:
                        d1 = datetime.strptime(p_start, "%Y-%m-%d")
                        d2 = datetime.strptime(p_end, "%Y-%m-%d")
                        p_dur = max(1, (d2 - d1).days)
                except Exception:
                    p_dur = 5

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO schedule_activities 
                    (activity_id, wbs_code, name, discipline, planned_start, planned_end, 
                     planned_duration, location, weightage, planned_cost, actual_cost, 
                     dependency_ids, unit_of_measure, planned_quantity, actual_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?, 0.0)
                    """,
                    (
                        act["activity_id"],
                        wbs_code,
                        act["name"],
                        act["discipline"],
                        act["planned_start"],
                        act["planned_end"],
                        p_dur,
                        act["location"],
                        weightage,
                        planned_cost,
                        deps,
                        unit_of_measure,
                        planned_qty,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            conn.commit()
            return inserted

    def get_all_activities(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedule_activities ORDER BY planned_start ASC, activity_id ASC")
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
        location: Optional[str] = None,
        timestamp_received: Optional[str] = None,
    ) -> str:
        ts = timestamp_received or datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO field_reports (report_id, source_format, raw_text, discipline_hint, reported_by, location, timestamp_received)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (report_id, source_format, raw_text, discipline_hint, reported_by, location, ts),
            )
            conn.commit()
        return report_id

    def save_extracted_event(
        self,
        event_id: str,
        report_id: str,
        activity_description: str,
        discipline: Optional[str] = None,
        event_date: Optional[str] = None,
        action_type: str = "in-progress",
        location: Optional[str] = None,
        quantity_done: float = 0.0,
        crew_size: int = 0,
        delay_reason: Optional[str] = None,
        raw_snippet: Optional[str] = None,
    ) -> str:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO extracted_events 
                (event_id, report_id, activity_description, discipline, event_date, action_type, location, quantity_done, crew_size, delay_reason, raw_snippet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, report_id, activity_description, discipline, event_date, action_type, location, quantity_done, crew_size, delay_reason, raw_snippet or ""),
            )
            conn.commit()
        return event_id

    def save_extracted_events(self, events: List[Any], report_id: str) -> List[str]:
        event_ids = []
        with self.get_connection() as conn:
            for ev in events:
                eid = getattr(ev, "event_id", None) or f"EVT-{uuid.uuid4().hex[:8]}"
                qty = getattr(ev, "quantity_done", 0.0)
                crew = getattr(ev, "crew_size", 0)
                delay = getattr(ev, "delay_reason", None)
                raw_snip = getattr(ev, "raw_snippet", "")
                conn.execute(
                    """
                    INSERT INTO extracted_events 
                    (event_id, report_id, activity_description, discipline, event_date, action_type, location, quantity_done, crew_size, delay_reason, raw_snippet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eid,
                        report_id,
                        ev.activity_description,
                        ev.discipline,
                        ev.event_date,
                        ev.action_type,
                        ev.location,
                        qty,
                        crew,
                        delay,
                        raw_snip,
                    ),
                )
                event_ids.append(eid)
            conn.commit()
        return event_ids

    def save_match_result(
        self,
        event_id: str,
        candidate_activity_id: str,
        semantic_score: float,
        discipline_score: float,
        date_score: float,
        confidence_score: float,
        decision: str,
        top_candidates: Optional[List[Dict[str, Any]]] = None,
        terminology_score: float = 0.0,
    ) -> str:
        match_id = f"MATCH-{uuid.uuid4().hex[:8]}"
        top_cand_str = json.dumps(top_candidates or [])
        planner_stat = "approved" if decision == "auto_linked" else "pending"
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO match_results 
                (match_id, event_id, candidate_activity_id, semantic_score, discipline_score, terminology_score, date_score, confidence_score, decision, top_candidates, planner_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    event_id,
                    candidate_activity_id,
                    semantic_score,
                    discipline_score,
                    terminology_score,
                    date_score,
                    confidence_score,
                    decision,
                    top_cand_str,
                    planner_stat,
                ),
            )
            conn.commit()
        return match_id

    def save_audit_log(
        self,
        activity_id: str,
        decision_maker: str,
        previous_value: Optional[str],
        new_value: Optional[str],
        match_id: Optional[str] = None,
        action: str = "UPDATE",
        notes: Optional[str] = None,
    ) -> str:
        """Saves audit record with cryptographic SHA-256 hash chaining."""
        log_id = f"LOG-{uuid.uuid4().hex[:8]}"
        ts = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch latest hash in chain
            cursor.execute("SELECT sha256_hash FROM audit_log ORDER BY timestamp DESC LIMIT 1")
            last_entry = cursor.fetchone()
            prev_hash = last_entry["sha256_hash"] if last_entry and last_entry["sha256_hash"] else "GENESIS_BLOCK_" + ("0" * 50)

            # Compute tamper-evident hash
            block_content = f"{prev_hash}|{log_id}|{activity_id}|{decision_maker}|{action}|{previous_value}|{new_value}|{ts}|{notes}"
            curr_hash = hashlib.sha256(block_content.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT INTO audit_log (log_id, match_id, activity_id, decision_maker, action, previous_value, new_value, timestamp, notes, sha256_hash, prev_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, match_id, activity_id, decision_maker, action, previous_value, new_value, ts, notes, curr_hash, prev_hash),
            )
            conn.commit()
        return log_id

    def apply_schedule_update(
        self,
        activity_id: str,
        action_type: str,
        event_date: Optional[str],
        decision_maker: str,
        match_id: Optional[str] = None,
        notes: Optional[str] = None,
        quantity_done: Optional[float] = None,
    ) -> bool:
        act = self.get_activity(activity_id)
        if not act:
            return False

        now_str = event_date or datetime.now().strftime("%Y-%m-%d")
        prev_start = act.get("actual_start")
        prev_end = act.get("actual_end")
        prev_status = act.get("status")
        prev_qty = act.get("actual_quantity") or 0.0
        planned_qty = act.get("planned_quantity") or 100.0

        new_start = prev_start
        new_end = prev_end
        new_status = prev_status
        new_qty = prev_qty + (quantity_done or 0.0) if quantity_done else prev_qty
        new_pct = min(100.0, round((new_qty / planned_qty) * 100.0, 1)) if planned_qty > 0 else 0.0

        act_lower = str(action_type or "").lower().strip()

        if act_lower in ["started", "start"]:
            if not prev_start:
                new_start = now_str
            if prev_status != "COMPLETED":
                new_status = "IN_PROGRESS"
                if new_pct == 0.0:
                    new_pct = 20.0
        elif act_lower in ["completed", "complete", "done"]:
            if not prev_start:
                new_start = now_str
            new_end = now_str
            new_status = "COMPLETED"
            new_pct = 100.0
            new_qty = planned_qty
        elif act_lower in ["in-progress", "in_progress", "progress", "ongoing"]:
            if not prev_start:
                new_start = now_str
            if prev_status != "COMPLETED":
                new_status = "IN_PROGRESS"
                if new_pct == 0.0:
                    new_pct = 50.0
            else:
                new_pct = 100.0
        elif act_lower in ["blocked", "hold"]:
            if prev_status != "COMPLETED":
                new_status = "BLOCKED"

        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE schedule_activities 
                SET actual_start = ?, actual_end = ?, status = ?, percent_complete = ?, actual_quantity = ?
                WHERE activity_id = ?
                """,
                (new_start, new_end, new_status, new_pct, new_qty, activity_id),
            )
            conn.commit()

        # Audit log entry with hash chaining
        prev_val_str = f"Status: {prev_status}, Start: {prev_start}, End: {prev_end}, Pct: {act.get('percent_complete')}%"
        new_val_str = f"Status: {new_status}, Start: {new_start}, End: {new_end}, Pct: {new_pct}%"
        self.save_audit_log(
            activity_id=activity_id,
            decision_maker=decision_maker,
            previous_value=prev_val_str,
            new_value=new_val_str,
            match_id=match_id,
            notes=notes or f"Updated via {action_type} field event",
        )
        return True

    def save_contradiction_flag(
        self,
        activity_id_a: str,
        activity_id_b: str,
        discipline_a: str,
        discipline_b: str,
        description: str,
        contradiction_type: str = "physical_precedence_violation",
        severity: str = "HIGH",
    ) -> str:
        flag_id = f"FLAG-{uuid.uuid4().hex[:8]}"
        ts = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO contradiction_flags 
                (flag_id, activity_id_a, activity_id_b, discipline_a, discipline_b, contradiction_type, severity, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """,
                (flag_id, activity_id_a, activity_id_b, discipline_a, discipline_b, contradiction_type, severity, description, ts),
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
                       ee.quantity_done, ee.crew_size, ee.delay_reason,
                       fr.raw_text, fr.reported_by, fr.source_format, sa.name as candidate_name,
                       sa.wbs_code as candidate_wbs
                FROM match_results mr
                JOIN extracted_events ee ON mr.event_id = ee.event_id
                JOIN field_reports fr ON ee.report_id = fr.report_id
                JOIN schedule_activities sa ON mr.candidate_activity_id = sa.activity_id
                WHERE mr.decision IN ('queued_for_review', 'unmatched_new') OR mr.planner_status = 'pending'
                ORDER BY mr.confidence_score ASC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT al.*, sa.name as activity_name, sa.discipline, sa.wbs_code
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
                SELECT mr.*, ee.action_type, ee.event_date, ee.quantity_done
                FROM match_results mr
                JOIN extracted_events ee ON mr.event_id = ee.event_id
                WHERE mr.match_id = ?
                """,
                (match_id,),
            )
            raw_item = cursor.fetchone()
            if not raw_item:
                return False
            item = dict(raw_item)

            cursor.execute(
                """
                UPDATE match_results 
                SET decision = 'resolved_by_planner', candidate_activity_id = ?, planner_status = 'approved', planner_notes = ?
                WHERE match_id = ?
                """,
                (selected_activity_id, notes, match_id),
            )
            conn.commit()

        return self.apply_schedule_update(
            activity_id=selected_activity_id,
            action_type=item["action_type"],
            event_date=item["event_date"],
            decision_maker=planner_name,
            match_id=match_id,
            notes=f"Planner manual resolution: {notes}",
            quantity_done=item.get("quantity_done"),
        )

    def update_contradiction_status(self, flag_id: str, new_status: str, resolution_notes: Optional[str] = None) -> bool:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE contradiction_flags SET status = ?, resolution_notes = ? WHERE flag_id = ?",
                (new_status, resolution_notes, flag_id),
            )
            conn.commit()
        return True

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
