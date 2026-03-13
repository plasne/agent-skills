"""
Stub GroundTruth dataclass.

The AML Evaluation Runner's ``eval_utils.py`` imports::

    from inference.Models.ground_truth import GroundTruth

At runtime the runner passes **plain dicts** (from ``json.load``), so this
dataclass is only needed to satisfy the import — its fields are never actually
used by the runner.  It mirrors the minimum shape of a GTC v2 ground truth
record so that downstream code that *does* use it gets sensible behaviour.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundTruth:
    """Minimal ground-truth record compatible with the runner's type hints."""

    id: str = ""
    question: str = ""
    answer: str = ""
    refs: list[Any] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    turns: list[Any] = field(default_factory=list)
    meta: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, file_path: str) -> "GroundTruth":
        """Load a GroundTruth from a JSON file."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_content(data)

    @classmethod
    def from_content(cls, data: dict) -> "GroundTruth":
        """Parse a dict into a GroundTruth."""
        return cls(
            id=data.get("id", ""),
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            refs=data.get("refs", []),
            tags=data.get("tags", []),
            turns=data.get("turns", data.get("history", [])),
            meta=data.get("meta"),
        )
