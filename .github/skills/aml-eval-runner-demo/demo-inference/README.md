# Demo Inference Module

A minimal inference plug-in for the AML Evaluation Runner. It accepts ground truth records in the **GTC v2 snapshot** format and returns deterministic mock responses with zero external dependencies.

## Usage

Point the runner at this folder:

```dotenv
AML_INF_MODULE_DIR=<path-to>/demo-inference
```

## How It Works

1. Reads the `question` (or `editedQuestion` / `synthQuestion`) and `answer` fields from each ground truth record.
2. Produces a slightly perturbed echo of the expected answer so evaluation metrics yield non-trivial (but imperfect) scores.
3. Returns the standard inference result dict consumed by the evaluation step.

No network calls, no API keys, and no pip packages beyond the standard library are required.
