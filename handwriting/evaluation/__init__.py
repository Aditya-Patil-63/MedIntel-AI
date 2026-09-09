"""
Handwriting Recognition Evaluation Module.

MedIntel AI — Phase 5.
"""

from handwriting.evaluation.evaluate import HandwritingEvaluator
from handwriting.evaluation.metrics import (
    character_error_rate,
    compute_handwriting_metrics,
    exact_match_accuracy,
    levenshtein_distance,
    word_error_rate,
)

__all__ = [
    "levenshtein_distance",
    "character_error_rate",
    "word_error_rate",
    "exact_match_accuracy",
    "compute_handwriting_metrics",
    "HandwritingEvaluator",
]
