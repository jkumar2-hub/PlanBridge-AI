"""Database schema definitions for PlanBridge AI SQLite database.
Includes full L1-L6 WBS support, EVM fields, cryptographic audit hash-chaining,
cross-discipline physics contradiction flags, and institutional memory repository.
"""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schedule_activities (
    activity_id TEXT PRIMARY KEY,
    wbs_code TEXT DEFAULT '1.0',
    name TEXT NOT NULL,
    discipline TEXT NOT NULL,
    planned_start TEXT NOT NULL,
    planned_end TEXT NOT NULL,
    planned_duration INTEGER DEFAULT 0,
    location TEXT NOT NULL,
    weightage REAL DEFAULT 1.0,
    planned_cost REAL DEFAULT 10000.0,
    actual_cost REAL DEFAULT 0.0,
    actual_start TEXT,
    actual_end TEXT,
    status TEXT DEFAULT 'NOT_STARTED',
    percent_complete REAL DEFAULT 0.0,
    dependency_ids TEXT DEFAULT '[]',
    unit_of_measure TEXT DEFAULT 'units',
    planned_quantity REAL DEFAULT 100.0,
    actual_quantity REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS field_reports (
    report_id TEXT PRIMARY KEY,
    source_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    discipline_hint TEXT,
    reported_by TEXT,
    location TEXT,
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
    quantity_done REAL DEFAULT 0.0,
    crew_size INTEGER DEFAULT 0,
    delay_reason TEXT,
    raw_snippet TEXT,
    FOREIGN KEY(report_id) REFERENCES field_reports(report_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    match_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    candidate_activity_id TEXT NOT NULL,
    semantic_score REAL NOT NULL,
    discipline_score REAL NOT NULL,
    terminology_score REAL DEFAULT 0.0,
    date_score REAL NOT NULL,
    confidence_score REAL NOT NULL,
    decision TEXT NOT NULL,
    top_candidates TEXT,
    planner_status TEXT DEFAULT 'approved',
    planner_notes TEXT,
    FOREIGN KEY(event_id) REFERENCES extracted_events(event_id),
    FOREIGN KEY(candidate_activity_id) REFERENCES schedule_activities(activity_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    match_id TEXT,
    activity_id TEXT NOT NULL,
    decision_maker TEXT NOT NULL,
    action TEXT DEFAULT 'UPDATE',
    previous_value TEXT,
    new_value TEXT,
    timestamp TEXT NOT NULL,
    notes TEXT,
    sha256_hash TEXT,
    prev_hash TEXT,
    FOREIGN KEY(activity_id) REFERENCES schedule_activities(activity_id)
);

CREATE TABLE IF NOT EXISTS contradiction_flags (
    flag_id TEXT PRIMARY KEY,
    activity_id_a TEXT NOT NULL,
    activity_id_b TEXT NOT NULL,
    discipline_a TEXT NOT NULL,
    discipline_b TEXT NOT NULL,
    contradiction_type TEXT DEFAULT 'physical_precedence_violation',
    severity TEXT DEFAULT 'HIGH',
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolution_notes TEXT
);

CREATE TABLE IF NOT EXISTS institutional_memory (
    memory_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    wbs_level TEXT DEFAULT 'L5',
    discipline TEXT NOT NULL,
    activity_name TEXT NOT NULL,
    planned_duration_days INTEGER NOT NULL,
    actual_duration_days INTEGER NOT NULL,
    variance_pct REAL NOT NULL,
    optimism_bias_ratio REAL NOT NULL,
    primary_delay_reason TEXT,
    productivity_metric TEXT,
    lessons_learned TEXT
);

CREATE TABLE IF NOT EXISTS productivity_benchmarks (
    benchmark_id TEXT PRIMARY KEY,
    discipline TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    unit_of_measure TEXT NOT NULL,
    standard_p50_rate REAL NOT NULL,
    optimistic_p10_rate REAL NOT NULL,
    pessimistic_p90_rate REAL NOT NULL,
    historical_samples_count INTEGER DEFAULT 10
);
"""
