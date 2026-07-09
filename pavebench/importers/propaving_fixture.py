from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from ..geometry import interior_point

# ProPaving gold traces were drawn on Google imagery; county/state orthos sit a
# couple of metres off. Ingested cases therefore land in review, never gold.
GEOREGISTRATION_CAVEAT = (
    "Gold geometry was hand-traced on Google imagery; it can sit ~2-3 m off this "
    "public-domain ortho. A reviewer must check the georegistration offset and "
    "adjust or re-trace before this case becomes reviewed_gold."
)


def _ring_lonlat(ring: list[list[float]]) -> list[tuple[float, float]]:
    points = [(float(pt[0]), float(pt[1])) for pt in ring]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    return points


def _bbox(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _project(
    ring: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> list[list[float]]:
    """Linear WGS84 -> pixel projection for an imageSR=4326 (plate-carree) export."""

    west, south, east, north = bbox
    span_lng = (east - west) or 1e-12
    span_lat = (north - south) or 1e-12
    projected: list[list[float]] = []
    for lng, lat in ring:
        x = (lng - west) / span_lng * width
        y = (north - lat) / span_lat * height
        projected.append([round(x, 3), round(y, 3)])
    return projected


def _export_image_url(base_url: str, bbox: tuple[float, float, float, float], width: int, height: int) -> str:
    west, south, east, north = bbox
    query = urllib.parse.urlencode(
        {
            "bbox": f"{west},{south},{east},{north}",
            "bboxSR": 4326,
            "imageSR": 4326,
            "size": f"{width},{height}",
            "format": "png",
            "f": "image",
        }
    )
    return f"{base_url.rstrip('/')}/exportImage?{query}"


def _meters_extent(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bbox
    lat_mid = math.radians((south + north) / 2)
    width_m = (east - west) * 111_320 * math.cos(lat_mid)
    height_m = (north - south) * 111_320
    return width_m, height_m


def create_case_from_propaving(
    fixture_path: str | Path,
    out_dir: str | Path,
    case_id: str,
    imagery_source: dict[str, Any],
    export_gsd_meters: float = 0.15,
    max_pixels: int = 4000,
    fetch: bool = True,
    split: str = "dev",
) -> dict[str, Any]:
    """Scaffold a benchmark case from a ProPaving gold fixture + imagery spec.

    ``imagery_source`` must declare a REDISTRIBUTABLE public-domain source, e.g.::

        {"name": "Cook County 2025 Orthophotography",
         "imageServer": "https://.../CookOrtho2025/ImageServer",
         "nativeGsdMeters": 0.1524, "vintage": "2025",
         "license": "public domain", "redistributable": true}

    Google imagery and Esri tiles are never redistributable and are rejected. The
    case is written with ``reviewStatus: needs_gold_review`` and the
    georegistration caveat; it is not benchmark truth until a reviewer promotes it.
    """

    if not imagery_source.get("redistributable"):
        raise ValueError(
            "imagery_source.redistributable must be true; only public-domain "
            "county/state orthos or USGS NAIP may back a public PaveBench case."
        )
    banned = ("google", "googleapis", "esri", "arcgisonline")
    haystack = " ".join(
        str(imagery_source.get(key, "")) for key in ("name", "imageServer", "sourceUrl", "license")
    ).lower()
    if any(term in haystack for term in banned):
        raise ValueError(
            f"imagery_source looks non-redistributable ({haystack!r}); Google and "
            "Esri World Imagery are prohibited for public cases."
        )

    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    geometry = fixture.get("geometry", {})
    if geometry.get("type") != "Polygon":
        raise ValueError("ProPaving fixture geometry must be a Polygon")
    rings = geometry.get("coordinates", [])
    if not rings:
        raise ValueError("ProPaving fixture polygon has no rings")

    boundary_lonlat = _ring_lonlat(rings[0])
    cutouts_lonlat = [_ring_lonlat(ring) for ring in rings[1:]]

    # The imagery extent is the user's analysis box when present ("imagery/crop
    # must fully contain this"), else the paved boundary.
    analysis_area = (fixture.get("analysisArea") or {}).get("geometry", {})
    if analysis_area.get("type") == "Polygon" and analysis_area.get("coordinates"):
        box_lonlat = _ring_lonlat(analysis_area["coordinates"][0])
        bbox = _bbox(box_lonlat)
    else:
        box_lonlat = None
        bbox = _bbox(boundary_lonlat)

    width_m, height_m = _meters_extent(bbox)
    width = max(1, round(width_m / export_gsd_meters))
    height = max(1, round(height_m / export_gsd_meters))
    scale = min(1.0, max_pixels / max(width, height))
    width = max(1, round(width * scale))
    height = max(1, round(height * scale))
    effective_gsd = round(((width_m / width) + (height_m / height)) / 2, 5)

    boundary_px = _project(boundary_lonlat, bbox, width, height)
    cutouts_px = [_project(ring, bbox, width, height) for ring in cutouts_lonlat]
    input_box_px = _project(box_lonlat, bbox, width, height) if box_lonlat else None

    try:
        cx, cy = interior_point(
            [(p[0], p[1]) for p in boundary_px],
            [[(p[0], p[1]) for p in ring] for ring in cutouts_px],
        )
        clicks = [{"id": "main", "x": round(cx, 3), "y": round(cy, 3)}]
    except ValueError:
        clicks = []

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)

    image_url = _export_image_url(imagery_source["imageServer"], bbox, width, height)
    imagery_status = "declared_not_fetched"
    image_file: str | None = None
    if fetch:
        request = urllib.request.Request(image_url, headers={"User-Agent": "PaveBench/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 (public gov ImageServer)
            payload = response.read()
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            raise RuntimeError(f"ImageServer did not return an image (Content-Type={content_type})")
        (destination / "image.png").write_bytes(payload)
        image_file = "image.png"
        imagery_status = "included_redistributable"

    native_gsd = imagery_source.get("nativeGsdMeters")
    imagery = {
        "source": imagery_source.get("name"),
        "sourceUrl": imagery_source.get("imageServer"),
        "exportUrl": image_url,
        "imageFile": image_file,
        "nativeGsdMeters": native_gsd,
        "exportGsdMeters": effective_gsd,
        "vintage": imagery_source.get("vintage"),
        "license": imagery_source.get("license"),
        "redistributable": True,
        "imageryStatus": imagery_status,
        "bbox": {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]},
        "bboxSR": 4326,
    }

    label_source = {
        "kind": "human_traced_paved_surface",
        "role": "guide",
        "reviewStatus": "needs_gold_review",
        "sourceMeasurementId": fixture.get("id"),
        "sourceName": fixture.get("name"),
        "tracedOn": "google_imagery",
        "georegistrationCaveat": GEOREGISTRATION_CAVEAT,
    }

    metadata: dict[str, Any] = {
        "caseId": case_id,
        "split": split,
        "imageSize": {"width": width, "height": height},
        "coordinateSpace": "image_pixels",
        "imagery": imagery,
        "resolutionMetersPerPixel": effective_gsd,
        "labelSource": label_source,
        "referenceSquareFeet": fixture.get("squareFeet"),
        "gold": {"boundary": boundary_px, "cutouts": cutouts_px},
        "clicks": clicks,
    }
    if input_box_px is not None:
        metadata["inputBox"] = input_box_px

    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    features = [
        {
            "type": "Feature",
            "properties": {"caseId": case_id, "role": "guide", "reviewStatus": "needs_gold_review"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    boundary_px + [boundary_px[0]],
                    *[ring + [ring[0]] for ring in cutouts_px],
                ],
            },
        }
    ]
    (destination / "gold.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
        encoding="utf-8",
    )

    return metadata
