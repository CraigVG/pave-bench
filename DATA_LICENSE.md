# Data License

The benchmark code is MIT licensed. Dataset files are licensed separately and each case must declare its own source and data license in `metadata.json`.

PaveBench public releases must use redistributable imagery. The intended v0 sources are U.S. public-domain aerial imagery, especially:

- USDA NAIP imagery
- USGS The National Map / USGS-derived orthophoto products

Do not commit Google Maps, Google Maps Static API, Map Tiles API, or other non-redistributable commercial basemap imagery to this repository.

Saved human-traced paved surfaces from ProPaving can be used as guide material only when:

- the underlying imagery is replaced with redistributable public imagery,
- customer/private context is removed,
- the traced surface is reviewed against the public image,
- the metadata marks whether the trace is `guide`, `reviewed_gold`, or `rejected`.
- unreviewed traces are stored as `guide` geometry, not `gold` truth.

Human traces copied from production are not automatically benchmark truth.
