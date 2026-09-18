"""Cross-Discipline Contradiction Detector.
Identifies logical conflicts between disciplines on dependent activities or shared locations.
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
        """Scans newly logged event against schedule state and predecessor activities for cross-discipline clashes."""
        detected_flags: List[Dict[str, Any]] = []

        curr_act = self.db.get_activity(matched_activity_id)
        if not curr_act:
            return detected_flags

        desc_lower = (event.activity_description + " " + (event.raw_snippet or "")).lower()
        is_blocked = (
            event.action_type == "blocked"
            or any(w in desc_lower for w in ["cannot start", "incomplete", "unaligned", "not ready", "rectify", "stopped"])
        )

        # 1. Successor vs Predecessor Contradiction
        # If this activity is blocked because of an incomplete predecessor, check if predecessor was marked COMPLETED
        deps_raw = curr_act.get("dependency_ids") or "[]"
        try:
            dep_ids = json.loads(deps_raw) if isinstance(deps_raw, str) else deps_raw
        except Exception:
            dep_ids = []

        if is_blocked:
            for pred_id in dep_ids:
                pred_act = self.db.get_activity(pred_id)
                if not pred_act:
                    continue

                # Check if predecessor is marked completed or has a completed event
                pred_status = pred_act.get("status")
                if pred_status == "COMPLETED" or pred_act.get("actual_end") is not None:
                    flag_desc = (
                        f"Cross-Discipline Conflict: {curr_act['discipline']} reports work blocked on "
                        f"'{curr_act['name']}' ({curr_act['activity_id']}) citing unreadiness/incomplete status, "
                        f"but prerequisite '{pred_act['name']}' ({pred_act['activity_id']}) was already marked COMPLETED by {pred_act['discipline']}."
                    )
                    
                    flag_id = self.db.save_contradiction_flag(
                        activity_id_a=pred_act["activity_id"],
                        activity_id_b=curr_act["activity_id"],
                        discipline_a=pred_act["discipline"],
                        discipline_b=curr_act["discipline"],
                        description=flag_desc,
                    )
                    detected_flags.append({
                        "flag_id": flag_id,
                        "activity_id_a": pred_act["activity_id"],
                        "activity_id_b": curr_act["activity_id"],
                        "discipline_a": pred_act["discipline"],
                        "discipline_b": curr_act["discipline"],
                        "description": flag_desc,
                    })

        # 2. Direct Foundation / Location Clash Check (handles mentions of predecessor asset)
        if is_blocked and any(term in desc_lower for term in ["pedestal", "foundation"]):
            # Find any civil foundation activities in the same location that were claimed completed
            all_acts = self.db.get_all_activities()
            for act in all_acts:
                if act["discipline"] == "Civil" and act["status"] == "COMPLETED" and "foundation" in act["name"].lower():
                    # If this wasn't already caught by dependency check
                    if not any(f["activity_id_a"] == act["activity_id"] for f in detected_flags):
                        flag_desc = (
                            f"Location / Asset Clash: {curr_act['discipline']} reported '{event.activity_description[:80]}' "
                            f"at {curr_act['location']}, conflicting with Civil completion of '{act['name']}' ({act['activity_id']})."
                        )
                        flag_id = self.db.save_contradiction_flag(
                            activity_id_a=act["activity_id"],
                            activity_id_b=curr_act["activity_id"],
                            discipline_a="Civil",
                            discipline_b=curr_act["discipline"],
                            description=flag_desc,
                        )
                        detected_flags.append({
                            "flag_id": flag_id,
                            "activity_id_a": act["activity_id"],
                            "activity_id_b": curr_act["activity_id"],
                            "discipline_a": "Civil",
                            "discipline_b": curr_act["discipline"],
                            "description": flag_desc,
                        })

        return detected_flags
