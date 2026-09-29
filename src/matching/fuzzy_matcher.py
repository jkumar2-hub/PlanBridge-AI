"""Fuzzy Matcher tying embedding engine, terminology disambiguator, and confidence scorer into candidate ranking."""
from typing import Any, Dict, List, Optional
from src.extraction.extractor_interface import ExtractedEvent
from src.matching.confidence_scorer import ConfidenceScorer
from src.matching.embedding_engine import EmbeddingEngine
from src.matching.terminology_dictionary import TerminologyDisambiguator


class FuzzyMatcher:
    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        confidence_scorer: Optional[ConfidenceScorer] = None,
        disambiguator: Optional[TerminologyDisambiguator] = None,
    ):
        self.engine = embedding_engine
        self.scorer = confidence_scorer or ConfidenceScorer()
        self.disambiguator = disambiguator or TerminologyDisambiguator()

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

            # Terminology boost for domain-specific contractor jargon
            term_boost = self.disambiguator.compute_terminology_boost(
                f"{event.activity_description} {event.raw_snippet or ''}", 
                act["name"]
            )

            # Combined semantic + terminology boost
            boosted_sem = min(1.0, sem_score + term_boost)

            scores = self.scorer.calculate_confidence(
                semantic_similarity=boosted_sem,
                lexical_similarity=lex_score,
                discipline_score=disc_score,
                date_proximity_score=date_score,
            )

            # Decision: auto_updated, queued_for_review, or unmatched_new
            conf = scores["confidence_score"]
            if conf >= 0.70 and disc_score >= 0.4:
                decision = "auto_updated"
            elif conf >= 0.40:
                decision = "queued_for_review"
            else:
                decision = "unmatched_new"

            ranked_candidates.append({
                "activity_id": act["activity_id"],
                "wbs_code": act.get("wbs_code", "L5"),
                "name": act["name"],
                "discipline": act["discipline"],
                "location": act["location"],
                "planned_start": act["planned_start"],
                "planned_end": act["planned_end"],
                "semantic_score": scores["semantic_score"],
                "discipline_score": scores["discipline_score"],
                "terminology_score": round(term_boost, 2),
                "date_score": scores["date_score"],
                "confidence_score": conf,
                "decision": decision,
            })

        # Sort descending by confidence score
        ranked_candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
        best = ranked_candidates[0]
        top_3 = ranked_candidates[:3]

        final_decision = best["decision"]
        if best["confidence_score"] < 0.40:
            final_decision = "unmatched_new"

        return {
            "candidate_activity_id": best["activity_id"],
            "candidate_wbs": best.get("wbs_code", "L5"),
            "candidate_name": best["name"],
            "semantic_score": best["semantic_score"],
            "discipline_score": best["discipline_score"],
            "terminology_score": best["terminology_score"],
            "date_score": best["date_score"],
            "confidence_score": best["confidence_score"],
            "decision": final_decision,
            "top_candidates": top_3,
        }
