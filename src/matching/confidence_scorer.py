"""Confidence Scorer combining semantic similarity, discipline matching, and date proximity."""
from datetime import datetime
from typing import Any, Dict, Optional
from src.config import CONFIDENCE_THRESHOLD, WEIGHT_DATE, WEIGHT_DISCIPLINE, WEIGHT_SEMANTIC


class ConfidenceScorer:
    def __init__(
        self,
        weight_semantic: float = WEIGHT_SEMANTIC,
        weight_discipline: float = WEIGHT_DISCIPLINE,
        weight_date: float = WEIGHT_DATE,
        threshold: float = CONFIDENCE_THRESHOLD,
    ):
        self.w_semantic = weight_semantic
        self.w_discipline = weight_discipline
        self.w_date = weight_date
        self.threshold = threshold

    def compute_discipline_score(self, extracted_discipline: Optional[str], candidate_discipline: str) -> float:
        if not extracted_discipline or extracted_discipline.lower() in ("general", "unknown"):
            return 0.5
        if extracted_discipline.lower() == candidate_discipline.lower():
            return 1.0
        # Complementary cross-discipline interaction allowance
        compatible_pairs = [("civil", "hse"), ("piping", "hse"), ("electrical", "instrumentation")]
        pair = (extracted_discipline.lower(), candidate_discipline.lower())
        if pair in compatible_pairs or (pair[1], pair[0]) in compatible_pairs:
            return 0.4
        return 0.0

    def compute_date_proximity_score(self, event_date_str: Optional[str], planned_start_str: str, planned_end_str: str) -> float:
        if not event_date_str:
            return 0.5
        try:
            evt_dt = datetime.strptime(event_date_str[:10], "%Y-%m-%d")
            p_start = datetime.strptime(planned_start_str[:10], "%Y-%m-%d")
            p_end = datetime.strptime(planned_end_str[:10], "%Y-%m-%d")
        except Exception:
            return 0.5

        # If inside planned window (with 3-day lead and 5-day lag buffer), full score
        if p_start <= evt_dt <= p_end:
            return 1.0

        diff_days = 0
        if evt_dt < p_start:
            diff_days = (p_start - evt_dt).days
        else:
            diff_days = (evt_dt - p_end).days

        if diff_days <= 3:
            return 0.9
        elif diff_days <= 7:
            return 0.7
        elif diff_days <= 14:
            return 0.4
        return 0.1

    def calculate_confidence(
        self,
        semantic_similarity: float,
        lexical_similarity: float,
        discipline_score: float,
        date_proximity_score: float,
    ) -> Dict[str, Any]:
        # Blended semantic + lexical score (80% embedding, 20% lexical)
        blended_semantic = (0.8 * semantic_similarity) + (0.2 * lexical_similarity)
        
        confidence = (
            (self.w_semantic * blended_semantic)
            + (self.w_discipline * discipline_score)
            + (self.w_date * date_proximity_score)
        )
        confidence = max(0.0, min(1.0, confidence))

        decision = "auto_updated" if confidence >= self.threshold else "queued_for_review"

        return {
            "semantic_score": round(blended_semantic, 4),
            "discipline_score": round(discipline_score, 4),
            "date_score": round(date_proximity_score, 4),
            "confidence_score": round(confidence, 4),
            "decision": decision,
        }
