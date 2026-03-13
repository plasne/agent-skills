#!/usr/bin/env python3
"""
Set up the AML Evaluation Runner demo modules.

This script:
1. Copies demo-inference and demo-evaluation into the aml-evaluation-runner tree.
2. Splits the sample ground-truths array into individual JSON files in the
   ground-truths datastore location (or a local folder for testing).
3. Prints the .exp.env lines to paste for AML_INF_MODULE_DIR and AML_EVAL_MODULE_DIR.

Usage:
    python setup_demo.py [--runner-root <path>] [--gt-output <path>]

Defaults:
    --runner-root   ../../aml-evaluation-runner   (relative to this script)
    --gt-output     <runner-root>/experiment/ground-truths
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up AML eval runner demo modules.")
    parser.add_argument(
        "--runner-root",
        type=str,
        default=None,
        help="Path to the aml-evaluation-runner directory.",
    )
    parser.add_argument(
        "--gt-output",
        type=str,
        default=None,
        help="Directory where individual ground-truth JSON files are written.",
    )
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent  # .github/skills/aml-eval-runner-demo
    workspace_root = skill_dir.parent.parent.parent     # workspace root

    runner_root = Path(args.runner_root) if args.runner_root else workspace_root / "aml-evaluation-runner"
    runner_root = runner_root.resolve()

    if not runner_root.is_dir():
        print(f"Error: runner root not found at {runner_root}", file=sys.stderr)
        sys.exit(1)

    # --- 1. Copy modules ---------------------------------------------------
    inf_src = skill_dir / "demo-inference"
    eval_src = skill_dir / "demo-evaluation"
    inf_dst = runner_root / "inference" / "demo-inference"
    eval_dst = runner_root / "evaluation" / "demo-evaluation"

    for src, dst in [(inf_src, inf_dst), (eval_src, eval_dst)]:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Copied {src.name} -> {dst}")

    # --- 2. Split ground truths --------------------------------------------
    gt_output = Path(args.gt_output) if args.gt_output else runner_root / "experiment" / "ground-truths"
    gt_output.mkdir(parents=True, exist_ok=True)

    sample_file = skill_dir / "assets" / "sample-ground-truths.json"
    if sample_file.exists():
        with open(sample_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        for item in items:
            item_id = item.get("id", "unknown")
            out_path = gt_output / f"{item_id}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(item, f, indent=2, ensure_ascii=False)
            print(f"Wrote {out_path.name}")

        print(f"\n{len(items)} ground-truth files written to {gt_output}")
    else:
        print(f"Warning: sample ground-truths not found at {sample_file}")

    # --- 3. Show .exp.env config -------------------------------------------
    inf_rel = os.path.relpath(inf_dst, runner_root / "experiment")
    eval_rel = os.path.relpath(eval_dst, runner_root / "experiment")

    print("\n--- Add these lines to experiment/.exp.env ---")
    print(f"AML_INF_MODULE_DIR={inf_rel}")
    print(f"AML_EVAL_MODULE_DIR={eval_rel}")
    print()


if __name__ == "__main__":
    main()
