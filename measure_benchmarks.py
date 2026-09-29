"""Benchmark & Measurement Script for Step 5 Checkpoint.
Measures latency, extrapolates LLM API costs, and evaluates match accuracy against ground-truth labels.
"""
import json
import os
import sys
import time
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import Pipeline

# Hand-labeled Ground Truth for synthetic benchmark set
GROUND_TRUTH = {
    "report_civil_oct03.txt": {
        "primary_expected_activity": "L5-CIV-102",
        "expected_action": "completed",
        "expected_discipline": "Civil",
        "expected_decision": "auto_updated",
    },
    "report_electrical_oct05.txt": {
        "primary_expected_activity": "L5-ELE-301",
        "expected_action": "blocked",
        "expected_discipline": "Electrical",
        "expected_decision": "auto_updated",
    },
    "report_piping_oct04.txt": {
        "primary_expected_activity": "L5-PIP-201",
        "expected_action": "completed",
        "expected_discipline": "Piping",
        "expected_decision": "auto_updated",
    },
    "report_instrumentation_oct06.txt": {
        "primary_expected_activity": "L5-INS-402",
        "expected_action": "completed",
        "expected_discipline": "Instrumentation",
        "expected_decision": "auto_updated",
    },
    "report_hse_oct02.txt": {
        "primary_expected_activity": "L5-HSE-501",
        "expected_action": "completed",
        "expected_discipline": "HSE",
        "expected_decision": "auto_updated",
    },
    "report_civil_lowconf_oct07.txt": {
        "primary_expected_activity": "L5-CIV-105",
        "expected_action": "in-progress",
        "expected_discipline": "Civil",
        "expected_decision": "queued_for_review",
    },
}


def run_benchmark():
    db_file = str(PROJECT_ROOT / "data" / "benchmark_run.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    pipeline = Pipeline(db_path=db_file)
    reports_dir = PROJECT_ROOT / "data" / "sample_daily_reports"

    latencies = []
    correct_matches = 0
    correct_decisions = 0
    total_reports = len(GROUND_TRUTH)

    print("==================================================================")
    print("STEP 5: MEASUREMENT PASS (LATENCY, COST, ACCURACY)")
    print("==================================================================")

    for filename, truth in GROUND_TRUTH.items():
        file_path = str(reports_dir / filename)
        start = time.perf_counter()
        res = pipeline.process_file(file_path)
        lat = (time.perf_counter() - start) * 1000
        latencies.append(lat)

        # Check accuracy against primary expected match
        matched_acts = [r["match"]["candidate_activity_id"] for r in res["results"]]
        decisions = [r["match"]["decision"] for r in res["results"]]

        act_match = truth["primary_expected_activity"] in matched_acts
        dec_match = truth["expected_decision"] in decisions

        if act_match:
            correct_matches += 1
        if dec_match:
            correct_decisions += 1

        print(f"[{filename}] Latency: {lat:.1f}ms | Primary Match: {truth['primary_expected_activity']} ({'PASS' if act_match else 'FAIL'}) | Decision: {truth['expected_decision']} ({'PASS' if dec_match else 'FAIL'})")

    avg_latency = float(np.mean(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    min_latency = float(np.min(latencies))
    max_latency = float(np.max(latencies))
    match_accuracy = (correct_matches / total_reports) * 100.0
    decision_accuracy = (correct_decisions / total_reports) * 100.0

    # Cost Model Extrapolation
    # Average tokens per report based on schema:
    # System prompt: ~250 tokens, User prompt (report text): ~150 tokens = ~400 input tokens
    # Output JSON payload: ~100 tokens
    prompt_tokens_per_report = 400
    completion_tokens_per_report = 100
    
    # Gemini 1.5 Flash Pricing: $0.075 / 1M input, $0.30 / 1M output
    cost_input_gemini = (prompt_tokens_per_report / 1_000_000) * 0.075
    cost_output_gemini = (completion_tokens_per_report / 1_000_000) * 0.30
    cost_per_report_gemini = cost_input_gemini + cost_output_gemini

    # GPT-4o-mini Pricing: $0.15 / 1M input, $0.60 / 1M output
    cost_input_openai = (prompt_tokens_per_report / 1_000_000) * 0.15
    cost_output_openai = (completion_tokens_per_report / 1_000_000) * 0.60
    cost_per_report_openai = cost_input_openai + cost_output_openai

    # Volume extrapolation:
    # Typical Oil India infrastructure build: 35 daily logs / updates per day across disciplines
    daily_volume = 35
    monthly_volume = daily_volume * 30
    monthly_cost_gemini = monthly_volume * cost_per_report_gemini
    monthly_cost_openai = monthly_volume * cost_per_report_openai

    print("\n------------------------------------------------------------------")
    print("RECORDED MEASUREMENTS:")
    print("------------------------------------------------------------------")
    print(f"1. LATENCY (Ingestion -> Extraction -> Match -> Contradiction -> DB):")
    print(f"   - Average: {avg_latency:.2f} ms")
    print(f"   - P95:     {p95_latency:.2f} ms")
    print(f"   - Range:   {min_latency:.2f} ms - {max_latency:.2f} ms")
    print(f"\n2. MATCH & DECISION ACCURACY (Hand-Labeled Benchmark):")
    print(f"   - Target Activity Match Accuracy: {match_accuracy:.1f}% ({correct_matches}/{total_reports})")
    print(f"   - Threshold Decision Accuracy:   {decision_accuracy:.1f}% ({correct_decisions}/{total_reports})")
    print(f"\n3. COST EXTRAPOLATION (Based on 35 reports/day, 1,050 reports/month):")
    print(f"   - Gemini 1.5 Flash Cost per report: ${cost_per_report_gemini:.6f}")
    print(f"   - Gemini 1.5 Flash Monthly Cost:    ${monthly_cost_gemini:.4f} / month")
    print(f"   - GPT-4o-mini Cost per report:      ${cost_per_report_openai:.6f}")
    print(f"   - GPT-4o-mini Monthly Cost:         ${monthly_cost_openai:.4f} / month")
    print("==================================================================")

    results_dict = {
        "latency": {
            "avg_ms": round(avg_latency, 2),
            "p95_ms": round(p95_latency, 2),
            "min_ms": round(min_latency, 2),
            "max_ms": round(max_latency, 2),
        },
        "accuracy": {
            "match_accuracy_pct": round(match_accuracy, 1),
            "decision_accuracy_pct": round(decision_accuracy, 1),
            "total_benchmark_reports": total_reports,
        },
        "cost": {
            "tokens_per_report": prompt_tokens_per_report + completion_tokens_per_report,
            "cost_per_report_gemini_usd": round(cost_per_report_gemini, 6),
            "monthly_cost_gemini_usd": round(monthly_cost_gemini, 4),
            "cost_per_report_openai_usd": round(cost_per_report_openai, 6),
            "monthly_cost_openai_usd": round(monthly_cost_openai, 4),
            "assumed_daily_volume": daily_volume,
        },
    }

    with open(PROJECT_ROOT / "data" / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2)

if __name__ == "__main__":
    run_benchmark()
