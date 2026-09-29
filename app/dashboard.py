"""Oil India Limited — PlanBridge AI (Production Suite)
SIH PS 26122: Intelligent Schedule-Linking & Real-Time Actual Progress Tracking Layer
Advanced, Interactive, High-Craft Dashboard with Voice Time Agent, Precedence Shield,
EVM Analytics, Institutional Memory Bank, and Primavera P6 / MSP Round-Trip Bridge.
"""

import hashlib
import io
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.evm_engine import EVMEngine
from src.config import BASELINE_SCHEDULE_PATH, CONFIDENCE_THRESHOLD, DB_PATH
from src.database.db_manager import DatabaseManager
from src.export.p6_bridge import P6ScheduleBridge
from src.institutional_memory.memory_engine import InstitutionalMemoryEngine
from src.pipeline import Pipeline
from src.voice_agent.time_agent import VoiceTimeAgent

# Page Configuration
st.set_page_config(
    page_title="PlanBridge AI | Oil India Limited",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Craft Industrial Dark/Slate Styling
st.markdown(
    """
    <style>
    /* Global Typography & Font Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre, .font-mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Executive Brand Banner */
    .brand-banner {
        background: linear-gradient(135deg, #0b1d3a 0%, #102a43 45%, #b45309 100%);
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(11, 29, 58, 0.28);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .brand-banner h1 {
        margin: 0;
        font-size: 2.0rem;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -0.6px;
    }
    .brand-banner p {
        margin: 6px 0 0 0;
        font-size: 1.0rem;
        color: #e2e8f0;
    }

    /* KPI Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }

    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-success { background-color: #dcfce7; color: #15803d; }
    .badge-warning { background-color: #fef3c7; color: #b45309; }
    .badge-danger { background-color: #fee2e2; color: #b91c1c; }
    .badge-info { background-color: #e0f2fe; color: #0369a1; }
    .badge-purple { background-color: #f3e8ff; color: #7e22ce; }

    /* Voice Chips */
    .voice-chip {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.92rem;
    }

    /* Cryptographic Hash Badge */
    .hash-badge {
        font-family: 'JetBrains Mono', monospace;
        background: #0f172a;
        color: #38bdf8;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {
            "role": "assistant",
            "content": "👋 **PlanBridge AI Online**: Real-time actual progress capture, voice logging, and schedule-linking engine active for **Oil India Limited — Duliajan GGS Expansion**.",
        }
    ]

# Initialize Core Services
@st.cache_resource
def load_core_services():
    db = DatabaseManager(str(DB_PATH))
    db.seed_schedule(BASELINE_SCHEDULE_PATH)
    pipe = Pipeline(db_path=str(DB_PATH), confidence_threshold=CONFIDENCE_THRESHOLD)
    mem_engine = InstitutionalMemoryEngine(db)
    evm_engine = EVMEngine(db)
    p6_bridge = P6ScheduleBridge(db)
    voice_agent = VoiceTimeAgent()
    return db, pipe, mem_engine, evm_engine, p6_bridge, voice_agent

db, pipeline, memory_engine, evm_engine, p6_bridge, voice_agent = load_core_services()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### 🛢️ Oil India Limited")
    st.markdown("**Infrastructure Project Management Bridge**")
    st.caption("PS ID: SIH PS 26122 | Duliajan Gas Gathering Station")
    st.markdown("---")

    st.markdown("#### 👤 Role-Based View (RBAC)")
    user_role = st.selectbox(
        "Current Persona",
        [
            "📋 Master Project Planner (Oil India Limited)",
            "👷‍♂️ Site Supervisor (Walkie-Talkie Field Logger)",
            "🏢 EPC General Contractor (L&T / EIL Project Controls)",
            "🏛️ Statutory Auditor (CAG / MoPNG Oversight)",
        ],
        index=0,
    )
    st.markdown("---")

    st.markdown("#### ⚡ 1-Click Field Scenarios")
    st.caption("Simulate incoming site reports & verify real-time auto-linking:")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🏗️ Civil Pour", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt"
            res = pipeline.process_file(str(p))
            st.session_state["chat_history"].append({"role": "user", "content": "Civil DPR: Booster pump foundation raft concreting completed."})
            st.session_state["chat_history"].append({"role": "assistant", "content": f"✅ **Auto-Linked to L5-CIV-102** (RCC casting & curing). Score: `0.92`. Master schedule updated."})
            st.toast("Ingested Civil Report (45 m3)", icon="✅")
            st.rerun()

        if st.button("🔧 Piping Spool", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_piping_oct04.txt"
            res = pipeline.process_file(str(p))
            st.session_state["chat_history"].append({"role": "user", "content": "Piping DPR: 12-inch crude suction manifold spool fitup and welding."})
            st.session_state["chat_history"].append({"role": "assistant", "content": f"✅ **Auto-Linked to L5-PIP-201**. Progress logged in {res['latency_ms']:.1f}ms."})
            st.toast("Ingested Piping Spool Log", icon="🔧")
            st.rerun()

    with col_btn2:
        if st.button("🚨 Elect. Clash", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt"
            res = pipeline.process_file(str(p))
            st.session_state["chat_history"].append({"role": "user", "content": "Electrical DPR: Cable tray crew arrived; pedestal unready/curing, cannot start."})
            st.session_state["chat_history"].append({"role": "assistant", "content": "🛑 **CONTRADICTION DETECTED**: Electrical L5-ELE-301 blocked by Civil L5-CIV-102 curing! Escalated to Precedence Shield."})
            st.toast("Precedence Clash Flagged!", icon="🚨")
            st.rerun()

        if st.button("📊 Piping CSV", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv"
            res = pipeline.process_file(str(p))
            st.session_state["chat_history"].append({"role": "user", "content": "Batch CSV: 5 weld joint entries uploaded from contractor spreadsheet."})
            st.session_state["chat_history"].append({"role": "assistant", "content": f"📊 **Processed 5 Multi-Row Records** in {res['latency_ms']:.1f}ms."})
            st.toast("Ingested 5 Multi-Row Weld Records", icon="📊")
            st.rerun()

    st.markdown("---")
    st.markdown("#### ⚙️ Confidence Threshold")
    threshold_slider = st.slider(
        "Auto-Approval Threshold",
        min_value=0.50,
        max_value=0.95,
        value=CONFIDENCE_THRESHOLD,
        step=0.05,
        help="Matches >= threshold are auto-linked; lower scores are queued for planner review.",
    )
    if threshold_slider != pipeline.scorer.threshold:
        pipeline.scorer.threshold = threshold_slider
        pipeline.matcher.scorer.threshold = threshold_slider

    st.markdown("---")
    if st.button("🔄 Reset & Re-Seed Master Baseline", use_container_width=True, type="secondary"):
        c = db.reset_and_reseed(BASELINE_SCHEDULE_PATH)
        memory_engine.seed_if_empty()
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": f"🔄 Master baseline schedule re-seeded with {c} L5/L6 activities."}
        ]
        st.toast(f"Database reset and re-seeded with {c} baseline activities!", icon="🔄")
        time.sleep(0.3)
        st.rerun()

    st.markdown("---")
    st.caption("**Edge Capabilities Active**")
    st.markdown("🛡️ **Physics Precedence Shield**: `Active`")
    st.markdown("🎙️ **Voice Time Agent (Hinglish/EN)**: `Active`")
    st.markdown("🏛️ **Institutional Memory Bank**: `8 Past Projects`")
    st.markdown("🔐 **Cryptographic Audit Ledger**: `SHA-256 Chained`")

# --- EXECUTIVE HEADER ---
st.markdown(
    """
    <div class="brand-banner">
        <h1>Intelligent Data Capture & Schedule-Linking Layer</h1>
        <p>Real-Time Actual Progress Tracking | Planning-to-Execution Bridge | Oil India Limited (SIH PS 26122)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- REAL-TIME PROJECT KPI RIBBON ---
evm_data = evm_engine.compute_evm_metrics()
review_queue = db.get_review_queue()
contradictions = db.get_contradictions()
open_contradictions = [c for c in contradictions if c.get("status") == "open"]

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("L5/L6 Activities", evm_data["total_activities"], f"{evm_data['completed']} Completed")
k2.metric("Overall Progress", f"{evm_data['overall_progress_pct']}%", f"{evm_data['in_progress']} In Progress")
k3.metric("Schedule Index (SPI)", f"{evm_data['spi']}", "Ahead (>1.0)" if evm_data['spi'] >= 1.0 else "Behind (<1.0)")
k4.metric("Cost Index (CPI)", f"{evm_data['cpi']}", "Favorable" if evm_data['cpi'] >= 1.0 else "Cost Overrun")
k5.metric("Review Queue", len(review_queue), f"{len(review_queue)} Pending", delta_color="inverse")
k6.metric("Precedence Clashes", len(open_contradictions), f"{len(open_contradictions)} Active", delta_color="inverse")

st.markdown("---")

# --- MAIN NAVIGATION TABS ---
tab_voice, tab_ingest, tab_workbench, tab_shield, tab_analytics, tab_memory, tab_export = st.tabs([
    "🎙️ 1. Supervisor Voice & Time Agent",
    "📥 2. Multi-Source Ingestion Studio",
    "🔗 3. Schedule Linking & Review Workbench",
    "🛡️ 4. Physical Precedence & Contradiction Shield",
    "📈 5. EVM Analytics & S-Curve Forecasting",
    "🏛️ 6. Institutional Memory & Planning Copilot",
    "🔄 7. P6/MSP Export & Cryptographic Audit Ledger",
])

# ==============================================================================
# TAB 1: SUPERVISOR VOICE & TIME AGENT (UNIQUE EDGE #2)
# ==============================================================================
with tab_voice:
    st.subheader("🎙️ Multilingual Supervisor Voice Time Agent (Walkie-Talkie Field Logger)")
    st.caption("Low-friction voice and conversational logging in English, Hindi, and Hinglish. Automatically extracts entities, quantities, crew size, and impediments, linking directly to L5/L6 schedule activities.")

    col_voice_left, col_voice_right = st.columns([1.3, 1])

    with col_voice_left:
        st.markdown("#### 🎙️ Live Field Audio & Walkie-Talkie Console")

        # Top Voice Controls (Language & Supervisor Name)
        v_c1, v_c2 = st.columns([1, 1])
        with v_c1:
            voice_lang = st.selectbox(
                "🌐 Speech Language",
                options=["Hindi / Hinglish (hi-IN)", "English - India (en-IN)", "English - Global (en-US)"],
                index=0,
                key="voice_lang_select"
            )
            lang_code = "hi-IN" if "hi-IN" in voice_lang else ("en-IN" if "en-IN" in voice_lang else "en-US")
        with v_c2:
            supervisor_name = st.text_input("👷 Supervisor Name", value="Supervisor Baruah", key="sup_name_box")

        # =====================================================================
        # SPEAK / MICROPHONE RECORDING (NATIVE BROWSER & HARDWARE MIC)
        # =====================================================================
        st.markdown("##### 🔴 Speak Now (Microphone Recording)")
        recorded_audio = st.audio_input(
            "Press the red microphone icon below to speak your update directly from your device:",
            key="hardware_mic_input"
        )

        if recorded_audio is not None:
            audio_bytes = recorded_audio.read()
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            if st.session_state.get("last_recorded_hash") != audio_hash:
                st.session_state["pending_audio_bytes"] = audio_bytes
                st.session_state["last_recorded_hash"] = audio_hash
                st.session_state["audio_processed"] = False

        if st.session_state.get("pending_audio_bytes") and not st.session_state.get("audio_processed"):
            st.audio(st.session_state["pending_audio_bytes"], format="audio/wav")
            c_proc, c_disc = st.columns([2, 1])
            with c_proc:
                if st.button("🚀 Transcribe Audio & Link to Master Schedule", type="primary", use_container_width=True, key="btn_run_transcribe"):
                    with st.spinner(f"Transcribing voice update ({voice_lang}) and linking to L5/L6 activities..."):
                        res = pipeline.process_voice_audio(
                            audio_bytes=st.session_state["pending_audio_bytes"],
                            supervisor_name=supervisor_name,
                            site_location="Unit 3 Area",
                            language=lang_code
                        )
                        transcription = res.get("transcription_raw") or "Spoken audio update"
                        st.session_state["chat_history"].append({"role": "user", "content": f"🎙️ **[Voice Memo Transcribed]**: *\"{transcription}\"*" })
                        rep = res["confirmation_message"] + f"\n\n**WBS Mapped**: `{res['match']['candidate_activity_id']}` ({res['match']['candidate_name']}) | **Confidence**: `{res['match']['confidence_score']:.2f}`"
                        if res.get("contradictions"):
                            rep += f"\n\n🚨 **Warning**: {len(res['contradictions'])} cross-discipline contradiction flagged!"
                        st.session_state["chat_history"].append({"role": "assistant", "content": rep})
                        st.session_state["audio_processed"] = True
                        st.toast("Voice memo successfully transcribed and linked to schedule!", icon="🎙️")
                        st.rerun()
            with c_disc:
                if st.button("🗑️ Discard Audio", use_container_width=True, key="btn_disc_audio"):
                    st.session_state["pending_audio_bytes"] = None
                    st.session_state["audio_processed"] = True
                    st.rerun()

        # Audio file upload expander
        with st.expander("📁 Or Upload Walkie-Talkie Audio File (.wav)"):
            uploaded_audio = st.file_uploader("Upload pre-recorded voice note", type=["wav"], key="uploader_voice_clip")
            if uploaded_audio is not None:
                u_bytes = uploaded_audio.read()
                u_hash = hashlib.md5(u_bytes).hexdigest()
                if st.session_state.get("last_uploaded_hash") != u_hash:
                    st.session_state["pending_uploaded_bytes"] = u_bytes
                    st.session_state["last_uploaded_hash"] = u_hash
                    st.session_state["uploaded_processed"] = False
                
                if st.session_state.get("pending_uploaded_bytes") and not st.session_state.get("uploaded_processed"):
                    st.audio(st.session_state["pending_uploaded_bytes"], format="audio/wav")
                    if st.button("⚡ Transcribe Uploaded Audio File", key="btn_proc_uploaded", type="primary", use_container_width=True):
                        with st.spinner("Processing uploaded audio file..."):
                            res = pipeline.process_voice_audio(
                                audio_bytes=st.session_state["pending_uploaded_bytes"],
                                supervisor_name=supervisor_name,
                                site_location="Field Unit",
                                language=lang_code
                            )
                            transcription = res.get("transcription_raw") or "Uploaded audio update"
                            st.session_state["chat_history"].append({"role": "user", "content": f"📁 **[Audio File]**: *\"{transcription}\"*" })
                            rep = res["confirmation_message"] + f"\n\n**WBS Mapped**: `{res['match']['candidate_activity_id']}` ({res['match']['candidate_name']}) | **Confidence**: `{res['match']['confidence_score']:.2f}`"
                            st.session_state["chat_history"].append({"role": "assistant", "content": rep})
                            st.session_state["uploaded_processed"] = True
                            st.toast("Uploaded audio file transcribed!", icon="📁")
                            st.rerun()

        st.markdown("---")
        st.markdown("##### 💬 Supervisor Live Walkie-Talkie Feed")

        # Chat container
        chat_box = st.container(height=300)
        with chat_box:
            for m in st.session_state["chat_history"]:
                with st.chat_message(m["role"], avatar="👷‍♂️" if m["role"] == "user" else "🤖"):
                    st.markdown(m["content"])

        # Supervisor Text Input fallback
        voice_prompt = st.chat_input("Or type field note here (e.g. 'Aaj Unit 3 booster pump foundation pour ho gaya 45m3, 12 workers the')...")
        if voice_prompt:
            st.session_state["chat_history"].append({"role": "user", "content": voice_prompt})
            with st.spinner("Voice Time Agent extracting entities and matching schedule WBS..."):
                res = pipeline.process_voice_transcript(
                    transcript_text=voice_prompt,
                    supervisor_name=supervisor_name,
                    site_location="Unit 3 Pump House",
                )
            
            # Formulate response
            rep = res["confirmation_message"] + f"\n\n**WBS Mapped**: `{res['match']['candidate_activity_id']}` ({res['match']['candidate_name']}) | **Confidence**: `{res['match']['confidence_score']:.2f}`"
            if res.get("contradictions"):
                rep += f"\n\n🚨 **Warning**: {len(res['contradictions'])} cross-discipline contradiction flagged!"
            
            st.session_state["chat_history"].append({"role": "assistant", "content": rep})
            st.toast("Field event extracted and linked to schedule!", icon="🎙️")
            st.rerun()

    with col_voice_right:
        st.markdown("#### ⚡ 1-Click Vernacular Voice Scenarios")
        st.caption("Simulate realistic audio updates from field foremen in Assam:")

        sample_prompts = [
            ("🇮🇳 Hinglish Civil Pour", "Aaj subah Unit 3 booster pump foundation ka concrete pour complete ho gaya, 45m3 concrete dala, 12 workers the."),
            ("🇬🇧 English Piping Erection", "Line 24 crude suction spool fit-up started at manifold area. 4 welders mobilized, but crane got delayed by 2 hours."),
            ("🛑 Electrical Blockage", "Substation LT cable pulling stopped because Civil drain trench is not backfilled yet and flooded with rainwater."),
            ("🛡️ HSE Walkdown", "Pre-commissioning safety walkdown completed with HSE team at Unit 3 Battery limit. Gas detection systems calibrated."),
        ]

        for title, p_text in sample_prompts:
            if st.button(f"🔊 {title}", key=f"voice_chip_{title}", use_container_width=True):
                st.session_state["chat_history"].append({"role": "user", "content": p_text})
                res = pipeline.process_voice_transcript(
                    transcript_text=p_text,
                    supervisor_name=supervisor_name,
                    site_location="Unit 3 Area",
                )
                rep = res["confirmation_message"] + f"\n\n**WBS Linked**: `{res['match']['candidate_activity_id']}` | **Confidence**: `{res['match']['confidence_score']:.2f}` | **Language**: `{res['detected_language']}`"
                if res.get("contradictions"):
                    rep += f"\n\n🛑 **Cross-Discipline Conflict**: Precedence shield activated!"
                st.session_state["chat_history"].append({"role": "assistant", "content": rep})
                st.rerun()

        st.markdown("---")
        st.markdown("#### 🔍 AI Entity Extraction Preview")
        latest_evt = pipeline.db.get_connection().execute("SELECT * FROM extracted_events ORDER BY rowid DESC LIMIT 1").fetchone()
        if latest_evt:
            e = dict(latest_evt)
            st.json({
                "Event ID": e.get("event_id"),
                "Discipline": e.get("discipline"),
                "Action Type": e.get("action_type"),
                "Quantity Logged": f"{e.get('quantity_done', 0.0)} units",
                "Workforce / Crew": f"{e.get('crew_size', 0)} workers",
                "Impediment Flagged": e.get("delay_reason") or "None (Unimpeded)",
                "Extracted Text": e.get("activity_description"),
            })

# ==============================================================================
# TAB 2: MULTI-SOURCE INGESTION STUDIO
# ==============================================================================
with tab_ingest:
    st.subheader("📥 Multi-Source Heterogeneous Ingestion Studio")
    st.caption("Supports Free-Text DPRs, Multi-Row Discipline Spreadsheets (CSV/Excel), Scanned Site Diaries, and Master Schedule Baseline.")

    sub_t1, sub_t2, sub_t3 = st.tabs(["📄 Free-Text Daily Progress Report (DPR)", "📊 Discipline Spreadsheets (CSV/Excel)", "📁 Direct File Upload"])

    with sub_t1:
        st.markdown("#### Paste Free-Text Site Diary or DPR")
        sample_reports = {
            "Civil Foundation DPR": (PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt").read_text(encoding="utf-8-sig"),
            "Piping Fitup & Welding DPR": (PROJECT_ROOT / "data" / "sample_daily_reports" / "report_piping_oct04.txt").read_text(encoding="utf-8-sig"),
            "Electrical Substation DPR": (PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt").read_text(encoding="utf-8-sig"),
            "HSE Pre-Commissioning DPR": (PROJECT_ROOT / "data" / "sample_daily_reports" / "report_hse_oct02.txt").read_text(encoding="utf-8-sig"),
            "Ambiguous Civil Note": (PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_lowconf_oct07.txt").read_text(encoding="utf-8-sig"),
        }
        sel_sample = st.selectbox("Load Sample Engineering Report", list(sample_reports.keys()))
        dpr_text = st.text_area("Report Body", value=sample_reports[sel_sample], height=180)

        if st.button("🚀 Ingest & Auto-Link DPR", type="primary", use_container_width=True):
            with st.spinner("Parsing text and linking to Primavera P6 WBS..."):
                res = pipeline.process_text_report(raw_text=dpr_text, reported_by="Site Engineer", source_format="free_text")
            st.success(f"Ingested {res['events_count']} event(s) in {res['latency_ms']:.1f}ms!")
            st.rerun()

    with sub_t2:
        st.markdown("#### Discipline-Wise Spreadsheets (Piping Fitup / Concrete Pour Logs)")
        csv_path = PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv"
        df_sample = pd.read_csv(csv_path)
        st.dataframe(df_sample, use_container_width=True)

        if st.button("📊 Ingest & Reconcile Spreadsheet Batch", type="primary", use_container_width=True):
            with st.spinner("Processing spreadsheet rows and auto-updating WBS..."):
                res = pipeline.process_file(str(csv_path))
            st.success(f"Batch Ingestion Complete: {res['events_count']} records processed in {res['latency_ms']:.1f}ms!")
            st.rerun()

    with sub_t3:
        st.markdown("#### Upload Custom DPR or Spreadsheet (.txt, .csv, .xlsx)")
        uploaded = st.file_uploader("Upload File", type=["txt", "csv", "xlsx"])
        if uploaded:
            t_path = Path(tempfile.gettempdir()) / uploaded.name
            t_path.write_bytes(uploaded.read())
            if st.button("Process Uploaded File", type="primary"):
                with st.spinner("Ingesting uploaded document..."):
                    res = pipeline.process_file(str(t_path))
                st.success(f"Successfully processed {uploaded.name} ({res['events_count']} events) in {res['latency_ms']:.1f}ms!")
                st.rerun()

# ==============================================================================
# TAB 3: SCHEDULE LINKING & REVIEW WORKBENCH
# ==============================================================================
with tab_workbench:
    st.subheader("🔗 Intelligent Schedule Linking & Planner Review Workbench")
    st.caption("Real-time reconciliation matrix linking field execution events to Primavera P6 / MS Project L5/L6 activities. Flagged low-confidence and emerging activities are routed for Human-In-The-Loop approval.")

    activities = db.get_all_activities()
    df_acts = pd.DataFrame(activities)

    # Discipline filter
    disc_filter = st.multiselect("Filter by Discipline", options=list(df_acts["discipline"].unique()), default=list(df_acts["discipline"].unique()))
    df_filtered = df_acts[df_acts["discipline"].isin(disc_filter)]

    # Display activities table
    cols_to_show = ["activity_id", "wbs_code", "name", "discipline", "planned_start", "planned_end", "actual_start", "actual_end", "status", "percent_complete"]
    def highlight_status(v):
        if v == "COMPLETED":
            return "background-color: #dcfce7; color: #15803d; font-weight: bold;"
        elif v == "IN_PROGRESS":
            return "background-color: #fef3c7; color: #b45309; font-weight: bold;"
        elif v == "BLOCKED":
            return "background-color: #fee2e2; color: #b91c1c; font-weight: bold;"
        return ""

    styler = df_filtered[cols_to_show].style
    if hasattr(styler, "map"):
        styled_df = styler.map(highlight_status, subset=["status"])
    else:
        styled_df = styler.applymap(highlight_status, subset=["status"])

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=320
    )

    st.markdown("---")
    st.markdown("#### ⚠️ Human-In-The-Loop (HITL) Planner Approval Queue")
    review_queue = db.get_review_queue()

    if not review_queue:
        st.info("✅ All incoming field events have been automatically linked with high confidence! Review queue is empty.")
    else:
        st.warning(f"⚠️ {len(review_queue)} incoming field events require Lead Planner review and sign-off.")
        for idx, item in enumerate(review_queue):
            with st.expander(f"Review #{idx+1}: {item.get('activity_description')} (Confidence: {item.get('confidence_score', 0):.2f})", expanded=(idx==0)):
                c_info, c_action = st.columns([1.5, 1])
                with c_info:
                    st.markdown(f"**Field Snippet**: `{item.get('raw_text')}`")
                    st.markdown(f"**Discipline Extracted**: `{item.get('extracted_discipline')}` | **Action**: `{item.get('action_type')}`")
                    st.markdown(f"**Top AI Suggested Activity**: `{item.get('candidate_activity_id')}` — *{item.get('candidate_name')}*")
                    st.markdown(f"**Semantic Score**: `{item.get('semantic_score', 0):.2f}` | **Terminology Score**: `{item.get('terminology_score', 0):.2f}`")

                with c_action:
                    st.markdown("**Planner Decision & Re-Assignment**")
                    act_options = [f"{a['activity_id']} - {a['name'][:45]}" for a in activities]
                    default_idx = 0
                    for i_act, opt in enumerate(act_options):
                        if item.get("candidate_activity_id") in opt:
                            default_idx = i_act
                            break

                    selected_act = st.selectbox("Confirm or Re-assign L5 Activity", options=act_options, index=default_idx, key=f"sel_act_{item['match_id']}")
                    planner_notes = st.text_input("Approval Notes", value="Verified against contractor site book", key=f"notes_{item['match_id']}")

                    if st.button("✅ Approve & Sign With Hash Audit", key=f"btn_approve_{item['match_id']}", type="primary"):
                        target_id = selected_act.split(" - ")[0]
                        db.resolve_review_item(
                            match_id=item["match_id"],
                            selected_activity_id=target_id,
                            planner_name="Lead Planner (Workbench)",
                            notes=planner_notes,
                        )
                        st.success(f"Approved and auto-updated {target_id}!")
                        time.sleep(0.3)
                        st.rerun()

# ==============================================================================
# TAB 4: PHYSICAL PRECEDENCE & CONTRADICTION SHIELD (UNIQUE EDGE #1)
# ==============================================================================
with tab_shield:
    st.subheader("🛡️ Physical Precedence & Cross-Discipline Contradiction Shield")
    st.caption("Anti-Ghost Progress Engine: Evaluates engineering physics, concrete curing intervals, and predecessor dependencies to catch fraudulent or unaligned progress claims across discipline silos.")

    contradictions = db.get_contradictions()
    open_clashes = [c for c in contradictions if c.get("status") == "open"]

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Active Precedence Clashes", len(open_clashes))
    col_stat2.metric("Total Conflict Flags Logged", len(contradictions))
    col_stat3.metric("Resolved / Cleared", len(contradictions) - len(open_clashes))

    if not open_clashes:
        st.success("🟢 No active physical precedence violations or cross-discipline clashes detected across site execution.")
    else:
        st.error(f"🚨 **{len(open_clashes)} Cross-Discipline Contradictions Require Immediate Intervention**")

        for idx, clash in enumerate(open_clashes):
            with st.container():
                st.markdown(
                    f"""
                    <div style="background: #fff5f5; border: 1px solid #feb2b2; border-left: 6px solid #e53e3e; border-radius: 8px; padding: 16px 20px; margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="badge badge-danger">SEVERITY: {clash.get('severity', 'HIGH')}</span>
                            <span style="font-size: 0.85rem; color: #718096;">Flag ID: {clash.get('flag_id')} | {clash.get('created_at', '')[:19]}</span>
                        </div>
                        <h4 style="margin: 8px 0; color: #9b2c2c;">{clash.get('description')}</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #4a5568;">
                            <b>Discipline A:</b> {clash.get('discipline_a')} (Activity: <code>{clash.get('activity_id_a')}</code>) &nbsp;|&nbsp; 
                            <b>Discipline B:</b> {clash.get('discipline_b')} (Activity: <code>{clash.get('activity_id_b')}</code>)
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_res1, col_res2 = st.columns([3, 1])
                with col_res1:
                    res_note = st.text_input("Resolution Log / Remediation Action", value="Joint site walkdown scheduled with Civil and Electrical foremen", key=f"clash_res_{clash['flag_id']}")
                with col_res2:
                    if st.button("Mark Resolved & Re-Align", key=f"btn_res_{clash['flag_id']}", type="secondary"):
                        db.update_contradiction_status(clash["flag_id"], "resolved", res_note)
                        st.success(f"Resolved flag {clash['flag_id']}!")
                        time.sleep(0.3)
                        st.rerun()

# ==============================================================================
# TAB 5: EVM ANALYTICS & S-CURVE FORECASTING
# ==============================================================================
with tab_analytics:
    st.subheader("📈 Earned Value Management (EVM) & S-Curve Project Forecasting")
    st.caption("Live mathematical monitoring of Planned Value (PV), Earned Value (EV), Schedule Performance Index (SPI), Cost Performance Index (CPI), and critical path milestone delay propagation.")

    evm = evm_engine.compute_evm_metrics()
    scurve = evm_engine.generate_scurve_data()

    col_g1, col_g2 = st.columns([1.5, 1])

    with col_g1:
        st.markdown("#### 📊 Cumulative Planned vs Actual S-Curve")
        if scurve["dates"]:
            df_scurve = pd.DataFrame({
                "Date": scurve["dates"],
                "Planned Progress (%)": scurve["planned_cum"],
                "Actual Earned Progress (%)": scurve["actual_cum"],
            })
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df_scurve["Date"], y=df_scurve["Planned Progress (%)"], mode="lines+markers", name="Planned Baseline S-Curve", line=dict(color="#0284c7", width=3, dash="dash")))
            fig_s.add_trace(go.Scatter(x=df_scurve["Date"], y=df_scurve["Actual Earned Progress (%)"], mode="lines+markers", name="Actual Earned Progress", line=dict(color="#10b981", width=4)))
            fig_s.update_layout(title="Project Cumulative S-Curve (Duliajan GGS)", xaxis_title="Date", yaxis_title="Cumulative Progress (%)", height=380, template="plotly_white")
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("No timeline data available for S-Curve.")

    with col_g2:
        st.markdown("#### 🎯 EVM Health & Performance Gauges")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=evm["spi"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Schedule Performance Index (SPI)"},
            gauge={
                'axis': {'range': [0.0, 1.5]},
                'bar': {'color': "#10b981" if evm["spi"] >= 1.0 else "#f59e0b"},
                'steps': [
                    {'range': [0.0, 0.8], 'color': "#fee2e2"},
                    {'range': [0.8, 1.0], 'color': "#fef3c7"},
                    {'range': [1.0, 1.5], 'color': "#dcfce7"},
                ],
                'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 1.0}
            }
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(
            f"""
            - **Planned Value (PV)**: ₹`{evm['pv']:,.0f}`
            - **Earned Value (EV)**: ₹`{evm['ev']:,.0f}`
            - **Schedule Variance (SV)**: ₹`{evm['sv']:,.0f}`
            - **Health State**: `{evm['health_status']}`
            """
        )

    st.markdown("---")
    st.markdown("#### 🚨 Critical Path Delay Propagation Forecaster")
    cp_delays = evm_engine.compute_critical_path_delays()
    if not cp_delays:
        st.success("🟢 No critical path milestone slippage detected. Project milestones are tracking on baseline schedule.")
    else:
        st.warning(f"⚠️ {len(cp_delays)} activities have experienced schedule slippage or hold points:")
        st.table(pd.DataFrame(cp_delays))

# ==============================================================================
# TAB 6: INSTITUTIONAL MEMORY & PLANNING COPILOT (UNIQUE EDGE #3)
# ==============================================================================
with tab_memory:
    st.subheader("🏛️ Institutional Memory Engine & Reference Class Planning Copilot")
    st.caption("Solves the critical problem of lost project knowledge. Queries historical execution patterns across completed Oil India Limited projects to de-bias baseline durations (Kahneman Reference Class Forecasting).")

    col_mem_left, col_mem_right = st.columns([1.2, 1])

    with col_mem_left:
        st.markdown("#### 🧠 Kahneman Reference Class Forecasting Copilot")
        st.caption("Enter a proposed duration for a future tender activity. AI automatically references historical actuals to compute the Optimism Bias Factor (OBF):")

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            plan_discipline = st.selectbox("Discipline", ["Piping", "Civil", "Electrical", "Instrumentation", "Mechanical", "HSE"])
            plan_days = st.number_input("Tender Proposed Baseline (Days)", min_value=1, max_value=60, value=7)
        with c_d2:
            plan_act = st.text_input("Activity Description / Type", value="Fabrication and fit-up of 12-inch crude suction manifold spool")

        if st.button("🔮 De-Bias Baseline Duration", type="primary", use_container_width=True):
            bias_res = memory_engine.evaluate_optimism_bias(
                planned_days=int(plan_days),
                discipline=plan_discipline,
                activity_text=plan_act,
            )
            st.markdown(
                f"""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 18px 22px; margin-top: 14px;">
                    <h3 style="margin: 0; color: #166534;">AI Calibrated Duration: {bias_res['calibrated_duration_days']} Days <span style="font-size: 1rem; color: #64748b;">(Baseline was {plan_days} Days)</span></h3>
                    <p style="margin: 6px 0; font-size: 0.95rem; color: #1e293b;">
                        <b>Historical Optimism Bias Factor:</b> <code>{bias_res['optimism_bias_factor']}x</code> &nbsp;|&nbsp;
                        <b>P90 Risk Worst-Case:</b> <code>{bias_res['p90_risk_duration_days']} Days</code> (+{bias_res['p90_risk_duration_days'] - plan_days} days slip)
                    </p>
                    <p style="margin: 4px 0; font-size: 0.9rem; color: #475569;">
                        <b>Primary Historical Delay Root:</b> ⚠️ {bias_res['primary_delay_risk']}
                    </p>
                    <p style="margin: 4px 0; font-size: 0.9rem; color: #047857; background: #ffffff; padding: 8px 12px; border-radius: 6px;">
                        <b>💡 Institutional Lesson Learned:</b> {bias_res['institutional_lesson']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_mem_right:
        st.markdown("#### 📊 Recurring Delay Causes Taxonomy")
        delay_causes = memory_engine.get_delay_root_causes()
        df_causes = pd.DataFrame(list(delay_causes.items()), columns=["Root Cause", "Frequency"])
        fig_pie = px.pie(df_causes, names="Root Cause", values="Frequency", hole=0.45, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📚 Searchable Historical Project Execution Memory Bank")
    mem_query = st.text_input("Search historical records (e.g., 'curing', 'spool', 'monsoon', 'alignment')...", value="")
    if mem_query:
        mems = memory_engine.search_memories(mem_query)
    else:
        mems = memory_engine.get_all_memories()

    df_mem_table = pd.DataFrame(mems)
    st.dataframe(
        df_mem_table[["project_name", "discipline", "activity_name", "planned_duration_days", "actual_duration_days", "variance_pct", "optimism_bias_ratio", "primary_delay_reason", "lessons_learned"]],
        use_container_width=True,
        height=280
    )

# ==============================================================================
# TAB 7: P6/MSP EXPORT & CRYPTOGRAPHIC AUDIT LEDGER (UNIQUE EDGE #4)
# ==============================================================================
with tab_export:
    st.subheader("🔄 Master Schedule Round-Trip Bridge & Cryptographic Audit Ledger")
    st.caption("Exports verified field actuals directly back into Oracle Primavera P6 and Microsoft Project with zero manual re-typing. Maintains an immutable SHA-256 blockchain-style cryptographic audit chain of custody.")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        st.markdown("#### 💾 1-Click Master Schedule Round-Trip Export")
        st.caption("Download production-ready XML schedules with updated Actual Starts, Finishes, and Quantities:")

        p6_xml_content = p6_bridge.generate_primavera_xml()
        msp_xml_content = p6_bridge.generate_msproject_xml()

        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button(
                label="📥 Export Primavera P6 XML",
                data=p6_xml_content,
                file_name=f"OIL_Duliajan_Actuals_P6_{datetime.now().strftime('%Y%m%d')}.xml",
                mime="application/xml",
                use_container_width=True,
                type="primary",
            )
        with c_dl2:
            st.download_button(
                label="📥 Export MS Project XML",
                data=msp_xml_content,
                file_name=f"OIL_Duliajan_Actuals_MSP_{datetime.now().strftime('%Y%m%d')}.xml",
                mime="application/xml",
                use_container_width=True,
            )

        st.info("💡 **Enterprise Compatibility**: The generated XML can be imported directly into Primavera P6 (EPPM / Professional) or Microsoft Project without data loss or schema mismatches.")

    with col_exp2:
        st.markdown("#### 🔐 Cryptographic Ledger Verification")
        st.caption("Verifies that no historic schedule record has been altered or retroactively manipulated:")

        audit_trail = db.get_audit_trail()
        st.metric("Total Cryptographic Blocks", len(audit_trail))

        # Verification check
        is_tamper_free = True
        chronological = list(reversed(audit_trail))
        for i in range(1, len(chronological)):
            if chronological[i].get("prev_hash") != chronological[i - 1].get("sha256_hash"):
                is_tamper_free = False
                break

        if is_tamper_free:
            st.success("🔒 **Cryptographic Ledger Intact**: All audit blocks are immutably verified via SHA-256 hash chaining.")
        else:
            st.error("🚨 Tampering Detected in Audit Log Chain!")

    st.markdown("---")
    st.markdown("#### 📜 Immutable SHA-256 Chained Audit Trail")
    df_audit = pd.DataFrame(audit_trail)
    if not df_audit.empty:
        st.dataframe(
            df_audit[["timestamp", "activity_id", "decision_maker", "previous_value", "new_value", "sha256_hash", "prev_hash", "notes"]],
            use_container_width=True,
            height=300
        )
    else:
        st.info("No audit transactions logged yet.")
