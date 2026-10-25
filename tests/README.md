# Own tests

Run from the repository root:

```sh
python tools/run.py --input tests/own_cases.jsonl > tests/actual.jsonl
python tests/check_own.py
python tests/scale_benchmark.py
```

`own_cases.jsonl`, `expected.jsonl` and `actual.jsonl` have matching lines. `check_own.py` checks witness validity, alternative valid answers, invalid witnesses and route reconstruction. `scale_benchmark.py` generates the published maximum sizes and writes actual summaries and timings to `scale_benchmark_actual.json`. The reasoning for expected values and the benchmark method are in `ANALYSIS.md`.
