"""
Evaluation metrics for handwritten medical text recognition.

CRITICAL PROTOCOL:
Metrics (CER, WER, Exact Match) are calculated strictly on DECODED TEXT PREDICTIONS,
never on raw model logits.

Evaluation flow:
    model outputs/logits
            ↓
      token decoding
            ↓
   predicted transcription
            ↓
 compare against ground-truth
            ↓
     CER / WER / Exact Match

Raw metrics are computed directly without applying any medicine dictionaries or
fuzzy vocabulary correction.
"""

from typing import Dict, List, Sequence, Union


def levenshtein_distance(seq1: Sequence, seq2: Sequence) -> int:
    """Compute Levenshtein edit distance between two sequences (characters or words).

    Uses memory-efficient two-row dynamic programming algorithm O(min(N, M)) space.
    """
    if len(seq1) < len(seq2):
        return levenshtein_distance(seq2, seq1)

    if len(seq2) == 0:
        return len(seq1)

    previous_row = list(range(len(seq2) + 1))
    for i, c1 in enumerate(seq1):
        current_row = [i + 1] + [0] * len(seq2)
        for j, c2 in enumerate(seq2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row

    return previous_row[-1]


def character_error_rate(
    predictions: List[str],
    references: List[str],
) -> float:
    """Calculate Character Error Rate (CER) across decoded string predictions.

    CER = sum(LevenshteinDistance(pred_chars, ref_chars)) / sum(len(ref_chars))

    Args:
        predictions: List of decoded string transcriptions from the model.
        references: List of ground-truth reference string transcriptions.

    Returns:
        float: Character Error Rate (0.0 represents perfect accuracy).
    """
    if len(predictions) != len(references):
        raise ValueError(
            f"Predictions count ({len(predictions)}) does not match references count ({len(references)})"
        )

    if not predictions:
        return 0.0

    total_distance = 0
    total_chars = 0

    for pred, ref in zip(predictions, references):
        pred_str = str(pred or "")
        ref_str = str(ref or "")

        dist = levenshtein_distance(list(pred_str), list(ref_str))
        total_distance += dist
        total_chars += len(ref_str)

    if total_chars == 0:
        return 0.0 if total_distance == 0 else 1.0

    return round(total_distance / total_chars, 4)


def word_error_rate(
    predictions: List[str],
    references: List[str],
) -> float:
    """Calculate Word Error Rate (WER) across decoded string predictions.

    WER = sum(LevenshteinDistance(pred_words, ref_words)) / sum(len(ref_words))

    Args:
        predictions: List of decoded string transcriptions.
        references: List of ground-truth reference strings.

    Returns:
        float: Word Error Rate (0.0 represents perfect accuracy).
    """
    if len(predictions) != len(references):
        raise ValueError(
            f"Predictions count ({len(predictions)}) does not match references count ({len(references)})"
        )

    if not predictions:
        return 0.0

    total_distance = 0
    total_words = 0

    for pred, ref in zip(predictions, references):
        pred_words = str(pred or "").strip().split()
        ref_words = str(ref or "").strip().split()

        dist = levenshtein_distance(pred_words, ref_words)
        total_distance += dist
        total_words += len(ref_words)

    if total_words == 0:
        return 0.0 if total_distance == 0 else 1.0

    return round(total_distance / total_words, 4)


def exact_match_accuracy(
    predictions: List[str],
    references: List[str],
    case_sensitive: bool = False,
) -> float:
    """Calculate Exact Match (EM) accuracy across decoded string predictions.

    Args:
        predictions: List of decoded string transcriptions.
        references: List of ground-truth reference strings.
        case_sensitive: If False, performs case-insensitive comparison.

    Returns:
        float: Proportion of exact string matches (between 0.0 and 1.0).
    """
    if len(predictions) != len(references):
        raise ValueError(
            f"Predictions count ({len(predictions)}) does not match references count ({len(references)})"
        )

    if not predictions:
        return 0.0

    matches = 0
    for pred, ref in zip(predictions, references):
        p = str(pred or "").strip()
        r = str(ref or "").strip()

        if not case_sensitive:
            p = p.lower()
            r = r.lower()

        if p == r:
            matches += 1

    return round(matches / len(predictions), 4)


def compute_handwriting_metrics(
    predictions: List[str],
    references: List[str],
) -> Dict[str, Union[float, int]]:
    """Compute consolidated metrics suite on decoded string transcriptions.

    Calculates:
    - cer: Character Error Rate
    - wer: Word Error Rate
    - exact_match: Case-insensitive Exact Match accuracy
    - exact_match_case_sensitive: Case-sensitive Exact Match accuracy
    - total_samples: Number of evaluated pairs

    Note: These are raw metrics. No dictionary lookup or fuzzy correction has been applied.
    """
    return {
        "cer": character_error_rate(predictions, references),
        "wer": word_error_rate(predictions, references),
        "exact_match": exact_match_accuracy(predictions, references, case_sensitive=False),
        "exact_match_case_sensitive": exact_match_accuracy(predictions, references, case_sensitive=True),
        "total_samples": len(predictions),
    }
