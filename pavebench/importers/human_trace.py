from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..geometry import interior_point


def _strip_closure(ring: list[list[float]]) -> list[list[float]]:
    points = [[float(point[0]), float(point[1])] for point in ring]
    if len(points) > 1 and points[0] == points[-1]:
        return points[:-1]
    return points


def _first_polygon(trace: dict[str, Any]) -> tuple[list[list[float]], list[list[list[float]]], dict[str, Any]]:
    features = trace.get("features", [])
    if not features:
        raise ValueError("Trace GeoJSON has no features")
    feature = features[0]
    geometry = feature.get("geometry", {})
    if geometry.get("type") != "Polygon":
        raise ValueError("Only Polygon traces are supported in v0")
    rings = geometry.get("coordinates", [])
    if not rings:
        raise ValueError("Polygon trace has no rings")
    return _strip_closure(rings[0]), [_strip_closure(ring) for ring in rings[1:]], dict(feature.get("properties", {}))


def _feature_collection(case_id: str, boundary: list[list[float]], cutouts: list[list[list[float]]]) -> dict:
    def close(ring: list[list[float]]) -> list[list[float]]:
        return ring + [ring[0]] if ring and ring[0] != ring[-1] else ring

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "caseId": case_id,
                    "labelSourceRole": "guide",
                    "reviewStatus": "needs_gold_review",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [close(boundary), *[close(cutout) for cutout in cutouts]],
                },
            }
        ],
    }


def _auto_click(boundary: list[list[float]], cutouts: list[list[list[float]]]) -> list[dict[str, Any]]:
    try:
        x, y = interior_point(boundary, cutouts)
    except ValueError:
        return []
    return [{"id": "main", "x": x, "y": y}]


def create_case_from_trace(
    trace_path: str | Path,
    out_dir: str | Path,
    case_id: str,
    image_width: int,
    image_height: int,
    clicks: list[dict[str, Any]] | None = None,
    coordinate_space: str | None = None,
    bounds: dict[str, float] | None = None,
    meters_per_pixel: float | None = None,
    extra_source: dict[str, Any] | None = None,
    extra_label_source: dict[str, Any] | None = None,
) -> None:
    """Create a review-guide case from a human-traced polygon.

    The geometry is carried through unchanged (pixel or geographic), marked
    ``role: guide`` / ``reviewStatus: needs_gold_review`` so it is never mistaken
    for benchmark truth. Imagery is intentionally excluded; ``bounds`` +
    ``coordinate_space`` are recorded so a later step can attach redistributable
    public-domain imagery (or, in a private local run, fetch from a BYO source).

    ``clicks`` carries the click target for ``click_connected_polygon``. When
    ``None`` (default) a single interior "main" click is auto-derived; pass an
    explicit list to override, or ``[]`` to leave the case click-less.
    """

    trace = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    boundary, cutouts, properties = _first_polygon(trace)
    source_measurement_id = properties.get("sourceMeasurementId") or properties.get("measurementId")

    resolved_clicks = _auto_click(boundary, cutouts) if clicks is None else clicks

    source: dict[str, Any] = {
        "imagery": "not included",
        "license": "pending public-domain imagery",
        "notes": "Attach redistributable public-domain imagery before promotion.",
    }
    if extra_source:
        source.update(extra_source)

    label_source: dict[str, Any] = {
        "kind": "human_traced_paved_surface",
        "role": "guide",
        "reviewStatus": "needs_gold_review",
        "sourceMeasurementId": source_measurement_id,
    }
    if extra_label_source:
        label_source.update(extra_label_source)

    metadata: dict[str, Any] = {
        "caseId": case_id,
        "imageSize": {
            "width": int(image_width),
            "height": int(image_height),
        },
        "source": source,
        "labelSource": label_source,
        "guide": {
            "boundary": boundary,
            "cutouts": cutouts,
        },
        "clicks": resolved_clicks,
    }
    if coordinate_space is not None:
        metadata["coordinateSpace"] = coordinate_space
    if bounds is not None:
        metadata["bounds"] = bounds
    if meters_per_pixel is not None:
        metadata["resolutionMetersPerPixel"] = float(meters_per_pixel)

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (destination / "guide.geojson").write_text(
        json.dumps(_feature_collection(case_id, boundary, cutouts), indent=2) + "\n",
        encoding="utf-8",
    )
