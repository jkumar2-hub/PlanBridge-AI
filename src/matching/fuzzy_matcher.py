"""Fuzzy Matcher tying embedding engine and confidence scorer into candidate ranking."""
from typing import Any, Dict, List, Optional
from src.extraction.extractor_interface import ExtractedEvent
from src.matching.confidence_scorer import ConfidenceScorer
from src.matching.embedding_engine import EmbeddingEngine


class FuzzyMatcher:
    def __init__(self, embedding_engine: EmbeddingEngine, confidence_scorer: Optional[ConfidenceScorer] = None):
        self.engine = embedding_engine
        self.scorer = confidence_scorer or ConfidenceScorer()

    def match_event(self, event: ExtractedEvent, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.engine.activity_cache or len(self.engine.activity_cache) != len(activities):
            self.engine.index_activities(activities)

        semantic_scores = self.engine.compute_semantic_scores(event.activity_description)
        ranked_candidates = []

        for idx, act in enumerate(activities):
            sem_score = semantic_scores[idx] if idx < len(semantic_scores) else 0.0
            lex_score = self.engine.compute_lexical_score(event.activity_description, act["name"])
            disc_score = self.scorer.compute_discipline_score(event.discipline, act["discipline"])
            date_score = self.scorer.compute_date_proximity_score(event.event_date, act["planned_start"], act["planned_end"])

            scores = self.scorer.calculate_confidence(
                semantic_similarity=sem_score,
                lexical_similarity=lex_score,
                discipline_score=disc_score,
                date_proximity_score=date_score,
            )

            ranked_candidates.append({
                "activity_id": act["activity_id"],
                "name": act["name"],
                "discipline": act["discipline"],
                "location": act["location"],
                "planned_start": act["planned_start"],
                "planned_end": act["planned_end"],
                "semantic_score": scores["semantic_score"],
                "discipline_score": scores["discipline_score"],
                "date_score": scores["date_score"],
                "confidence_score": scores["confidence_score"],
                "decision": scores["decision"],
            })

        # Sort descending by confidence score
        ranked_candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
        best = ranked_candidates[0]
        top_3 = ranked_candidates[:3]

        return {
            "candidate_activity_id": best["activity_id"],
            "candidate_name": best["name"],
            "semantic_score": best["semantic_score"],
            "discipline_score": best["discipline_score"],
            "date_score": best["date_score"],
            "confidence_score": best["confidence_score"],
            "decision": best["decision"],
            "top_candidates": top_3,
        }
