# Benchmark Card

## Intended Use

PaveBench evaluates aerial pavement segmentation and pavement polygon extraction for contractor-style measurement workflows.

## Not Intended For

PaveBench is not a generic road-network extraction benchmark, not a cadastral boundary benchmark, and not a legal property-boundary dataset.

## Public Data Rule

Public releases should use redistributable public-domain imagery. Google Maps, Google Maps Static API, Map Tiles API, and other restricted commercial basemaps must not be committed as benchmark imagery.

## Label Quality

Benchmark labels should be hand-reviewed paved-surface masks or polygons. Existing product drawings can guide reviewers, but loose project-scope overlays are not strict segmentation truth.

## Known Biases

Initial cases will likely overrepresent U.S. parking lots and contractor-relevant paved surfaces. The dataset should explicitly tag snow, canopy, shadows, adjacent lots, commercial retail, industrial yards, and small lots as coverage grows.

## Metrics

PaveBench reports IoU, area delta, cutout counts, click containment, pass/fail gates, and eventually boundary F1, p90 failure rates, invalid polygon rate, latency, and cost.
