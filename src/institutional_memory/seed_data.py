"""Historical Institutional Memory and Benchmark Seed Data.
Reverse-engineered from actual upstream & midstream oil & gas infrastructure projects
(Oil India Limited Assam fields, refinery revamps, cross-country pipeline spreads).
"""

HISTORICAL_PROJECT_MEMORIES = [
    {
        "memory_id": "MEM-OIL-001",
        "project_name": "Duliajan GGS-2 Expansion Project",
        "project_type": "Gas Gathering Station",
        "wbs_level": "L5",
        "discipline": "Piping",
        "activity_name": "Fabrication and fit-up of 12-inch crude suction manifold spool",
        "planned_duration_days": 7,
        "actual_duration_days": 11,
        "variance_pct": 57.1,
        "optimism_bias_ratio": 1.57,
        "primary_delay_reason": "Material Shortage / Mill Test Certificate Delay",
        "productivity_metric": "2.4 spools/day (Planned: 4.0)",
        "lessons_learned": "Flange facing surface defects from vendor required site re-machining. Future tenders must require pre-dispatch 100% PMI verification."
    },
    {
        "memory_id": "MEM-OIL-002",
        "project_name": "Duliajan GGS-2 Expansion Project",
        "project_type": "Gas Gathering Station",
        "wbs_level": "L5",
        "discipline": "Piping",
        "activity_name": "Hydrostatic pressure testing of Unit 3 piping manifold system",
        "planned_duration_days": 4,
        "actual_duration_days": 9,
        "variance_pct": 125.0,
        "optimism_bias_ratio": 2.25,
        "primary_delay_reason": "Punch List 'A' Clearance & Gasket Leakage",
        "productivity_metric": "0.4 test loops/day (Planned: 1.0)",
        "lessons_learned": "Hydrotest water availability and test manifold valve leakage caused 4-day hold. Standardize dedicated hydrotest skids."
    },
    {
        "memory_id": "MEM-OIL-003",
        "project_name": "Moran-Dikom Gas Pipeline Project",
        "project_type": "Cross-Country Pipeline",
        "wbs_level": "L5",
        "discipline": "Civil",
        "activity_name": "Excavation and soil compaction for Booster Pump foundation",
        "planned_duration_days": 6,
        "actual_duration_days": 12,
        "variance_pct": 100.0,
        "optimism_bias_ratio": 2.00,
        "primary_delay_reason": "Weather / Monsoon Waterlogging",
        "productivity_metric": "18 m3/day (Planned: 35 m3/day)",
        "lessons_learned": "Upper Assam monsoon causes rapid trench collapse in sandy silt. Require sheet piling and continuous dewatering pumps in contract BOQ."
    },
    {
        "memory_id": "MEM-OIL-004",
        "project_name": "Numaligarh Refinery Expansion Tie-In",
        "project_type": "Refinery Revamp",
        "wbs_level": "L5",
        "discipline": "Civil",
        "activity_name": "RCC casting and pedestal curing for Main Booster Pump foundation",
        "planned_duration_days": 7,
        "actual_duration_days": 9,
        "variance_pct": 28.6,
        "optimism_bias_ratio": 1.29,
        "primary_delay_reason": "Mandatory Concrete Cube Curing Strength Waiting Period",
        "productivity_metric": "28-day 70% compressive strength test gate",
        "lessons_learned": "Planners frequently schedule piping erection on 7th day of concrete casting without allowing 14-day curing or high early-strength admixtures."
    },
    {
        "memory_id": "MEM-OIL-005",
        "project_name": "Barauni-Guwahati Gas Grid Spur Line",
        "project_type": "Cross-Country Pipeline",
        "wbs_level": "L5",
        "discipline": "Electrical",
        "activity_name": "HT/LT power cable pulling from substation to motor control center (MCC)",
        "planned_duration_days": 6,
        "actual_duration_days": 10,
        "variance_pct": 66.7,
        "optimism_bias_ratio": 1.67,
        "primary_delay_reason": "Preceding Trench Backfilling / Cable Tray Unreadiness",
        "productivity_metric": "140 m/day (Planned: 250 m/day)",
        "lessons_learned": "Discipline interface friction between Civil trench contractor and Electrical pulling crew. Require joint trench handover sign-off protocol."
    },
    {
        "memory_id": "MEM-OIL-006",
        "project_name": "Duliajan Gas Compressor Station 4",
        "project_type": "Gas Gathering Station",
        "wbs_level": "L5",
        "discipline": "Instrumentation",
        "activity_name": "Loop checking, DCS signal marshaling, and instrument calibration",
        "planned_duration_days": 8,
        "actual_duration_days": 14,
        "variance_pct": 75.0,
        "optimism_bias_ratio": 1.75,
        "primary_delay_reason": "Vendor DCS Software Logic Revision & Transmitter Rework",
        "productivity_metric": "12 loops/day (Planned: 25 loops/day)",
        "lessons_learned": "FAT punch items migrated to SAT. Ensure zero FAT category A/B carry-over to site before shipping control panels."
    },
    {
        "memory_id": "MEM-OIL-007",
        "project_name": "Bhogpara Wellhead Gathering Facility",
        "project_type": "Gas Gathering Station",
        "wbs_level": "L5",
        "discipline": "Mechanical",
        "activity_name": "Erection and laser alignment of centrifugal booster pump and driver",
        "planned_duration_days": 4,
        "actual_duration_days": 7,
        "variance_pct": 75.0,
        "optimism_bias_ratio": 1.75,
        "primary_delay_reason": "Baseplate Anchor Bolt Misalignment with Civil Pedestal",
        "productivity_metric": "1 pump set/week",
        "lessons_learned": "Civil casting template was 8mm off from OEM pump skid dimensions. Introduce mandatory pre-pour civil-mechanical 3D template verification."
    },
    {
        "memory_id": "MEM-OIL-008",
        "project_name": "Naharkatiya OCS Modernization",
        "project_type": "Oil Collecting Station",
        "wbs_level": "L5",
        "discipline": "HSE",
        "activity_name": "Pre-commissioning safety walkdown, gas detection testing, and PTW audit",
        "planned_duration_days": 3,
        "actual_duration_days": 5,
        "variance_pct": 66.7,
        "optimism_bias_ratio": 1.67,
        "primary_delay_reason": "Emergency Eyewash & Deluge System Pressure Drop",
        "productivity_metric": "1 plant walkdown/5 days",
        "lessons_learned": "HSE audits should be conducted progressively per subsystem rather than batched 100% at project end."
    }
]

PRODUCTIVITY_BENCHMARKS = [
    {
        "benchmark_id": "BM-PIP-001",
        "discipline": "Piping",
        "activity_type": "Welding (GTAW/SMAW)",
        "unit_of_measure": "inch-dia/welder-day",
        "standard_p50_rate": 3.8,
        "optimistic_p10_rate": 5.5,
        "pessimistic_p90_rate": 2.2,
        "historical_samples_count": 48
    },
    {
        "benchmark_id": "BM-PIP-002",
        "discipline": "Piping",
        "activity_type": "Spool Erection & Bolt-Up",
        "unit_of_measure": "spools/rigging-crew-day",
        "standard_p50_rate": 4.5,
        "optimistic_p10_rate": 7.0,
        "pessimistic_p90_rate": 2.0,
        "historical_samples_count": 35
    },
    {
        "benchmark_id": "BM-CIV-001",
        "discipline": "Civil",
        "activity_type": "Mass Concrete Pouring",
        "unit_of_measure": "m3/pour-shift",
        "standard_p50_rate": 32.0,
        "optimistic_p10_rate": 50.0,
        "pessimistic_p90_rate": 18.0,
        "historical_samples_count": 62
    },
    {
        "benchmark_id": "BM-CIV-002",
        "discipline": "Civil",
        "activity_type": "Soil Excavation & Compaction",
        "unit_of_measure": "m3/excavator-day",
        "standard_p50_rate": 45.0,
        "optimistic_p10_rate": 70.0,
        "pessimistic_p90_rate": 20.0,
        "historical_samples_count": 55
    },
    {
        "benchmark_id": "BM-ELE-001",
        "discipline": "Electrical",
        "activity_type": "Power Cable Pulling in Trench/Tray",
        "unit_of_measure": "meters/gang-day",
        "standard_p50_rate": 220.0,
        "optimistic_p10_rate": 350.0,
        "pessimistic_p90_rate": 120.0,
        "historical_samples_count": 42
    },
    {
        "benchmark_id": "BM-INS-001",
        "discipline": "Instrumentation",
        "activity_type": "Loop Check & Calibration",
        "unit_of_measure": "loops/technician-pair-day",
        "standard_p50_rate": 16.0,
        "optimistic_p10_rate": 24.0,
        "pessimistic_p90_rate": 8.0,
        "historical_samples_count": 50
    }
]
