"""Application configuration and centralized scoring weights/thresholds."""
import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "sih_bridge.db"))
BASELINE_SCHEDULE_PATH = DATA_DIR / "baseline_schedule.json"

# Starting hypothesis weights (to be tuned at Step 2 against synthetic dataset)
WEIGHT_SEMANTIC = 0.5
WEIGHT_DISCIPLINE = 0.3
WEIGHT_DATE = 0.2

# Confidence threshold for automatic updates vs human review queue
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# LLM provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
