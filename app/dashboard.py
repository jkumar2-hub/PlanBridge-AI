"""Streamlit Dashboard for SIH PS 26122 - Planning-to-Execution Bridge.
Three core views:
1. Live Feed & Time Agent (Conversational site updates & batch ingestion)
2. Review + Contradictions (Planner decision center & cross-discipline clashes)
3. Schedule Tracking & Audit Trail (Planned vs Actual status & immutable logs)
"""
import os
import sys
import json
from pathlib import Path
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BASELINE_SCHEDULE_PATH, CONFIDENCE_THRESHOLD, DB_PATH
from src.database.db_manager import DatabaseManager
from src.pipeline import Pipeline

st.set_page_config(
    page_title="Oil India Limited - Schedule-Linking Layer",
    page_icon="🏗️",
    layout="wide",
)

@st.cache_resource
def get_pipeline():
    return Pipeline(db_path=str(DB_PATH))

pipeline = get_pipeline()
db = pipeline.db

# Header
st.title("🏗️ Oil India Limited — Intelligent Schedule-Linking Bridge")
st.caption("SIH PS 26122: Real-Time Actual Progress Tracking | Planning-to-Execution Bridge")

# Top Metrics Row
activities = db.get_all_activities()
total_acts = len(activities)
completed_acts = sum(1 for a in activities if a.get("status") == "COMPLETED")
in_progress_acts = sum(1 for a in activities if a.get("status") == "IN_PROGRESS")
review_items = db.get_review_queue()
contradictions = db.get_contradictions()

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("Total Activities", total_acts)
col_m2.metric("Completed", completed_acts)
col_m3.metric("In Progress", in_progress_acts)
col_m4.metric("Review Queue", len(review_items), delta=f"{len(review_items)} pending", delta_color="inverse")
col_m5.metric("Contradictions", len(contradictions), delta=f"{len(contradictions)} flagged", delta_color="inverse")

st.markdown("---")

# Navigation Tabs (Strictly 3 Views as defined in plan)
tab_live, tab_review, tab_audit = st.tabs([
    "📡 1. Live Feed & Time Agent",
    "⚠️ 2. Review + Contradictions",
    "📊 3. Schedule Tracking & Audit Trail",
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
# VIEW 3: SCHEDULE TRACKING & AUDIT TRAIL
# ==============================================================================
with tab_audit:
    st.subheader("Master Schedule Status & Immutable Audit Log")
    
    st.markdown("### 📅 Planned vs Actual Master Schedule")
    acts = db.get_all_activities()
    table_data = []
    for a in acts:
        table_data.append({
            "Activity ID": a["activity_id"],
            "Task Name": a["name"],
            "Discipline": a["discipline"],
            "Location": a["location"],
            "Planned Start": a["planned_start"],
            "Planned End": a["planned_end"],
            "Actual Start": a["actual_start"] or "—",
            "Actual End": a["actual_end"] or "—",
            "Status": a["status"],
        })
    df_acts = pd.DataFrame(table_data)

    def style_status(val):
        if val == "COMPLETED":
            return "background-color: #d4edda; color: #155724; font-weight: bold;"
        elif val == "IN_PROGRESS":
            return "background-color: #cce5ff; color: #004085; font-weight: bold;"
        return "color: #6c757d;"

    st.dataframe(
        df_acts.style.map(style_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("### 📜 Immutable Audit Trail")
    st.write("Every automatic system update and manual planner override is permanently logged:")
    
    logs = db.get_audit_trail()
    if not logs:
        st.info("No audit entries recorded yet.")
    else:
        audit_rows = []
        for l in logs:
            audit_rows.append({
                "Timestamp": l["timestamp"],
                "Activity ID": l["activity_id"],
                "Activity Name": l.get("activity_name", ""),
                "Decision Maker": l["decision_maker"],
                "Previous Value": l["previous_value"],
                "New Value": l["new_value"],
                "Notes / Rationale": l["notes"],
            })
        df_audit = pd.DataFrame(audit_rows)
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
