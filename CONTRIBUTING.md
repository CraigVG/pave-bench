# Contributing

## Local Checks

```bash
python3 -m pytest
```

## Dataset Contributions

Public dataset contributions must include:

- redistributable imagery source and license
- `metadata.json`
- reviewed paved-surface geometry
- clear task tags
- no Google Maps, Google Static Maps, Map Tiles, or other restricted commercial basemap imagery

Human traces from products or private systems may be submitted only as review guides. They must be reviewed against public-domain imagery before being labeled `reviewed_gold`.

## Leaderboard Contributions

Prediction submissions should disclose:

- model name and version
- track
- training/fine-tuning data
- auxiliary data used
- number of model calls
- latency and cost
- commit hash for the runner
