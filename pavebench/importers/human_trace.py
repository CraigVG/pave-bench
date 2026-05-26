from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def create_case_from_trace(
    trace_path: str | Path,
    out_dir: str | Path,
    case_id: str,
    image_width: int,
    image_height: int,
) -> None:
    trace = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    boundary, cutouts, properties = _first_polygon(trace)
    source_measurement_id = properties.get("sourceMeasurementId") or properties.get("measurementId")

    metadata = {
        "caseId": case_id,
        "imageSize": {
            "width": int(image_width),
            "height": int(image_height),
        },
        "source": {
            "imagery": "not included",
            "license": "pending public-domain imagery",
            "notes": "Attach redistributable public-domain imagery before promotion.",
        },
        "labelSource": {
            "kind": "human_traced_paved_surface",
            "role": "guide",
            "reviewStatus": "needs_gold_review",
            "sourceMeasurementId": source_measurement_id,
        },
        "guide": {
            "boundary": boundary,
            "cutouts": cutouts,
        },
        "clicks": [],
    }

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (destination / "guide.geojson").write_text(
        json.dumps(_feature_collection(case_id, boundary, cutouts), indent=2) + "\n",
        encoding="utf-8",
    )
