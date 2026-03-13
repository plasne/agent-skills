# Demo Evaluation Module

A minimal evaluation plug-in for the AML Evaluation Runner. It computes lightweight, deterministic metrics using only the Python standard library.

## Usage

Point the runner at this folder:

```dotenv
AML_EVAL_MODULE_DIR=<path-to>/demo-evaluation
```

## Metrics

| Metric                   | Range  | Description                                                |
| ------------------------ | ------ | ---------------------------------------------------------- |
| `answer_similarity`      | 0 – 1  | SequenceMatcher ratio between expected and actual answers. |
| `word_overlap_f1`        | 0 – 1  | Token-level F1 score (precision × recall harmonic mean).   |
| `answer_length_ratio`    | 0 – 2  | Ratio of actual to expected answer length (word count).    |
| `has_answer`             | 0 or 1 | Binary flag: did inference produce a non-empty response?   |
| `meta_inference_time_ms` | ≥ 0    | Inference latency reported by the inference step.          |
| `meta_prompt_tokens`     | ≥ 0    | Input token count from the inference usage block.          |
| `meta_completion_tokens` | ≥ 0    | Output token count from the inference usage block.         |

No network calls, no API keys, and no pip packages beyond the standard library are required.
