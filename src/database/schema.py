"""Database schema definitions for SQLite."""
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schedule_activities (
    activity_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    discipline TEXT NOT NULL,
    planned_start TEXT NOT NULL,
    planned_end TEXT NOT NULL,
    location TEXT NOT NULL,
    actual_start TEXT,
    actual_end TEXT,
    status TEXT DEFAULT 'NOT_STARTED',
    dependency_ids TEXT
);

CREATE TABLE IF NOT EXISTS field_reports (
    report_id TEXT PRIMARY KEY,
    source_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    discipline_hint TEXT,
    reported_by TEXT,
    timestamp_received TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extracted_events (
    event_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    activity_description TEXT NOT NULL,
    discipline TEXT,
    event_date TEXT,
    action_type TEXT NOT NULL,
    location TEXT,
    FOREIGN KEY(report_id) REFERENCES field_reports(report_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    match_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    candidate_activity_id TEXT NOT NULL,
    semantic_score REAL NOT NULL,
    discipline_score REAL NOT NULL,
    date_score REAL NOT NULL,
    confidence_score REAL NOT NULL,
    decision TEXT NOT NULL,
    top_candidates TEXT,
    FOREIGN KEY(event_id) REFERENCES extracted_events(event_id),
    FOREIGN KEY(candidate_activity_id) REFERENCES schedule_activities(activity_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    match_id TEXT,
    activity_id TEXT NOT NULL,
    decision_maker TEXT NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    timestamp TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY(activity_id) REFERENCES schedule_activities(activity_id)
);

CREATE TABLE IF NOT EXISTS contradiction_flags (
    flag_id TEXT PRIMARY KEY,
    activity_id_a TEXT NOT NULL,
    activity_id_b TEXT NOT NULL,
    discipline_a TEXT NOT NULL,
    discipline_b TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL
);
"""
