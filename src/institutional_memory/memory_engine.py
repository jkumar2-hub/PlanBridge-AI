"""Institutional Memory Engine & Reference Class Planning Copilot.
Transforms past project actual execution patterns into queryable institutional memory
and provides Kahneman-style Reference Class Forecasting to eliminate optimism bias.
"""

import json
from typing import Any, Dict, List, Optional
from src.database.db_manager import DatabaseManager
from src.institutional_memory.seed_data import HISTORICAL_PROJECT_MEMORIES, PRODUCTIVITY_BENCHMARKS


class InstitutionalMemoryEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.seed_if_empty()

    def seed_if_empty(self) -> None:
        """Seeds historical memory and benchmarks into SQLite if not already present."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM institutional_memory")
            row = cursor.fetchone()
            if row["cnt"] == 0:
                for mem in HISTORICAL_PROJECT_MEMORIES:
                    conn.execute(
                        """
                        INSERT INTO institutional_memory 
                        (memory_id, project_name, project_type, wbs_level, discipline, 
                         activity_name, planned_duration_days, actual_duration_days, 
                         variance_pct, optimism_bias_ratio, primary_delay_reason, 
                         productivity_metric, lessons_learned)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            mem["memory_id"], mem["project_name"], mem["project_type"],
                            mem["wbs_level"], mem["discipline"], mem["activity_name"],
                            mem["planned_duration_days"], mem["actual_duration_days"],
                            mem["variance_pct"], mem["optimism_bias_ratio"],
                            mem["primary_delay_reason"], mem["productivity_metric"],
                            mem["lessons_learned"]
                        )
                    )

            cursor.execute("SELECT COUNT(*) as cnt FROM productivity_benchmarks")
            row = cursor.fetchone()
            if row["cnt"] == 0:
                for bm in PRODUCTIVITY_BENCHMARKS:
                    conn.execute(
                        """
                        INSERT INTO productivity_benchmarks
                        (benchmark_id, discipline, activity_type, unit_of_measure,
                         standard_p50_rate, optimistic_p10_rate, pessimistic_p90_rate, historical_samples_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            bm["benchmark_id"], bm["discipline"], bm["activity_type"],
                            bm["unit_of_measure"], bm["standard_p50_rate"],
                            bm["optimistic_p10_rate"], bm["pessimistic_p90_rate"],
                            bm["historical_samples_count"]
                        )
                    )
            conn.commit()

    def get_all_memories(self, discipline: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if discipline and discipline.lower() != "all":
                cursor.execute(
                    "SELECT * FROM institutional_memory WHERE LOWER(discipline) = ? ORDER BY variance_pct DESC",
                    (discipline.lower(),)
                )
            else:
                cursor.execute("SELECT * FROM institutional_memory ORDER BY variance_pct DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        q = f"%{query.strip().lower()}%"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM institutional_memory 
                WHERE LOWER(activity_name) LIKE ? 
                   OR LOWER(lessons_learned) LIKE ? 
                   OR LOWER(primary_delay_reason) LIKE ?
                   OR LOWER(discipline) LIKE ?
                   OR LOWER(project_name) LIKE ?
                ORDER BY optimism_bias_ratio DESC
                """,
                (q, q, q, q, q)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_delay_root_causes(self) -> Dict[str, int]:
        """Calculates frequency breakdown of recurring root causes of delay."""
        memories = self.get_all_memories()
        breakdown = {}
        for m in memories:
            reason = m.get("primary_delay_reason", "Unspecified")
            category = "Other"
            r_lower = reason.lower()
            if "weather" in r_lower or "monsoon" in r_lower:
                category = "Weather / Monsoon"
            elif "material" in r_lower or "shortage" in r_lower or "vendor" in r_lower:
                category = "Supply Chain & Material Quality"
            elif "curing" in r_lower or "strength" in r_lower:
                category = "Curing & Technical Waiting Gates"
            elif "trench" in r_lower or "interface" in r_lower or "misalignment" in r_lower:
                category = "Discipline Interface Clashes"
            elif "punch" in r_lower or "leakage" in r_lower or "rework" in r_lower:
                category = "Pre-Commissioning Punch Clearance"
            elif "ptw" in r_lower or "safety" in r_lower:
                category = "Permit-to-Work (PTW) & Safety Gate"
            else:
                category = reason.split("/")[0].strip()

            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown

    def get_productivity_benchmarks(self, discipline: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if discipline and discipline.lower() != "all":
                cursor.execute(
                    "SELECT * FROM productivity_benchmarks WHERE LOWER(discipline) = ?",
                    (discipline.lower(),)
                )
            else:
                cursor.execute("SELECT * FROM productivity_benchmarks")
            return [dict(row) for row in cursor.fetchall()]

    def evaluate_optimism_bias(self, planned_days: int, discipline: str, activity_text: str) -> Dict[str, Any]:
        """De-biases baseline duration using Kahneman Reference Class Forecasting."""
        matches = self.search_memories(activity_text)
        if not matches:
            matches = self.get_all_memories(discipline)

        if matches:
            ratios = [m["optimism_bias_ratio"] for m in matches]
            avg_bias = sum(ratios) / len(ratios)
            p90_bias = max(ratios)
            min_bias = min(ratios)
            relevant_lesson = matches[0]["lessons_learned"]
            primary_risk = matches[0]["primary_delay_reason"]
        else:
            avg_bias = 1.35
            p90_bias = 1.70
            min_bias = 1.10
            relevant_lesson = "General engineering buffer recommended due to monsoon and permit dependencies."
            primary_risk = "Vendor & Permitting Coordination"

        recommended_duration = int(round(planned_days * avg_bias))
        p90_duration = int(round(planned_days * p90_bias))

        return {
            "planned_days": planned_days,
            "optimism_bias_factor": round(avg_bias, 2),
            "calibrated_duration_days": recommended_duration,
            "p90_risk_duration_days": p90_duration,
            "potential_overrun_days": recommended_duration - planned_days,
            "primary_delay_risk": primary_risk,
            "institutional_lesson": relevant_lesson,
            "sample_size": len(matches)
        }
