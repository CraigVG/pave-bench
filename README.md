# PaveBench

PaveBench is a public benchmark harness for aerial pavement segmentation and pavement-to-polygon extraction.

The benchmark is built around a practical contractor workflow: given a top-down aerial image, return a valid paved-surface mask or polygon with interior cutouts for buildings, islands, grass, trees, and other non-paved holes.

## Tracks

- `pure_segmentation`: image segmentation models that output masks or polygons.
- `vlm_polygon`: vision-language models that directly emit JSON polygon coordinates.
- `image_generation_mask`: image-generation/editing models that paint a mask image.
- `hybrid_production`: production-style pipelines using declared aids such as clicks, user boxes, parcel vectors, image cleaning, ensembles, or post-processing.

The tracks are intentionally separate. Direct VLM polygon generation, true mask segmentation, and hybrid post-processed systems test different capabilities.

## Tasks

- `semantic_mask`: segment visible pavement in the image.
- `click_connected_polygon`: return the paved component containing the target click.
- `scope_polygon`: future task for matching a specific commercial project scope.

## Google Maps Imagery

Do not use Google Maps Static API, Map Tiles API, or cached Google imagery in public PaveBench datasets.

Maps Static API is a Google Maps Platform Core Service, and Google Maps Platform terms restrict caching, extracting, and creating content from Google Maps Content. The terms also prohibit using Google Maps Content to train, test, validate, or fine-tune ML/AI models. See `docs/google-static-maps-use.md`.

## Human-Traced Surfaces

Saved ProPaving human-traced paved surfaces are useful as guide material. They can seed candidate cases, rough boundaries, or reviewer starting points.

They are not automatically benchmark truth. A public PaveBench gold label must be reviewed against redistributable imagery and marked as `reviewed_gold` in metadata.

## Quick Start

```bash
python3 -m pytest

python3 -m pavebench.cli oracle \
  --manifest dataset/v0/manifest.example.jsonl \
  --out results/oracle.example.jsonl

python3 -m pavebench.cli score-manifest \
  --manifest dataset/v0/manifest.example.jsonl \
  --predictions results/oracle.example.jsonl \
  --out results/oracle-score.json

python3 -m pavebench.cli score \
  --case dataset/v0/cases/demo_human_trace_guided/metadata.json \
  --predictions dataset/v0/cases/demo_human_trace_guided/predictions.example.jsonl \
  --out results/demo-score.json
```

Create a review-guide case from a saved human trace:

```bash
python3 -m pavebench.cli case-from-trace \
  --trace path/to/human-trace.geojson \
  --case-id pb_us_example_001 \
  --image-width 1024 \
  --image-height 1024 \
  --out-dir dataset/v0/cases/pb_us_example_001
```

The generated case is marked `role: guide` and `reviewStatus: needs_gold_review`. It must be reviewed against redistributable public imagery before becoming benchmark truth.

## Submission Shape

Predictions are JSONL:

```json
{
  "caseId": "demo_human_trace_guided",
  "task": "click_connected_polygon",
  "track": "vlm_polygon",
  "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
  "cutouts": [],
  "latencyMs": 1200,
  "costUsd": 0.01,
  "metadata": {"model": "example"}
}
```

See `docs/submission-format.md` for the full contract.

## Current Status

This repository is a v0 harness scaffold. It includes evaluator code, manifest scoring, an oracle baseline, human-trace case scaffolding, documentation, and a toy synthetic case. It does not yet include real public-domain aerial imagery.
