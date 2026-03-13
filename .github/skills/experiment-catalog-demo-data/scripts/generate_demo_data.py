#!/usr/bin/env python3
"""Generate realistic demo data for the experiment catalog.

Usage:
    python generate_demo_data.py [--base-url URL] [--results N]
"""

import argparse
import random
import sys
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECTS = ["sprint01", "sprint02"]

METRIC_DEFINITIONS: list[dict[str, Any]] = [
    {"name": "retrieval_accuracy",      "min": 0.0, "max": 1.0, "aggregate_function": "Average", "order": 100},
    {"name": "retrieval_precision",     "min": 0.0, "max": 1.0, "aggregate_function": "Average", "order": 110},
    {"name": "retrieval_recall",        "min": 0.0, "max": 1.0, "aggregate_function": "Average", "order": 120},
    {"name": "generation_correctness",  "min": 0.0, "max": 1.0, "aggregate_function": "Average", "order": 300},
    {"name": "generation_faithfulness", "min": 0.0, "max": 1.0, "aggregate_function": "Average", "order": 310},
    {"name": "meta_inference_time",     "aggregate_function": "Average", "order": 1000, "tags": ["lower-is-better", "no-p"]},
    {"name": "meta_inference_cost",     "aggregate_function": "Cost",    "order": 1010, "tags": ["lower-is-better"]},
]

EXPERIMENTS: dict[str, dict[str, Any]] = {
    "top-k": {
        "hypothesis": "Varying the retrieval top-k parameter improves accuracy by surfacing more relevant passages.",
        "permutations": ["top-k-3", "top-k-5", "top-k-10"],
        # Per-permutation metric biases (added to base random value).
        "biases": {
            "top-k-3": {
                "retrieval_accuracy": -0.05, "retrieval_precision": 0.08, "retrieval_recall": -0.12,
                "generation_correctness": -0.03, "generation_faithfulness": 0.0,
                "meta_inference_time": -0.4, "meta_inference_cost": -0.002,
            },
            "top-k-5": {
                "retrieval_accuracy": 0.0, "retrieval_precision": 0.0, "retrieval_recall": 0.0,
                "generation_correctness": 0.0, "generation_faithfulness": 0.0,
                "meta_inference_time": 0.0, "meta_inference_cost": 0.0,
            },
            "top-k-10": {
                "retrieval_accuracy": 0.04, "retrieval_precision": -0.06, "retrieval_recall": 0.10,
                "generation_correctness": 0.02, "generation_faithfulness": -0.01,
                "meta_inference_time": 0.6, "meta_inference_cost": 0.003,
            },
        },
    },
    "models": {
        "hypothesis": "Larger language models produce better generation quality at the expense of cost and latency.",
        "permutations": ["gpt-4o-mini", "gpt-4o", "gpt-4.1"],
        "biases": {
            "gpt-4o-mini": {
                "retrieval_accuracy": 0.0, "retrieval_precision": 0.0, "retrieval_recall": 0.0,
                "generation_correctness": -0.08, "generation_faithfulness": -0.06,
                "meta_inference_time": -1.0, "meta_inference_cost": -0.005,
            },
            "gpt-4o": {
                "retrieval_accuracy": 0.0, "retrieval_precision": 0.0, "retrieval_recall": 0.0,
                "generation_correctness": 0.0, "generation_faithfulness": 0.0,
                "meta_inference_time": 0.0, "meta_inference_cost": 0.0,
            },
            "gpt-4.1": {
                "retrieval_accuracy": 0.0, "retrieval_precision": 0.0, "retrieval_recall": 0.0,
                "generation_correctness": 0.06, "generation_faithfulness": 0.05,
                "meta_inference_time": 0.8, "meta_inference_cost": 0.004,
            },
        },
    },
}

# Base centres for each metric (before bias).
METRIC_CENTRES: dict[str, tuple[float, float]] = {
    # (centre, noise_half_width)
    "retrieval_accuracy":      (0.72,  0.15),
    "retrieval_precision":     (0.68,  0.18),
    "retrieval_recall":        (0.75,  0.14),
    "generation_correctness":  (0.65,  0.20),
    "generation_faithfulness": (0.70,  0.16),
    "meta_inference_time":     (2.5,   1.2),
    "meta_inference_cost":     (0.012, 0.006),
}

# Tags and the approximate fraction of refs they apply to.
TAGS: dict[str, float] = {
    "multi-turn":     0.15,
    "complex-query":  0.10,
    "domain:finance": 0.25,
    "domain:legal":   0.25,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _post(url: str, json: Any, *, allow_conflict: bool = True) -> None:
    """POST JSON and raise for unexpected errors. 409 conflicts are silently skipped."""
    resp = requests.post(url, json=json, timeout=30)
    if allow_conflict and resp.status_code == 409:
        return
    resp.raise_for_status()


def _put(url: str, json: Any) -> None:
    resp = requests.put(url, json=json, timeout=30)
    resp.raise_for_status()


def _patch(url: str) -> None:
    resp = requests.patch(url, timeout=30)
    resp.raise_for_status()


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _generate_metric_value(metric_name: str, bias: float) -> float:
    centre, half_width = METRIC_CENTRES[metric_name]
    raw = random.gauss(centre + bias, half_width * 0.5)
    # Clamp bounded metrics to [0, 1]; leave unbounded ones non-negative.
    if metric_name.startswith("meta_"):
        return round(max(0.0, raw), 4)
    return round(_clamp(raw, 0.0, 1.0), 4)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def generate(base_url: str, num_results: int) -> None:
    api = f"{base_url}/api"
    ref_ids = [f"q{str(i).zfill(3)}" for i in range(1, num_results + 1)]

    for project in PROJECTS:
        print(f"\n{'='*60}")
        print(f"Project: {project}")
        print(f"{'='*60}")

        # -- Create project ------------------------------------------------
        _post(f"{api}/projects", {"name": project})
        print(f"  Created project '{project}'")

        # -- Metric definitions --------------------------------------------
        _put(f"{api}/projects/{project}/metrics", METRIC_DEFINITIONS)
        print(f"  Added {len(METRIC_DEFINITIONS)} metric definitions")

        # -- Tags ----------------------------------------------------------
        tag_assignments: dict[str, list[str]] = {t: [] for t in TAGS}
        for ref in ref_ids:
            for tag_name, fraction in TAGS.items():
                if random.random() < fraction:
                    tag_assignments[tag_name].append(ref)

        for tag_name, refs in tag_assignments.items():
            if refs:
                _put(f"{api}/projects/{project}/tags", {"name": tag_name, "refs": refs})
                print(f"  Tag '{tag_name}' → {len(refs)} refs")

        # -- Experiments ---------------------------------------------------
        for exp_name, exp_cfg in EXPERIMENTS.items():
            print(f"\n  Experiment: {exp_name}")

            _post(
                f"{api}/projects/{project}/experiments",
                {"name": exp_name, "hypothesis": exp_cfg["hypothesis"]},
            )

            permutations: list[str] = exp_cfg["permutations"]
            biases: dict[str, dict[str, float]] = exp_cfg["biases"]

            # First permutation is the baseline.
            baseline_set = permutations[0]

            for perm in permutations:
                perm_bias = biases[perm]
                count = 0
                for ref in ref_ids:
                    metrics: dict[str, float] = {}
                    for m_name in METRIC_CENTRES:
                        metrics[m_name] = _generate_metric_value(m_name, perm_bias.get(m_name, 0.0))
                    _post(
                        f"{api}/projects/{project}/experiments/{exp_name}/results",
                        {"ref": ref, "set": perm, "metrics": metrics},
                    )
                    count += 1

                print(f"    Permutation '{perm}': {count} results")

            # Set the first permutation as baseline for the experiment.
            _patch(f"{api}/projects/{project}/experiments/{exp_name}/sets/{baseline_set}/baseline")
            print(f"    Baseline set to '{baseline_set}'")

    print(f"\n{'='*60}")
    print("Done. Demo data generation complete.")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo data for the experiment catalog.")
    parser.add_argument("--base-url", default="http://localhost:6010", help="Catalog API base URL (default: http://localhost:6010)")
    parser.add_argument("--results", type=int, default=300, help="Number of results per permutation (default: 300)")
    args = parser.parse_args()

    try:
        generate(args.base_url, args.results)
    except requests.ConnectionError:
        print(f"\nERROR: Could not connect to {args.base_url}. Is the catalog backend running?", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as exc:
        print(f"\nERROR: HTTP {exc.response.status_code} — {exc.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
