"""Oil India Limited — Intelligent Schedule-Linking Layer & Progress Tracking
SIH PS 26122 (Planning-to-Execution Bridge)
Interactive UI/UX Dashboard built with Streamlit, Plotly, and pandas.
"""
import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BASELINE_SCHEDULE_PATH, CONFIDENCE_THRESHOLD, DB_PATH
from src.database.db_manager import DatabaseManager
from src.pipeline import Pipeline

st.set_page_config(
    page_title="Oil India Limited | Schedule Bridge",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for enterprise look & feel
st.markdown(
    """
    <style>
    .brand-banner {
        background: linear-gradient(135deg, #0b2545 0%, #134074 60%, #1d4e89 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(11, 37, 69, 0.25);
    }
    .brand-banner h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .brand-banner p {
        margin: 6px 0 0 0;
        font-size: 0.92rem;
        color: #e2e8f0;
    }
    .badge-auto {
        background-color: #d1fae5;
        color: #065f46;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-queue {
        background-color: #fef3c7;
        color: #92400e;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-clash {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource
def get_pipeline(threshold: float = CONFIDENCE_THRESHOLD):
    return Pipeline(db_path=str(DB_PATH), confidence_threshold=threshold)

pipeline = get_pipeline()
db = pipeline.db

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### 🛢️ Oil India Limited")
    st.caption("**Unit 3 Booster Pump & Manifold Expansion**")
    st.markdown("---")

    st.markdown("#### ⚙️ Engine Parameters")
    threshold_slider = st.slider(
        "Confidence Decision Threshold",
        min_value=0.50,
        max_value=0.95,
        value=CONFIDENCE_THRESHOLD,
        step=0.05,
        help="Matches with confidence >= threshold auto-update; lower scores go to the review queue.",
    )
    if threshold_slider != pipeline.scorer.threshold:
        pipeline.scorer.threshold = threshold_slider
        pipeline.matcher.scorer.threshold = threshold_slider

    st.markdown("#### ⚡ Quick Demo Scenarios")
    st.caption("Click to inject realistic field updates:")

    if st.button("🏗️ 1. Civil: Foundation Done", use_container_width=True):
        p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt"
        res = pipeline.process_file(str(p))
        st.toast(f"Ingested Civil Log ({res['latency_ms']:.1f} ms)", icon="✅")
        st.rerun()

    if st.button("🚨 2. Electrical: Contradiction Clash", use_container_width=True):
        p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt"
        res = pipeline.process_file(str(p))
        st.toast(f"Ingested Electrical Clash ({res['latency_ms']:.1f} ms)", icon="🚨")
        st.rerun()

    if st.button("🔧 3. Piping: Suction Spool Log", use_container_width=True):
        p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_piping_oct04.txt"
        res = pipeline.process_file(str(p))
        st.toast(f"Ingested Piping Log ({res['latency_ms']:.1f} ms)", icon="🔧")
        st.rerun()

    if st.button("📊 4. Piping CSV (5 Rows)", use_container_width=True):
        p = PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv"
        res = pipeline.process_file(str(p))
        st.toast(f"Ingested CSV Rows ({res['latency_ms']:.1f} ms)", icon="📊")
        st.rerun()

    if st.button("❓ 5. Ambiguous Civil Note", use_container_width=True):
        p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_lowconf_oct07.txt"
        res = pipeline.process_file(str(p))
        st.toast(f"Ingested Vague Note ({res['latency_ms']:.1f} ms)", icon="🟡")
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset & Re-seed DB", use_container_width=True, type="secondary"):
        count = db.reset_and_reseed(BASELINE_SCHEDULE_PATH)
        st.toast(f"Reset database & re-seeded {count} schedule activities!", icon="🔄")
        time.sleep(0.4)
        st.rerun()

    st.markdown("---")
    st.caption("**Live Status**")
    st.markdown("🟢 **Model**: `all-MiniLM-L6-v2` (Local)")
    st.markdown("🟢 **DB**: SQLite (`sih_bridge.db`)")
    st.markdown(f"🟢 **Extractor**: `{pipeline.extractor.client_type or 'Structured JSON'}`")

# --- MAIN HEADER ---
st.markdown(
    """
    <div class="brand-banner">
        <h1>Intelligent Data Capture & Schedule-Linking Layer</h1>
        <p>Real-Time Actual Progress Tracking | Planning-to-Execution Bridge | Oil India Limited (SIH PS 26122)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

activities = db.get_all_activities()
total_acts = len(activities)
completed_acts = sum(1 for a in activities if a.get("status") == "COMPLETED")
in_progress_acts = sum(1 for a in activities if a.get("status") == "IN_PROGRESS")
not_started_acts = sum(1 for a in activities if a.get("status") == "NOT_STARTED")
review_items = db.get_review_queue()
contradictions = db.get_contradictions()
open_contradictions = [c for c in contradictions if c.get("status") == "open"]

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Activities", total_acts)
k2.metric("Completed", completed_acts, f"{(completed_acts/total_acts)*100:.1f}%")
k3.metric("In Progress", in_progress_acts)
k4.metric("Not Started", not_started_acts)
k5.metric("Review Queue", len(review_items), f"{len(review_items)} pending", delta_color="inverse")
k6.metric("Contradictions", len(open_contradictions), f"{len(open_contradictions)} active", delta_color="inverse")

st.markdown("---")

tab_live, tab_review, tab_schedule, tab_audit = st.tabs([
    "📡 1. Live Feed & Time Agent",
    "⚠️ 2. Review + Contradictions",
    "📊 3. Master Schedule & Analytics",
    "📜 4. Searchable Audit Trail & Memory",
])


# ==============================================================================
# VIEW 1: LIVE FEED & TIME AGENT
# ==============================================================================
with tab_live:
    st.subheader("Field Input & Ingestion Stream")
    
    col_input, col_feed = st.columns([1.1, 1.4])
    
    with col_input:
        st.markdown("### 💬 Conversational Time Agent")
        st.write("Site supervisors log raw field updates in plain language:")
        
        with st.form(key="time_agent_form"):
            reporter_name = st.text_input("Supervisor / Reporter Name", value="D. Phukan (Elect. Supervisor)")
            discipline_hint = st.selectbox("Discipline Hint (Optional)", ["Auto-Detect", "Civil", "Piping", "Electrical", "Instrumentation", "HSE"])
            field_text = st.text_area(
                "Shift Notes / Diary Entry",
                value="Cable tray brackets team mobilized with 6 riggers. Inspected pump house for cable tray laying; found foundation pedestals still incomplete and unaligned, cannot start cable tray installation.",
                height=110,
            )
            submit_log = st.form_submit_button("⚡ Submit to Schedule Bridge", use_container_width=True)
            
            if submit_log and field_text.strip():
                disc = None if discipline_hint == "Auto-Detect" else discipline_hint
                with st.spinner("Processing event through LLM extraction & embedding matcher..."):
                    result = pipeline.process_text_report(
                        raw_text=field_text.strip(),
                        reported_by=reporter_name,
                        discipline_hint=disc,
                        source_format="conversational",
                    )
                st.success(f"Processed report {result['report_id']} in {result['latency_ms']} ms!")
                if result.get("contradictions"):
                    st.error(f"🚨 {len(result['contradictions'])} Cross-Discipline Contradiction(s) Flagged! Check Review View.")
                st.rerun()

        st.markdown("### 📁 Batch Sample Ingestion")
        st.write("Quickly ingest pre-built sample files:")
        sample_col1, sample_col2, sample_col3 = st.columns(3)
        
        if sample_col1.button("📄 Civil Oct 3 Log", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_civil_oct03.txt"
            res = pipeline.process_file(str(p))
            st.success(f"Ingested Civil Log ({res['events_count']} events, {res['latency_ms']}ms)")
            st.rerun()
            
        if sample_col2.button("🚨 Elect Oct 5 (Clash)", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_daily_reports" / "report_electrical_oct05.txt"
            res = pipeline.process_file(str(p))
            st.warning(f"Ingested Electrical Log ({res['events_count']} events, {res['latency_ms']}ms)")
            st.rerun()

        if sample_col3.button("📊 Piping CSV Log", use_container_width=True):
            p = PROJECT_ROOT / "data" / "sample_spreadsheets" / "piping_fitup_weld_log.csv"
            res = pipeline.process_file(str(p))
            st.success(f"Ingested Spreadsheet ({res['events_count']} rows, {res['latency_ms']}ms)")
            st.rerun()

    with col_feed:
        st.markdown("### 📋 Recent Extracted Events & Auto-Matches")
        with db.get_connection() as conn:
            query = """
            SELECT ee.event_id, ee.activity_description, ee.discipline, ee.event_date, ee.action_type,
                   mr.candidate_activity_id, sa.name as matched_name, mr.confidence_score, mr.decision,
                   fr.reported_by, fr.timestamp_received
            FROM extracted_events ee
            JOIN field_reports fr ON ee.report_id = fr.report_id
            JOIN match_results mr ON ee.event_id = mr.event_id
            JOIN schedule_activities sa ON mr.candidate_activity_id = sa.activity_id
            ORDER BY fr.timestamp_received DESC, ee.event_id DESC
            LIMIT 15
            """
            feed_df = pd.read_sql_query(query, conn)

        if feed_df.empty:
            st.info("No field reports processed yet. Use the Time Agent or click a sample file on the left to start!")
        else:
            for _, row in feed_df.iterrows():
                badge = "🟢 Auto-Updated" if row["decision"] == "auto_updated" else "🟡 Review Queued"
                action_badge = f"[{row['action_type'].upper()}]"
                with st.container():
                    st.markdown(f"**{badge}** {action_badge} **`{row['discipline']}`** | *{row['reported_by']}* ({row['event_date']})")
                    st.write(f"📝 *Field Note:* {row['activity_description']}")
                    st.caption(f"🎯 **Matched:** `{row['candidate_activity_id']}` — {row['matched_name']} | **Confidence:** `{row['confidence_score']:.3f}`")
                    st.markdown("---")

# ==============================================================================
# VIEW 2: REVIEW + CONTRADICTIONS
# ==============================================================================
with tab_review:
    st.subheader("Human-in-the-Loop & Differentiator Action Center")
    st.write("Cross-discipline logical contradictions and low-confidence matches requiring planner judgment.")

    # Section A: Cross-Discipline Contradictions
    st.markdown("### 🚨 Detected Cross-Discipline Contradictions")
    contradiction_list = db.get_contradictions()
    if not contradiction_list:
        st.success("✅ No cross-discipline contradictions currently flagged.")
    else:
        for c in contradiction_list:
            st.error(
                f"**Conflict ID:** `{c['flag_id']}` | **Disciplines:** `{c['discipline_a']}` vs `{c['discipline_b']}`\n\n"
                f"**Activities involved:** `{c['activity_id_a']}` and `{c['activity_id_b']}`\n\n"
                f"**Clash Description:** {c['description']}\n\n"
                f"*Flagged at:* {c['created_at']} | *Status:* **{c['status'].upper()}**"
            )

    st.markdown("---")

    # Section B: Planner Review Queue
    st.markdown("### ⚖️ Planner Review Queue (Ambiguous Matches)")
    queue = db.get_review_queue()
    if not queue:
        st.success("✅ Review queue is empty. All processed reports met the high-confidence auto-update threshold.")
    else:
        st.write(f"Displaying **{len(queue)}** updates held for engineer review:")
        for idx, item in enumerate(queue):
            with st.expander(f"📌 Item {idx+1}: '{item['activity_description'][:60]}...' (Score: {item['confidence_score']:.2f})", expanded=(idx==0)):
                col_q1, col_q2 = st.columns([1.2, 1])
                with col_q1:
                    st.markdown(f"**Extracted Event Description:**\n> {item['activity_description']}")
                    st.write(f"- **Discipline:** `{item['extracted_discipline']}` | **Action:** `{item['action_type']}` | **Date:** `{item['event_date']}`")
                    st.write(f"- **Reported by:** {item['reported_by']}")
                    st.caption(f"- **Raw Report Context:** {item['raw_text']}")
                    
                    st.markdown("**Score Breakdown:**")
                    st.write(f"Semantic: `{item['semantic_score']:.2f}` | Discipline: `{item['discipline_score']:.2f}` | Date Proximity: `{item['date_score']:.2f}` => Total: `{item['confidence_score']:.3f}`")

                with col_q2:
                    st.markdown("**Top Candidate Matches:**")
                    top_candidates = json.loads(item.get("top_candidates") or "[]")
                    candidate_options = {}
                    for cand in top_candidates:
                        label = f"{cand['activity_id']}: {cand['name']} (Conf: {cand.get('confidence_score', 'N/A')})"
                        candidate_options[label] = cand["activity_id"]

                    # Also provide full activity list in case planner wants another activity
                    for act in activities:
                        label = f"{act['activity_id']}: {act['name']} [{act['discipline']}]"
                        if label not in candidate_options:
                            candidate_options[label] = act["activity_id"]

                    selected_label = st.selectbox(f"Select Verified Activity (#{idx+1})", list(candidate_options.keys()), key=f"sel_{item['match_id']}")
                    selected_act_id = candidate_options[selected_label]
                    planner_name = st.text_input(f"Planner Name (#{idx+1})", value="Planning Engineer", key=f"user_{item['match_id']}")
                    planner_notes = st.text_input(f"Resolution Notes (#{idx+1})", value="Manually verified and confirmed by planner", key=f"notes_{item['match_id']}")
                    
                    if st.button(f"✅ Approve & Update Schedule (#{idx+1})", key=f"btn_{item['match_id']}"):
                        success = db.resolve_review_item(
                            match_id=item["match_id"],
                            selected_activity_id=selected_act_id,
                            planner_name=planner_name,
                            notes=planner_notes,
                        )
                        if success:
                            st.success(f"Updated {selected_act_id} and recorded audit entry!")
                            st.rerun()

# ==============================================================================
# TAB 3: MASTER SCHEDULE & ANALYTICS
# ==============================================================================
with tab_schedule:
    st.subheader("Master Schedule Tracking & Discipline Analytics")
    st.caption("Live Primavera P6 / MS Project WBS L5/L6 Progress Tracking for Unit 3.")

    # Charts Row
    chart_c1, chart_c2 = st.columns([1.4, 1])

    with chart_c1:
        disc_summary = []
        for d in ["Civil", "Piping", "Electrical", "Instrumentation", "HSE"]:
            d_acts = [a for a in activities if a["discipline"] == d]
            c_cnt = sum(1 for a in d_acts if a["status"] == "COMPLETED")
            i_cnt = sum(1 for a in d_acts if a["status"] == "IN_PROGRESS")
            n_cnt = sum(1 for a in d_acts if a["status"] == "NOT_STARTED")
            disc_summary.append({"Discipline": d, "Status": "Completed", "Count": c_cnt})
            disc_summary.append({"Discipline": d, "Status": "In Progress", "Count": i_cnt})
            disc_summary.append({"Discipline": d, "Status": "Not Started", "Count": n_cnt})
        
        df_disc = pd.DataFrame(disc_summary)
        fig_bar = px.bar(
            df_disc,
            x="Discipline",
            y="Count",
            color="Status",
            title="Work Breakdown Progress by Engineering Discipline",
            color_discrete_map={"Completed": "#10b981", "In Progress": "#3b82f6", "Not Started": "#cbd5e1"},
            barmode="stack",
            height=300,
        )
        fig_bar.update_layout(margin=dict(l=10, r=10, t=35, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_c2:
        status_counts = {"Completed": completed_acts, "In Progress": in_progress_acts, "Not Started": not_started_acts}
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    hole=0.55,
                    marker=dict(colors=["#10b981", "#3b82f6", "#cbd5e1"]),
                )
            ]
        )
        fig_donut.update_layout(
            title_text="Project Completion Ratio",
            height=300,
            margin=dict(l=10, r=10, t=35, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # Interactive Master Schedule Table
    st.markdown("### 📋 Planned vs Actual Master Schedule")
    
    col_f1, col_f2, col_f3 = st.columns([1.2, 1, 1])
    with col_f1:
        search_query = st.text_input("🔍 Search Task Name, ID, or Area", value="")
    with col_f2:
        filter_disc = st.multiselect("Filter Discipline", ["Civil", "Piping", "Electrical", "Instrumentation", "HSE"], default=[])
    with col_f3:
        filter_status = st.multiselect("Filter Status", ["COMPLETED", "IN_PROGRESS", "NOT_STARTED"], default=[])

    table_rows = []
    for a in activities:
        if search_query:
            q = search_query.lower()
            if q not in a["name"].lower() and q not in a["activity_id"].lower() and q not in a["location"].lower():
                continue
        if filter_disc and a["discipline"] not in filter_disc:
            continue
        if filter_status and a["status"] not in filter_status:
            continue

        variance = "On Track"
        if a["status"] == "COMPLETED":
            variance = "Completed"
        elif a["status"] == "IN_PROGRESS" and a.get("actual_start"):
            if a["actual_start"] > a["planned_end"]:
                variance = "Delayed"

        table_rows.append({
            "Activity ID": a["activity_id"],
            "Task Name": a["name"],
            "Discipline": a["discipline"],
            "Location": a["location"],
            "Planned Start": a["planned_start"],
            "Planned End": a["planned_end"],
            "Actual Start": a["actual_start"] or "—",
            "Actual End": a["actual_end"] or "—",
            "Status": a["status"],
            "Variance": variance,
        })

    df_schedule = pd.DataFrame(table_rows)

    def highlight_status(val):
        if val == "COMPLETED":
            return "background-color: #d1fae5; color: #065f46; font-weight: bold;"
        elif val == "IN_PROGRESS":
            return "background-color: #dbeafe; color: #1e40af; font-weight: bold;"
        return "color: #64748b;"

    def highlight_variance(val):
        if val == "Completed":
            return "color: #065f46; font-weight: bold;"
        elif val == "Delayed":
            return "color: #b91c1c; font-weight: bold;"
        return "color: #1e293b;"

    if df_schedule.empty:
        st.warning("No activities match the selected filter criteria.")
    else:
        st.dataframe(
            df_schedule.style.map(highlight_status, subset=["Status"]).map(highlight_variance, subset=["Variance"]),
            use_container_width=True,
            hide_index=True,
            height=380,
        )

# ==============================================================================
# TAB 4: SEARCHABLE AUDIT TRAIL & MEMORY
# ==============================================================================
with tab_audit:
    st.subheader("Immutable Audit Trail & Institutional Memory")
    st.caption("Permanent, tamper-evident log of every automated AI decision and human planner override.")

    logs = db.get_audit_trail()
    
    if not logs:
        st.info("No audit transactions logged yet.")
    else:
        df_logs = pd.DataFrame(logs)
        
        col_a1, col_a2, col_a3 = st.columns([1, 1, 1.2])
        with col_a1:
            maker_filter = st.selectbox("Filter by Decision Maker", ["All"] + sorted(list(df_logs["decision_maker"].unique())))
        with col_a2:
            act_filter = st.selectbox("Filter by Activity ID", ["All"] + sorted(list(df_logs["activity_id"].unique())))
        with col_a3:
            csv_buf = io.StringIO()
            df_logs.to_csv(csv_buf, index=False)
            st.download_button(
                label="📥 Export Audit Trail (CSV for Primavera / PMIS)",
                data=csv_buf.getvalue(),
                file_name=f"audit_trail_oil_india_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        filtered_logs = df_logs.copy()
        if maker_filter != "All":
            filtered_logs = filtered_logs[filtered_logs["decision_maker"] == maker_filter]
        if act_filter != "All":
            filtered_logs = filtered_logs[filtered_logs["activity_id"] == act_filter]

        st.markdown(f"Displaying **{len(filtered_logs)}** immutable transaction records:")
        
        display_logs = filtered_logs[[
            "timestamp", "activity_id", "activity_name", "discipline", "decision_maker", "previous_value", "new_value", "notes"
        ]].copy()
        display_logs.columns = ["Timestamp", "Activity ID", "Task Name", "Discipline", "Decision Maker", "Previous State", "New State", "Audit Notes"]
        
        st.dataframe(display_logs, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🏛️ Institutional Memory Repository")
    st.write("Aggregated execution learnings for future capex estimating and duration benchmarking:")
    
    completed_items = [a for a in activities if a["status"] == "COMPLETED" and a.get("actual_start") and a.get("actual_end")]
    if not completed_items:
        st.info("Complete activities to populate cycle time durations for institutional memory.")
    else:
        memory_rows = []
        for item in completed_items:
            try:
                p_start = datetime.strptime(item["planned_start"][:10], "%Y-%m-%d")
                p_end = datetime.strptime(item["planned_end"][:10], "%Y-%m-%d")
                a_start = datetime.strptime(item["actual_start"][:10], "%Y-%m-%d")
                a_end = datetime.strptime(item["actual_end"][:10], "%Y-%m-%d")
                p_dur = (p_end - p_start).days
                a_dur = (a_end - a_start).days
                diff = a_dur - p_dur
            except Exception:
                p_dur, a_dur, diff = 0, 0, 0

            memory_rows.append({
                "Activity ID": item["activity_id"],
                "Task Name": item["name"],
                "Discipline": item["discipline"],
                "Planned Duration (Days)": p_dur,
                "Actual Duration (Days)": a_dur,
                "Duration Variance": f"{'+' if diff > 0 else ''}{diff} days",
                "Execution Performance": "On Schedule" if diff <= 0 else "Delayed",
            })
        
        st.dataframe(pd.DataFrame(memory_rows), use_container_width=True, hide_index=True)

