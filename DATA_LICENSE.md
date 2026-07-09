# Data License

The benchmark code is MIT licensed. Dataset files are licensed separately and each case must declare its own source and data license in `metadata.json`.

PaveBench public releases must use redistributable imagery. The intended v0 sources are U.S. public-domain aerial imagery, especially:

- USDA NAIP imagery
- USGS The National Map / USGS-derived orthophoto products
- County / state government orthophotography published as a public record
  (e.g. Cook County IL 2025 ortho, Ramsey County MN 2024 ortho, served via
  ArcGIS ImageServer `exportImage`). Confirm each jurisdiction's terms and
  record `source`, `sourceUrl`, `vintage`, and `license` in the case
  `metadata.json` `imagery` block. Attribute the county/state in any publication.

Do not commit Google Maps, Google Maps Static API, Map Tiles API, Esri World
Imagery tiles, or any other non-redistributable commercial basemap imagery to
this repository. `pavebench case-from-propaving` rejects sources whose name/URL
matches Google or Esri and requires an explicit `redistributable: true`.

### Committed real-imagery cases

| Case | Imagery | License |
|------|---------|---------|
| `pb_us_il_justice_testa_001` | Cook County IL 2025 Orthophotography | Public record / public domain |

Saved human-traced paved surfaces from ProPaving can be used as guide material only when:

- the underlying imagery is replaced with redistributable public imagery,
- customer/private context is removed,
- the traced surface is reviewed against the public image,
- the metadata marks whether the trace is `guide`, `reviewed_gold`, or `rejected`.
- unreviewed traces are stored as `guide` geometry, not `gold` truth.

Human traces copied from production are not automatically benchmark truth.
