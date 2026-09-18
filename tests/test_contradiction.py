"""Verification of Cross-Discipline Contradiction Detection."""
import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import DatabaseManager
from src.pipeline import Pipeline


@pytest.fixture
def contradiction_pipeline(tmp_path):
    db_file = str(tmp_path / "test_contradiction.db")
    return Pipeline(db_path=db_file)


def test_planted_contradiction_detection(contradiction_pipeline):
    # Step 1: Civil logs foundation complete on Oct 3
    civ_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt")
    res_civ = contradiction_pipeline.process_file(civ_file)
    assert res_civ["events_count"] > 0

    civ_act = contradiction_pipeline.db.get_activity("L5-CIV-102")
    assert civ_act["status"] == "COMPLETED"

    # Step 2: Electrical logs cable tray blocked due to unaligned/incomplete foundation on Oct 5
    ele_file = str(PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt")
    res_ele = contradiction_pipeline.process_file(ele_file)
    assert res_ele["events_count"] > 0

    # Step 3: Verify contradiction flags are stored and detail the clash
    flags = contradiction_pipeline.db.get_contradictions()
    assert len(flags) > 0

    # Find the Civil vs Electrical contradiction
    ele_clashes = [
        f for f in flags
        if ("Civil" in (f["discipline_a"], f["discipline_b"]) and "Electrical" in (f["discipline_a"], f["discipline_b"]))
        or ("L5-CIV-102" in (f["activity_id_a"], f["activity_id_b"]))
    ]
    assert len(ele_clashes) > 0
    clash = ele_clashes[0]
    assert clash["status"] == "open"
    assert "Cross-Discipline Conflict" in clash["description"] or "Clash" in clash["description"]
