"""
Demo inference module for the AML Evaluation Runner.

Implements the InferenceService contract expected by the runner:
    class InferenceService:
        def process_inference_request(self, ground_truth_source: dict) -> dict

This module accepts ground truth records in the GTC v2 export schema and
returns a deterministic mock response. It has **zero external dependencies**
beyond the Python standard library so it can run inside any AML environment
without extra packages.

Ground truth input shape (GTC v2 snapshot item):
    {
        "id": "sleek-voxel",
        "question": "How do I reset my password?",       # or synthQuestion / editedQuestion
        "answer": "Navigate to Settings > Security ...",
        "refs": [{"url": "...", "title": "...", ...}],
        "tags": ["source:sme", "topic:security"],
        "history": [
            {"role": "user", "msg": "...", "refs": null},
            {"role": "assistant", "msg": "...", "refs": [...]}
        ]
    }

Output shape (matches the contract consumed by the evaluation step):
    {
        "response": "...",
        "conversation_id": "demo-...",
        "is_not_text_response": false,
        "time_taken_in_ms": 0.0,
        "function_calls": [],
        "usage": {"model": "demo-echo", "input_tokens": 0, "output_tokens": 0},
        "retries": [],
        "in_error": false
    }
"""

import hashlib
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stubs required by the AML Evaluation Runner's hard-coded imports:
#     from inference.inference import EventBus, GroundTruth
# Neither class is used at runtime; they only need to exist so the import
# resolves without error.
# ---------------------------------------------------------------------------

class EventBus:
    """No-op stub satisfying the runner's ``from inference.inference import EventBus``."""

    pass


class GroundTruth:
    """No-op stub satisfying the runner's ``from inference.inference import GroundTruth``."""

    pass


__all__ = ["InferenceService", "EventBus", "GroundTruth"]


class InferenceService:
    """Demo inference service that echoes a deterministic mock response."""

    def process_inference_request(self, ground_truth_source: dict) -> dict:
        """
        Process a single ground truth record and return a mock inference result.

        The mock response is built by reversing the expected answer (if present)
        so that evaluation metrics produce non-trivial scores — not perfect, not
        zero — making it easy to verify the pipeline is working end-to-end.

        Args:
            ground_truth_source: A ground truth record in GTC v2 export format.

        Returns:
            A dict matching the inference result schema expected by the
            evaluation step.
        """
        start = time.perf_counter()

        gt_id = ground_truth_source.get("id", "unknown")

        # Resolve the question — GTC exports use editedQuestion or synthQuestion
        question = (
            ground_truth_source.get("question")
            or ground_truth_source.get("editedQuestion")
            or ground_truth_source.get("synthQuestion")
            or ""
        )

        # Resolve the expected answer
        expected_answer = ground_truth_source.get("answer", "")

        # Build a deterministic mock response.
        # Strategy: echo the expected answer with light perturbation so metrics
        # are meaningful but imperfect.
        if expected_answer:
            response_text = _perturb_answer(expected_answer)
        else:
            response_text = f"This is a demo response to: {question}"

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info("Demo inference for %s completed in %.1f ms", gt_id, elapsed_ms)

        return {
            "response": response_text,
            "conversation_id": f"demo-{gt_id}",
            "is_not_text_response": False,
            "time_taken_in_ms": elapsed_ms,
            "function_calls": [],
            "usage": {
                "model": "demo-echo",
                "input_tokens": len(question.split()),
                "output_tokens": len(response_text.split()),
            },
            "retries": [],
            "in_error": False,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _perturb_answer(answer: str) -> str:
    """
    Return a slightly altered version of *answer* so that string-similarity
    metrics produce a score between 0 and 1 rather than exactly 1.

    The perturbation is deterministic (based on a hash of the input) so
    repeated runs yield identical results.
    """
    words = answer.split()
    if len(words) <= 3:
        return answer

    # Use a hash to pick which word to drop — deterministic but varied.
    h = int(hashlib.md5(answer.encode()).hexdigest(), 16)
    drop_index = h % len(words)
    perturbed = words[:drop_index] + words[drop_index + 1 :]
    return " ".join(perturbed)
