"""Calibration and Threshold Tuning Script for Step 2 Checkpoint."""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BASELINE_SCHEDULE_PATH
from src.database.db_manager import DatabaseManager
from src.pipeline import Pipeline

def run_calibration():
    print("==================================================================")
    print("STEP 2: CALIBRATING EXTRACTION & MATCHING ON MESSY SYNTHETIC DATA")
    print("==================================================================")

    # Use clean in-memory or fresh db for calibration
    test_db_path = str(PROJECT_ROOT / "data" / "calibration_test.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    pipeline = Pipeline(db_path=test_db_path)
    reports_dir = PROJECT_ROOT / "data" / "sample_daily_reports"
    report_files = sorted(list(reports_dir.glob("*.txt")))

    all_scores = []
    print(f"\nProcessing {len(report_files)} messy daily reports:")

    for r_file in report_files:
        print(f"\n--- Ingesting: {r_file.name} ---")
        res = pipeline.process_file(str(r_file))
        print(f"Report ID: {res['report_id']} | Latency: {res['latency_ms']} ms | Events: {res['events_count']}")

        for idx, item in enumerate(res["results"], 1):
            evt = item["event"]
            m = item["match"]
            all_scores.append({
                "file": r_file.name,
                "desc": evt["activity_description"][:45],
                "disc": evt["discipline"],
                "action": evt["action_type"],
                "matched_id": m["candidate_activity_id"],
                "matched_name": m["candidate_name"][:45],
                "sem": m["semantic_score"],
                "disc_score": m["discipline_score"],
                "date_score": m["date_score"],
                "conf": m["confidence_score"],
                "decision": m["decision"],
            })
            print(f"  [{idx}] {evt['activity_description'][:40]}... -> {m['candidate_activity_id']}")
            print(f"      Sem: {m['sem_score'] if 'sem_score' in m else m['semantic_score']:.2f} | Disc: {m['discipline_score']} | Date: {m['date_score']} => Conf: {m['confidence_score']:.3f} [{m['decision']}]")

    print("\n--- Ingesting Spreadsheet: piping_fitup_weld_log.csv ---")
    sheet_path = PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv"
    sheet_res = pipeline.process_file(str(sheet_path))
    print(f"Report ID: {sheet_res['report_id']} | Latency: {sheet_res['latency_ms']} ms | Rows: {sheet_res['events_count']}")
    for idx, item in enumerate(sheet_res["results"], 1):
        m = item["match"]
        print(f"  [Row {idx}] -> {m['candidate_activity_id']} (Conf: {m['confidence_score']:.3f}, {m['decision']})")

    print("\n==================================================================")
    print("THRESHOLD CALIBRATION SUMMARY")
    print("==================================================================")
    auto_count = sum(1 for s in all_scores if s["decision"] == "auto_updated")
    queue_count = sum(1 for s in all_scores if s["decision"] == "queued_for_review")
    print(f"Total Text Events: {len(all_scores)}")
    print(f"  -> Auto-updated (high confidence): {auto_count}")
    print(f"  -> Queued for Planner Review: {queue_count}")

    # Check the low-confidence report specifically
    low_conf_items = [s for s in all_scores if "lowconf" in s["file"]]
    print(f"\nDeliberate Ambiguous Report (report_civil_lowconf_oct07.txt):")
    for item in low_conf_items:
        print(f"  Matched to: {item['matched_id']} with Confidence: {item['conf']:.3f} -> Decision: {item['decision']}")
        assert item["decision"] == "queued_for_review", "Ambiguous report should route to review queue!"

    print("\nSUCCESS: Calibration confirmed. Core pipeline operates properly on messy data!")

if __name__ == "__main__":
    run_calibration()
