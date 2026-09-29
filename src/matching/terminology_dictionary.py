"""Engineering Terminology Disambiguation Dictionary & Granularity Resolver.
Maps field vernacular, colloquial contractor jargon, and micro-activity phrasing
to formal Primavera P6 / MS Project L5/L6 engineering WBS descriptions.
"""

import re
from typing import Dict, List, Tuple

# Domain Synonym Maps: Field Jargon -> Standard Baseline Concepts
TERMINOLOGY_SYNONYMS = {
    # Piping & Welding
    "spool erected": ["erect spool", "pipe lifted", "spool placed", "line erected", "spool installation", "manifold erection"],
    "fit-up": ["fitup", "tack weld", "joint alignment", "flange match", "pipe fitting", "bevelling"],
    "butt welding": ["gtaw", "smaw", "tig weld", "root run", "capping", "joint welded", "golden weld", "welder", "welds"],
    "hydrostatic pressure testing": ["hydrotest", "pressure test", "test pack", "leak test", "loop test", "punch a", "punch b"],
    "radiography": ["rt test", "ndt", "x-ray", "ultrasonic test", "ut test", "dye penetrant", "dpt"],

    # Civil & Structural
    "excavation and soil compaction": ["khudai", "digging", "earthwork", "trenching", "compaction", "soil test", "pit excavation", "dewatering"],
    "rcc casting and pedestal curing": ["concrete pour", "rcc casting", "pedestal pour", "shuttering", "rebar tying", "curing", "concrete placed", "casting done"],
    "grouting and anchor bolt": ["anchor bolt fixing", "soleplate grouting", "baseplate grouting", "pocket grouting", "non-shrink grout"],
    "structural pipe rack column": ["pipe rack foundation", "rack pedestal", "structural steel", "bay 1-3", "column base"],
    "drain trench": ["drainage trench", "precast slab", "storm water drain", "culvert"],

    # Electrical
    "power cable pulling": ["cable pulling", "cable laying", "cable pull", "tray laying", "cable hauling", "megger test"],
    "motor control center": ["mcc panel", "switchgear", "substation", "breaker", "busbar", "ht lt panel"],
    "transformer installation": ["transformer placement", "oil filtration", "bushing test", "transformer radiator"],
    "earthing grid": ["grounding pit", "earthing strip", "earth electrode", "resistance test"],

    # Instrumentation
    "loop checking": ["cold loop", "hot loop", "dcs check", "signal check", "scada link", "marshaling", "continuity"],
    "transmitter calibration": ["pressure transmitter", "temperature sensor", "flow meter", "calibration bench", "zero span"],
    "control valve testing": ["stroke check", "positioner calibration", "actuator test", "air tubing"],

    # Mechanical
    "booster pump erection": ["pump placement", "pump skid", "centrifugal pump", "motor base", "skid mounting"],
    "laser alignment": ["shaft alignment", "dial gauge check", "coupling alignment", "runout check", "soft foot check"],

    # HSE
    "safety walkdown": ["pre-commissioning walkdown", "safety inspection", "gas detection", "ptw audit", "fire water test"]
}


class TerminologyDisambiguator:
    def __init__(self):
        pass

    def compute_terminology_boost(self, field_text: str, planned_activity_name: str) -> float:
        """Computes a semantic boost if field jargon matches known synonyms of the planned activity."""
        f_lower = field_text.lower()
        p_lower = planned_activity_name.lower()
        boost = 0.0

        for standard_concept, synonyms in TERMINOLOGY_SYNONYMS.items():
            # Check if planned activity embodies this concept
            std_in_plan = any(token in p_lower for token in standard_concept.split())
            if std_in_plan:
                # Check if field text uses any known contractor jargon/synonym
                for syn in synonyms:
                    if syn in f_lower:
                        boost = max(boost, 0.35)
                        break

        return boost

    def resolve_granularity_rollup(self, micro_quantity: float, planned_total_quantity: float) -> Tuple[float, str]:
        """Resolves 1-to-many micro execution events into percentage completion of the L5/L6 node."""
        if planned_total_quantity <= 0:
            return 0.0, "unknown"
        pct = min(100.0, (micro_quantity / planned_total_quantity) * 100.0)
        status = "COMPLETED" if pct >= 99.5 else "IN_PROGRESS"
        return round(pct, 1), status
