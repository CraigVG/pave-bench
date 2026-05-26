# First Results Plan

## What The Repo Can Do Now

- Score polygon prediction JSONL.
- Score grayscale PNG mask predictions through `maskPath`.
- Score a whole manifest and report missing predictions.
- Refuse unreviewed guide traces unless `--allow-guide` is passed.
- Generate oracle and empty baseline predictions.
- Import saved human-traced polygons as guide cases, not gold truth.
- Report pixel IoU, area delta, click containment, invalid polygons, missing predictions, and square feet when `resolutionMetersPerPixel` is present.

## First Pilot Target

Start with five reviewed public-domain cases:

- one large retail lot with islands
- one small contractor-scale lot
- one adjacent-lot confusion case
- one tree/shadow case
- one no-cutout simple lot

Each case needs:

- public-domain image crop
- source/license metadata
- reviewed `gold` geometry
- at least one click for `click_connected_polygon`
- `resolutionMetersPerPixel` for sqft reporting

## First Baselines

Run:

```bash
python3 -m pavebench.cli oracle --manifest dataset/v0/manifest.jsonl --out results/oracle.jsonl
python3 -m pavebench.cli empty --manifest dataset/v0/manifest.jsonl --out results/empty.jsonl
python3 -m pavebench.cli score-manifest --manifest dataset/v0/manifest.jsonl --predictions results/oracle.jsonl --out results/oracle-score.json
python3 -m pavebench.cli score-manifest --manifest dataset/v0/manifest.jsonl --predictions results/empty.jsonl --out results/empty-score.json
```

Then add one actual model adapter:

- SAM/segmentation mask output via `maskPath`, or
- VLM polygon JSON output via `boundary` and `cutouts`.

## Needed From Craig

- 5-10 candidate lots worth making public.
- Permission to use saved ProPaving traces as reviewer guide geometry for those lots.
- A decision on imagery source for v0: USGS National Map/NAIP service export, NAIP on AWS, or manually prepared public-domain crops.
- A reviewer decision for each candidate: accept/adjust/reject the guide trace as public gold.
