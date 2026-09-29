"""Tests for Voice Time Agent, Institutional Memory, Cryptographic Hash Chain, and P6 Export."""
import json
from pathlib import Path
from src.analytics.evm_engine import EVMEngine
from src.database.db_manager import DatabaseManager
from src.export.p6_bridge import P6ScheduleBridge
from src.institutional_memory.memory_engine import InstitutionalMemoryEngine
from src.pipeline import Pipeline
from src.voice_agent.time_agent import VoiceTimeAgent


def test_voice_time_agent_multilingual():
    agent = VoiceTimeAgent()
    
    # 1. Test Hinglish field transcript
    hinglish_text = "Aaj subah Unit 3 booster pump foundation ka concrete pour complete ho gaya, 45m3 concrete dala, 12 workers the."
    res = agent.parse_voice_log(hinglish_text, supervisor_name="Supervisor Baruah")
    evt = res["event"]
    
    assert res["detected_language"] == "hinglish"
    assert evt.discipline == "Civil"
    assert evt.action_type == "completed"
    assert evt.quantity_done == 45.0
    assert evt.crew_size == 12
    assert "Supervisor Baruah" in res["confirmation_message"]

    # 2. Test English transcript with delay reason
    eng_text = "Line 24 crude suction spool fit-up started at manifold area. 4 welders mobilized, but crane got delayed by 2 hours."
    res2 = agent.parse_voice_log(eng_text, supervisor_name="Lead Welder Smith")
    evt2 = res2["event"]

    assert evt2.discipline == "Piping"
    assert evt2.action_type == "started"
    assert evt2.crew_size == 4
    assert evt2.delay_reason is not None
    assert "crane got delayed" in evt2.delay_reason.lower()


def test_institutional_memory_and_bias_calculator(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = DatabaseManager(str(db_file))
    engine = InstitutionalMemoryEngine(db)

    # Verify seed data
    memories = engine.get_all_memories()
    assert len(memories) >= 8

    # Verify search
    piping_mems = engine.search_memories("spool")
    assert len(piping_mems) > 0
    assert any("Piping" == m["discipline"] for m in piping_mems)

    # Verify delay breakdown
    delay_breakdown = engine.get_delay_root_causes()
    assert len(delay_breakdown) > 0

    # Verify Optimism Bias Reference Class Forecasting
    eval_result = engine.evaluate_optimism_bias(
        planned_days=7,
        discipline="Piping",
        activity_text="12-inch crude suction manifold spool"
    )
    assert eval_result["planned_days"] == 7
    assert eval_result["optimism_bias_factor"] > 1.0
    assert eval_result["calibrated_duration_days"] >= 7
    assert "institutional_lesson" in eval_result


def test_cryptographic_audit_hash_chain(tmp_path):
    db_file = tmp_path / "test_audit.db"
    db = DatabaseManager(str(db_file))
    db.seed_schedule()

    # Apply 3 updates and verify blockchain-style hash continuity
    db.apply_schedule_update("L5-CIV-101", "started", "2026-10-01", "Planner A", notes="Update 1")
    db.apply_schedule_update("L5-CIV-101", "progress", "2026-10-02", "Planner B", notes="Update 2")
    db.apply_schedule_update("L5-CIV-101", "completed", "2026-10-03", "Planner C", notes="Update 3")

    audit_trail = db.get_audit_trail()
    assert len(audit_trail) >= 3

    # Check hash chaining: each row's prev_hash must equal the previous entry's sha256_hash
    # audit_trail is ordered timestamp DESC, so reverse for chronological check
    chronological = list(reversed(audit_trail[-3:]))
    for i in range(1, len(chronological)):
        assert chronological[i]["prev_hash"] == chronological[i - 1]["sha256_hash"]
        assert len(chronological[i]["sha256_hash"]) == 64


def test_primavera_and_msproject_export(tmp_path):
    db_file = tmp_path / "test_export.db"
    db = DatabaseManager(str(db_file))
    db.seed_schedule()
    
    bridge = P6ScheduleBridge(db)
    p6_xml = bridge.generate_primavera_xml("Test Oil India Project")
    assert "<PrimaveraXML" in p6_xml
    assert "<Activity>" in p6_xml
    assert "L5-CIV-101" in p6_xml

    msp_xml = bridge.generate_msproject_xml("Test Oil India Project")
    assert "<Project" in msp_xml
    assert "<Task>" in msp_xml
    assert "L5-CIV-101" in msp_xml


def test_evm_analytics_engine(tmp_path):
    db_file = tmp_path / "test_evm.db"
    db = DatabaseManager(str(db_file))
    db.seed_schedule()

    evm = EVMEngine(db)
    metrics = evm.compute_evm_metrics()
    assert metrics["total_activities"] > 0
    assert metrics["spi"] >= 0.0
    assert metrics["cpi"] >= 0.0

    scurve = evm.generate_scurve_data()
    assert "dates" in scurve
    assert "planned_cum" in scurve
    assert "actual_cum" in scurve
