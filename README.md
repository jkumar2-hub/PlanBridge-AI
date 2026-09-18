# SIH PS 26122: Intelligent Data Capture & Schedule-Linking Layer
### Planning-to-Execution Bridge for Oil India Limited (Infrastructure Projects)

## Overview
This platform bridges master schedules (Primavera P6 / MS Project L5/L6 activities) and unstructured field reports (daily site logs, contractor spreadsheets, conversational updates). It automatically parses progress events, performs semantic and discipline-aware candidate matching, scores confidence, routes ambiguous updates to a planner review queue, logs all decisions immutably, and features **Cross-Discipline Contradiction Detection**.

## Repository Structure
```
sih-ps26122-bridge/
├── data/
│   ├── baseline_schedule.json          # 26 L5/L6 activities across Civil, Piping, Electrical, Inst, HSE
│   ├── sample_daily_reports/           # 6 varied messy daily field reports (includes planted contradiction)
│   └── sample_spreadsheets/            # Multi-row discipline CSV log
├── src/
│   ├── config.py                       # Centralized configuration, weights, and thresholds
│   ├── database/                       # SQLite schema & database manager
│   ├── ingestion/                      # Free-text & CSV/Excel parsers
│   ├── extraction/                     # Structured Pydantic models & LLM extraction
│   ├── matching/                       # sentence-transformers & confidence scoring
│   ├── contradiction/                  # Cross-discipline contradiction detector
│   └── pipeline.py                     # Unified end-to-end processing pipeline
├── app/
│   └── dashboard.py                    # 3-view Streamlit application & Time Agent
├── tests/                              # Automated integration and contradiction tests
└── future_work/                        # Documented deliberate scope cuts & roadmap
```

## Quick Start & Setup

### 1. Environment Setup
```bash
# Clone the repository (or navigate to workspace)
cd sih-ps26122-bridge

# Create and activate Python 3.11 virtual environment
py -3.11 -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure LLM API Keys
Copy `.env.example` to `.env` and set your API key:
```bash
cp .env.example .env
```
Choose `gemini` (recommended) or `openai` as your provider.

### 3. Running the Pipeline & Dashboard
```bash
# Run pipeline test
python -m pytest tests/

# Launch Streamlit dashboard
streamlit run app/dashboard.py
```
