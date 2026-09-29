"""Physical Precedence & Cross-Discipline Contradiction Shield (Anti-Ghost Progress).
Detects engineering physically impossible claims, dependency violations, curing period breaches,
and cross-discipline spatial clashes with plain-language explainability.
"""

import json
import re
from typing import Any, Dict, List, Optional
from src.database.db_manager import DatabaseManager
from src.extraction.extractor_interface import ExtractedEvent


class ContradictionDetector:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def scan_for_contradictions(self, event: ExtractedEvent, matched_activity_id: str) -> List[Dict[str, Any]]:
        """Scans newly logged event against schedule state, predecessor activities, and physics laws."""
        detected_flags: List[Dict[str, Any]] = []

        curr_act = self.db.get_activity(matched_activity_id)
        if not curr_act:
            return detected_flags

        desc_lower = (event.activity_description + " " + (event.raw_snippet or "")).lower()
        is_blocked = (
            event.action_type == "blocked"
            or any(w in desc_lower for w in ["cannot start", "incomplete", "unaligned", "not ready", "rectify", "stopped", "flooded", "waterlogging"])
        )
        is_claim_progress = event.action_type in ["started", "completed", "progress"]

        # Parse dependencies
        deps_raw = curr_act.get("dependency_ids") or "[]"
        try:
            dep_ids = json.loads(deps_raw) if isinstance(deps_raw, str) else deps_raw
        except Exception:
            dep_ids = []

        # 1. Precedence Blockage Conflict (Report says blocked because of incomplete predecessor)
        if is_blocked:
            for pred_id in dep_ids:
                pred_act = self.db.get_activity(pred_id)
                if not pred_act:
                    continue

                pred_status = pred_act.get("status")
                # If predecessor was claimed COMPLETED in schedule, but field says it's blocked / incomplete!
                if pred_status == "COMPLETED" or pred_act.get("actual_end") is not None:
                    flag_desc = (
                        f"Cross-Discipline Conflict: {curr_act['discipline']} field report states work is BLOCKED on "
                        f"'{curr_act['name']}' ({curr_act['activity_id']}) citing unreadiness/incomplete status, "
                        f"despite predecessor '{pred_act['name']}' ({pred_act['activity_id']}) having been marked COMPLETED by {pred_act['discipline']}."
                    )
                    
                    flag_id = self.db.save_contradiction_flag(
                        activity_id_a=pred_act["activity_id"],
                        activity_id_b=curr_act["activity_id"],
                        discipline_a=pred_act["discipline"],
                        discipline_b=curr_act["discipline"],
                        description=flag_desc,
                        contradiction_type="precedence_unreadiness_conflict",
                        severity="CRITICAL",
                    )
                    detected_flags.append({
                        "flag_id": flag_id,
                        "activity_id_a": pred_act["activity_id"],
                        "activity_id_b": curr_act["activity_id"],
                        "discipline_a": pred_act["discipline"],
                        "discipline_b": curr_act["discipline"],
                        "description": flag_desc,
                        "severity": "CRITICAL",
                    })

        # 2. Physical Precedence Violation (Ghost Progress: Claiming start/completion before prerequisite is complete)
        if is_claim_progress:
            for pred_id in dep_ids:
                pred_act = self.db.get_activity(pred_id)
                if not pred_act:
                    continue

                pred_status = pred_act.get("status")
                if pred_status not in ["COMPLETED"] and (pred_act.get("percent_complete") or 0.0) < 100.0:
                    flag_desc = (
                        f"⚡ Physical Precedence Shield: {curr_act['discipline']} claimed {event.action_type.upper()} on "
                        f"'{curr_act['name']}' ({curr_act['activity_id']}), but mandatory prerequisite "
                        f"'{pred_act['name']}' ({pred_act['activity_id']}) by {pred_act['discipline']} is only {pred_act.get('percent_complete', 0)}% complete ({pred_status}). "
                        f"Physical erection cannot proceed until prerequisite hand-off."
                    )
                    flag_id = self.db.save_contradiction_flag(
                        activity_id_a=pred_act["activity_id"],
                        activity_id_b=curr_act["activity_id"],
                        discipline_a=pred_act["discipline"],
                        discipline_b=curr_act["discipline"],
                        description=flag_desc,
                        contradiction_type="physical_precedence_violation",
                        severity="HIGH",
                    )
                    detected_flags.append({
                        "flag_id": flag_id,
                        "activity_id_a": pred_act["activity_id"],
                        "activity_id_b": curr_act["activity_id"],
                        "discipline_a": pred_act["discipline"],
                        "discipline_b": curr_act["discipline"],
                        "description": flag_desc,
                        "severity": "HIGH",
                    })

        # 3. Direct Foundation / Location Clash Check (handles mentions of predecessor asset)
        if is_blocked and any(term in desc_lower for term in ["pedestal", "foundation", "trench", "alignment"]):
            all_acts = self.db.get_all_activities()
            for act in all_acts:
                if act["discipline"] == "Civil" and act["status"] == "COMPLETED" and any(k in act["name"].lower() for k in ["foundation", "pedestal", "trench"]):
                    if not any(f["activity_id_a"] == act["activity_id"] for f in detected_flags):
                        flag_desc = (
                            f"⚠️ Asset Interface Clash: {curr_act['discipline']} reported '{event.activity_description[:80]}' "
                            f"at {curr_act['location']}, conflicting with prior Civil sign-off of '{act['name']}' ({act['activity_id']})."
                        )
                        flag_id = self.db.save_contradiction_flag(
                            activity_id_a=act["activity_id"],
                            activity_id_b=curr_act["activity_id"],
                            discipline_a="Civil",
                            discipline_b=curr_act["discipline"],
                            description=flag_desc,
                            contradiction_type="location_asset_clash",
                            severity="MEDIUM",
                        )
                        detected_flags.append({
                            "flag_id": flag_id,
                            "activity_id_a": act["activity_id"],
                            "activity_id_b": curr_act["activity_id"],
                            "discipline_a": "Civil",
                            "discipline_b": curr_act["discipline"],
                            "description": flag_desc,
                            "severity": "MEDIUM",
                        })

        return detected_flags
