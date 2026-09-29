"""Integration tests for PlanBridge AI FastAPI backend."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PlanBridge AI Engine"
    assert data["database"]["status"] == "connected"
    assert data["database"]["activities_count"] > 0


def test_get_master_schedule():
    response = client.get("/api/v1/schedule")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, list)
    assert len(activities) > 0
    first = activities[0]
    assert "activity_id" in first
    assert "name" in first
    assert "discipline" in first


def test_ingest_text_api():
    payload = {
        "raw_text": "Completed pump suction line spool alignment and welding for Unit 3.",
        "reported_by": "Test Supervisor",
        "discipline_hint": "Piping",
        "source_format": "api_test",
    }
    response = client.post("/api/v1/ingest/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report_id" in data
    assert data["latency_ms"] > 0
    assert data["events_count"] >= 1


def test_ask_ai_memory_endpoint():
    payload = {"query": "What caused the biggest delay?"}
    response = client.post("/api/v1/ask-ai", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "key_metrics" in data
    assert "total_activities" in data["key_metrics"]
