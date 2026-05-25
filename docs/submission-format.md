# Submission Format

Predictions are JSON Lines files. Each line is one case/task prediction.

```json
{
  "caseId": "demo_human_trace_guided",
  "task": "click_connected_polygon",
  "track": "vlm_polygon",
  "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
  "cutouts": [],
  "latencyMs": 1200,
  "costUsd": 0.01,
  "metadata": {
    "model": "example-model",
    "modelCalls": 1,
    "promptHash": "sha256:..."
  }
}
```

Coordinates are pixel coordinates in `[x, y]` order with origin at the top-left corner of the benchmark image.

Required fields:

- `caseId`
- `task`
- `track`
- `boundary`
- `cutouts`

Allowed `track` values:

- `pure_segmentation`
- `vlm_polygon`
- `image_generation_mask`
- `hybrid_production`

Every leaderboard submission should also disclose model versions, training data, auxiliary data, number of model calls, average cost, average latency, and the code commit used to generate predictions.

## CLI

Score one case:

```bash
python3 -m pavebench.cli score --case path/to/metadata.json --predictions predictions.jsonl --out score.json
```

Score a manifest:

```bash
python3 -m pavebench.cli score-manifest --manifest dataset/v0/manifest.example.jsonl --predictions predictions.jsonl --out score.json
```

Generate oracle predictions:

```bash
python3 -m pavebench.cli oracle --manifest dataset/v0/manifest.example.jsonl --out oracle.jsonl
```
