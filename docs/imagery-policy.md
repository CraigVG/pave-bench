# Imagery Policy

PaveBench is a public, reproducible benchmark. Imagery licensing is the single
biggest constraint on what can ship, so the rules are explicit.

## Decision: public-domain imagery for the official set; BYO source is optional and private

| Mode | Imagery | Key required | Redistributable | Official leaderboard |
|------|---------|--------------|-----------------|----------------------|
| **Official gold cases** | Public-domain aerials (USGS **NAIP**, state orthophotos) shipped with the benchmark | No | Yes | Yes |
| **Private local run** | Bring-your-own source (incl. your own Google Maps key) against your own traces | Your key | No | No — results are local/unofficial |

### Why not require a Google Maps key to run the benchmark

A Google Maps key as a hard requirement was considered and rejected:

1. **It does not cure the terms problem — it distributes it.** Google Maps
   Platform terms restrict caching/extracting Maps Content and (per our reading)
   prohibit using Maps Content to train, test, validate, or fine-tune ML/AI
   models. Requiring each user to fetch Google imagery just moves the same
   prohibited action into the benchmark's run instructions. (Confirm against the
   live terms / counsel before anything public-facing.)
2. **It breaks reproducibility.** Gold labels are traced against a *specific*
   image. Google refreshes aerials, so two runs months apart fetch different
   pixels and the same label no longer matches — scores stop being comparable.
   NAIP is dated by acquisition year, so a label stays valid against its image.
3. **It raises the barrier.** Requiring a billed cloud account excludes exactly
   the independent/academic participants a public benchmark wants, and ties a
   neutral leaderboard to one commercial vendor.

### Why BYO is still allowed (optionally, privately)

Teams legitimately want to evaluate against their own production imagery and
their own traces. That is supported as an **optional local adapter**: declare
the imagery source, results are marked non-official and are never part of the
public gold set. This mirrors how the harness already separates tracks and makes
you *declare* aids.

## How cases are structured to support both paths

Guide cases imported from human traces (see `tools/import_propaving_traces.py`)
store geometry in **geographic WGS84** (not pixels) plus:

- `bounds` — the geographic extent of the trace
- `resolutionMetersPerPixel` — capture resolution
- `coordinateSpace: geographic_wgs84`
- `source.imageryStatus: excluded_not_redistributable`

Because the geometry is world-anchored and image-independent, a promotion step
can project it onto **either** NAIP imagery (for the official `reviewed_gold`
set) **or** a BYO image (for a private run) — without re-tracing. Until imagery
is attached and reviewed, every such case stays `role: guide` /
`reviewStatus: needs_gold_review` and is not benchmark truth.
