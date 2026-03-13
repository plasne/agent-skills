"""
Demo evaluation module for the AML Evaluation Runner.

Implements the run_eval contract expected by the runner:
    def run_eval(payload_json: dict) -> dict

This module computes lightweight, deterministic metrics using **only the
Python standard library** — no OpenAI calls, no azure-ai-evaluation, and
no heavy ML packages.

Input shape (written by the inference step):
    {
        "ground_truth": {
            "id": "...",
            "question": "...",
            "answer": "expected answer",
            "refs": [...],
            "tags": [...],
            "history": [...]
        },
        "inference": {
            "response": "model answer",
            "time_taken_in_ms": 12.3,
            "usage": {"input_tokens": 10, "output_tokens": 20, "model": "..."},
            "function_calls": [...],
            ...
        }
    }

Output shape:
    {
        "$metrics": {
            "answer_similarity": 0.85,
            "answer_length_ratio": 0.92,
            "word_overlap_f1": 0.78,
            "has_answer": 1,
            "meta_inference_time_ms": 12.3,
            "meta_prompt_tokens": 10,
            "meta_completion_tokens": 20
        }
    }
"""

import difflib
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def run_eval(payload_json: dict) -> dict:
    """
    Evaluate a single inference result against its ground truth.

    Args:
        payload_json: Combined ground truth + inference payload.

    Returns:
        A dict with a ``$metrics`` key containing all computed scores.
    """
    ground_truth = payload_json.get("ground_truth", {})
    inference = payload_json.get("inference", {})

    # Resolve fields --------------------------------------------------------
    question = (
        ground_truth.get("question")
        or ground_truth.get("editedQuestion")
        or ground_truth.get("synthQuestion")
        or ""
    )
    expected_answer = ground_truth.get("answer", "")
    actual_answer = inference.get("response", "")
    gt_id = ground_truth.get("id", "unknown")

    # Metrics ---------------------------------------------------------------
    metrics: dict[str, Any] = {}

    # 1. Sequence-matcher similarity (0-1, stdlib difflib)
    metrics["answer_similarity"] = _sequence_similarity(expected_answer, actual_answer)

    # 2. Word-overlap F1
    metrics["word_overlap_f1"] = _word_overlap_f1(expected_answer, actual_answer)

    # 3. Answer length ratio (|actual| / |expected|, capped at 2.0)
    metrics["answer_length_ratio"] = _length_ratio(expected_answer, actual_answer)

    # 4. Binary: did inference produce a non-empty answer?
    metrics["has_answer"] = 1 if actual_answer.strip() else 0

    # 5. Meta: inference latency
    metrics["meta_inference_time_ms"] = inference.get("time_taken_in_ms", 0.0)

    # 6. Meta: token counts
    usage = inference.get("usage", {})
    metrics["meta_prompt_tokens"] = usage.get("input_tokens", 0)
    metrics["meta_completion_tokens"] = usage.get("output_tokens", 0)

    logger.info(
        "Demo eval for %s: similarity=%.2f  f1=%.2f  has_answer=%d",
        gt_id,
        metrics["answer_similarity"],
        metrics["word_overlap_f1"],
        metrics["has_answer"],
    )

    return {"$metrics": metrics}


# ---------------------------------------------------------------------------
# Metric helpers — pure Python, zero dependencies
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenisation."""
    return _WORD_RE.findall(text.lower())


def _sequence_similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio between two strings (0-1)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _word_overlap_f1(reference: str, candidate: str) -> float:
    """Token-level F1 between reference and candidate."""
    ref_tokens = _tokenize(reference)
    cand_tokens = _tokenize(candidate)
    if not ref_tokens and not cand_tokens:
        return 1.0
    if not ref_tokens or not cand_tokens:
        return 0.0

    ref_set = set(ref_tokens)
    cand_set = set(cand_tokens)
    overlap = ref_set & cand_set

    precision = len(overlap) / len(cand_set) if cand_set else 0.0
    recall = len(overlap) / len(ref_set) if ref_set else 0.0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _length_ratio(reference: str, candidate: str) -> float:
    """Ratio of candidate length to reference length, capped at 2.0."""
    ref_len = len(reference.split()) if reference else 0
    cand_len = len(candidate.split()) if candidate else 0
    if ref_len == 0:
        return 1.0 if cand_len == 0 else 2.0
    return min(cand_len / ref_len, 2.0)
