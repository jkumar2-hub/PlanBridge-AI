"""End-to-End Pipeline Integration Tests."""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import DatabaseManager
from src.pipeline import Pipeline


@pytest.fixture
def test_pipeline(tmp_path):
    db_file = str(tmp_path / "test_pipe.db")
    pipe = Pipeline(db_path=db_file)
    return pipe


def test_baseline_schedule_loading(test_pipeline):
    activities = test_pipeline.db.get_all_activities()
    assert len(activities) >= 25
    civ_act = test_pipeline.db.get_activity("L5-CIV-102")
    assert civ_act is not None
    assert civ_act["discipline"] == "Civil"
    assert civ_act["status"] == "NOT_STARTED"


def test_high_confidence_auto_update(test_pipeline):
    civ_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt")
    res = test_pipeline.process_file(civ_file)
    assert res["events_count"] > 0
    assert res["latency_ms"] > 0

    # L5-CIV-102 should be COMPLETED
    act = test_pipeline.db.get_activity("L5-CIV-102")
    assert act["status"] == "COMPLETED"
    assert act["actual_end"] is not None

    # Audit log should record system update
    logs = test_pipeline.db.get_audit_trail()
    assert len(logs) > 0
    assert any(l["activity_id"] == "L5-CIV-102" and l["decision_maker"] == "system" for l in logs)


def test_low_confidence_routing_to_review_queue(test_pipeline):
    ambiguous_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_lowconf_oct07.txt")
    res = test_pipeline.process_file(ambiguous_file)
    assert res["events_count"] > 0

    queue = test_pipeline.db.get_review_queue()
    assert len(queue) > 0

    # Verify top candidates are stored for the planner
    item = queue[0]
    top_cands = json.loads(item["top_candidates"])
    assert len(top_cands) >= 1
    assert "activity_id" in top_cands[0]


def test_planner_manual_resolution(test_pipeline):
    ambiguous_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_lowconf_oct07.txt")
    test_pipeline.process_file(ambiguous_file)

    queue = test_pipeline.db.get_review_queue()
    assert len(queue) > 0
    target_item = queue[0]

    planner_name = "Lead Planner Roy"
    ok = test_pipeline.db.resolve_review_item(
        match_id=target_item["match_id"],
        selected_activity_id="L5-CIV-105",
        planner_name=planner_name,
        notes="Confirmed drain trench patching work.",
    )
    assert ok is True

    # Check updated schedule activity
    act = test_pipeline.db.get_activity("L5-CIV-105")
    assert act["status"] == "IN_PROGRESS"

    # Check audit log records planner resolution
    logs = test_pipeline.db.get_audit_trail()
    planner_logs = [l for l in logs if l["decision_maker"] == planner_name]
    assert len(planner_logs) == 1
    assert "Confirmed drain trench" in planner_logs[0]["notes"]


def test_spreadsheet_ingestion(test_pipeline):
    csv_file = str(PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv")
    res = test_pipeline.process_file(csv_file)
    assert res["events_count"] == 5

    # Check that piping activities got updated
    act_pip = test_pipeline.db.get_activity("L5-PIP-201")
    assert act_pip["status"] == "COMPLETED"


def test_duplicate_report_handling(test_pipeline):
    report_text = "Fit-up of 12 inch suction manifold spool finished by 2pm. Inspector signed fitup card."
    # Process first time
    res1 = test_pipeline.process_text_report(report_text, reported_by="Foreman")
    logs_count_1 = len(test_pipeline.db.get_audit_trail())

    # Process second identical time
    res2 = test_pipeline.process_text_report(report_text, reported_by="Foreman")
    logs_count_2 = len(test_pipeline.db.get_audit_trail())

    # Schedule should remain valid and consistent
    act = test_pipeline.db.get_activity("L5-PIP-201")
    assert act["status"] in ("COMPLETED", "IN_PROGRESS")


def test_graceful_handling_empty_or_broken_input(test_pipeline):
    res = test_pipeline.process_text_report("   \n\n  ", reported_by="Tester")
    assert res["events_count"] >= 1
    assert res["latency_ms"] >= 0
