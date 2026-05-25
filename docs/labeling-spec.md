# Labeling Spec

## Label Classes

PaveBench v0 uses one foreground class: paved surface.

Include:

- asphalt and concrete lots
- parking stalls and painted stripes
- drive aisles
- loading docks and paved service yards
- pavement hidden by ordinary parked cars or shadows when the underlying paved surface is visually inferable

Exclude:

- roofs and buildings
- grass, trees, mulch, planters, medians, and landscape islands
- sidewalks unless a case explicitly asks for pedestrian paving
- public roads unless the task explicitly says roads are in scope
- adjacent lots outside the clicked connected component
- gravel unless the case is tagged as a gravel task

## Human-Traced Paved Surfaces

Saved human-traced surfaces are valuable guide material. They can reduce labeling time, identify likely paved regions, and help choose benchmark cases.

They become gold only after review against the public-domain benchmark image.

Metadata must declare one of:

- `guide`: useful starting geometry, not benchmark truth
- `reviewed_gold`: accepted benchmark truth
- `rejected`: visible mismatch, loose scope, private/customer-specific, or otherwise not valid

## Task Rules

For `semantic_mask`, label every visible paved surface in the crop.

For `click_connected_polygon`, label only the paved component containing the target click. Interior non-paved regions must be holes/cutouts. Adjacent pavement across a road, curb, grass strip, building edge, or visible property separation is out of scope.

For future `scope_polygon`, labels must say whether the target is the whole paved surface or a commercial project scope.

## Importing Saved Traces

Use `case-from-trace` to convert an existing polygon GeoJSON into review-guide case files:

```bash
python3 -m pavebench.cli case-from-trace \
  --trace human-trace.geojson \
  --case-id pb_us_example_001 \
  --image-width 1024 \
  --image-height 1024 \
  --out-dir dataset/v0/cases/pb_us_example_001
```

This writes `metadata.json` and `gold.geojson`, but the label is intentionally marked as a guide until reviewed against public-domain imagery.
