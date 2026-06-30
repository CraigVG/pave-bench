# propaving_v0 — human-trace guide collection

250 review-guide cases imported from ProPaving production measurements via
`tools/import_propaving_traces.py`.

**These are guides, not benchmark truth.** Every case is `role: guide` /
`reviewStatus: needs_gold_review` with imagery excluded. Geometry is geographic
WGS84 with `bounds` + `resolutionMetersPerPixel` recorded, so each case can be
promoted by attaching public-domain (NAIP) imagery and reviewing. See
`docs/imagery-policy.md`.

## Composition

- `cases/propaving_<id>/metadata.json` + `guide.geojson` per case
- `manifest.jsonl` — one row per case (`caseId`, `split`, `scope`, `tasks`, ...)
- **scope** tag distinguishes `full_lot` (165) from `work_scope` (85) traces.
  Most ProPaving measurements are partial work areas ("Sealcoat", "Repair",
  sub-"Areas"); only full-lot traces suit full-surface segmentation, while
  work-scope traces fit `click_connected_polygon` / the planned `scope_polygon`.

## Privacy

Customer-identifying fields (street address, company/user/project ids) are not
written. Only the opaque trace id, opaque `sourceMeasurementId`, scope tag, and
measurement category are kept. Note that geographic `bounds`/geometry inherently
encode site location.
