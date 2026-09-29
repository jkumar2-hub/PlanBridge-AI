"""Step 3 Verification: Audit Trail, Review Queue, and Contradiction Detection."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import Pipeline

def test_step3():
    print("==================================================================")
    print("STEP 3 CHECKPOINT: AUDIT TRAIL, REVIEW QUEUE & CONTRADICTION ENGINE")
    print("==================================================================")

    test_db = str(PROJECT_ROOT / "data" / "step3_test.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    pipeline = Pipeline(db_path=test_db)

    # 1. Ingest Civil Oct 3 (Foundation complete)
    civ_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt")
    print(f"\n1. Ingesting Civil Report: {civ_file}")
    res_civ = pipeline.process_file(civ_file)
    print(f"   Civil events processed: {res_civ['events_count']}")

    civ_act = pipeline.db.get_activity("L5-CIV-102")
    print(f"   L5-CIV-102 Status after Civil Report: {civ_act['status']} (Actual End: {civ_act['actual_end']})")
    assert civ_act["status"] == "COMPLETED", "L5-CIV-102 should be COMPLETED!"

    # 2. Ingest Electrical Oct 5 (Planted contradiction: foundation unaligned / blocked)
    ele_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt")
    print(f"\n2. Ingesting Electrical Report (Planted Contradiction): {ele_file}")
    res_ele = pipeline.process_file(ele_file)
    print(f"   Electrical events processed: {res_ele['events_count']}")
    print(f"   Contradictions caught in return payload: {len(res_ele['contradictions'])}")

    # 3. Check contradiction_flags table
    stored_flags = pipeline.db.get_contradictions()
    print(f"\n3. Contradiction Flags in Database: {len(stored_flags)}")
    assert len(stored_flags) > 0, "At least one contradiction flag must be created!"
    for flag in stored_flags:
        print(f"   - [FLAG ID: {flag['flag_id']}] Disciplines: {flag['discipline_a']} vs {flag['discipline_b']}")
        print(f"     Activities: {flag['activity_id_a']} <-> {flag['activity_id_b']}")
        print(f"     Description: {flag['description']}")

    # 4. Check Review Queue
    queue_items = pipeline.db.get_review_queue()
    print(f"\n4. Review Queue Items: {len(queue_items)}")
    assert len(queue_items) > 0, "Review queue must hold low-confidence items!"
    sample_queue_item = queue_items[0]
    print(f"   Sample Review Item ID: {sample_queue_item['match_id']}")
    print(f"   Extracted text: '{sample_queue_item['activity_description']}'")
    print(f"   Candidate guess: {sample_queue_item['candidate_activity_id']} (Confidence: {sample_queue_item['confidence_score']})")
    print(f"   Top-3 candidate alternatives visible: {sample_queue_item['top_candidates'][:100]}...")

    # 5. Test Planner Manual Resolution
    print("\n5. Testing Planner Manual Resolution of Queued Item:")
    planner_name = "Chief Planning Engineer Sharma"
    resolve_success = pipeline.db.resolve_review_item(
        match_id=sample_queue_item["match_id"],
        selected_activity_id="L5-CIV-103",
        planner_name=planner_name,
        notes="Confirmed pedestal level rework required before grouting.",
    )
    print(f"   Resolution execution success: {resolve_success}")
    assert resolve_success, "Planner resolution should succeed!"

    # 6. Verify Audit Trail
    audit_trail = pipeline.db.get_audit_trail()
    print(f"\n6. Audit Trail Records: {len(audit_trail)}")
    planner_logs = [log for log in audit_trail if log["decision_maker"] == planner_name]
    assert len(planner_logs) > 0, "Audit trail must contain planner resolution entry!"
    print(f"   Planner Audit Record: [{planner_logs[0]['timestamp']}] Maker: {planner_logs[0]['decision_maker']}")
    print(f"   Notes: {planner_logs[0]['notes']}")
    print(f"   State change: {planner_logs[0]['previous_value']} -> {planner_logs[0]['new_value']}")

    print("\n==================================================================")
    print("STEP 3 CHECKPOINT PASSED: AUDIT, QUEUE & DIFFERENTIATOR ALL VERIFIED!")
    print("==================================================================")

if __name__ == "__main__":
    test_step3()
