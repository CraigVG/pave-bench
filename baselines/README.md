# Baselines

Planned baselines:

- oracle
- empty mask
- largest gray/dark connected component
- SAM point prompt
- one direct VLM polygon prompt
- one public train-split segmentation model

Baselines should be simple, reproducible, and intentionally boring. Their job is to validate the evaluator and expose failure modes.

Implemented:

```bash
python3 -m pavebench.cli oracle --manifest dataset/v0/manifest.example.jsonl --out results/oracle.example.jsonl
python3 -m pavebench.cli empty --manifest dataset/v0/manifest.example.jsonl --out results/empty.example.jsonl
```
