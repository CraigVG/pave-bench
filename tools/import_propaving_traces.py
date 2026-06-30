#!/usr/bin/env python3
"""Batch-import ProPaving human traces into PaveBench review-guide cases.

Reads the curated production traces in
``../propaving/scripts/vision-finetune/data/prod-curated-250`` and emits one
PaveBench guide case per trace under ``dataset/v0/propaving_v0/``.

Design decisions (see docs/imagery-policy.md):
  * Geometry is kept GEOGRAPHIC (WGS84 lng/lat), not pixel — the traces are
    world-anchored and the imagery (currently Google Static Maps, which is NOT
    redistributable) is excluded. Each case records its ``bounds`` and
    ``resolutionMetersPerPixel`` so a later step can attach public-domain NAIP
    imagery for the official set, or fetch from a BYO source for a private run.
  * Every case is ``role: guide`` / ``reviewStatus: needs_gold_review`` — these
    are reviewer guides, not benchmark truth, until paired with public imagery.
  * Customer-identifying fields (street address, company/user ids) are NOT
    written. Only the opaque trace id, opaque sourceMeasurementId, a coarse
    scope tag, and the (non-PII) measurement category are kept.

Run from the pave-bench repo root:
    python3 tools/import_propaving_traces.py [--limit N] [--full-lot-only]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pavebench.importers.human_trace import create_case_from_trace  # noqa: E402
SRC = REPO_ROOT.parent / "propaving" / "scripts" / "vision-finetune" / "data" / "prod-curated-250"
OUT = REPO_ROOT / "dataset" / "v0" / "propaving_v0"


def meters_per_pixel(bounds: dict, image_width: int) -> float:
    lat_mid = (bounds["north"] + bounds["south"]) / 2.0
    width_deg = bounds["east"] - bounds["west"]
    width_m = abs(width_deg) * 111_320.0 * math.cos(math.radians(lat_mid))
    return width_m / image_width if image_width else 0.0


def classify_scope(row: dict) -> str:
    """Full-lot traces vs partial work-scope measurements (see FINDINGS)."""
    name = (row.get("measurementName") or "").lower()
    if "repair" in name:
        return "work_scope"
    if row.get("maskCoverage", 0) >= 0.15 and row.get("squareFeet", 0) >= 15_000:
        return "full_lot"
    return "work_scope"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only import the first N traces")
    parser.add_argument("--full-lot-only", action="store_true", help="Skip partial work-scope traces")
    parser.add_argument("--clean", action="store_true", help="Remove existing propaving_v0 output first")
    args = parser.parse_args()

    if not SRC.exists():
        raise SystemExit(f"Source dataset not found: {SRC}")

    manifest_path = SRC / "manifest.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text().splitlines() if line.strip()]

    if args.clean and OUT.exists():
        shutil.rmtree(OUT)
    cases_dir = OUT / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    manifest_lines: list[str] = []
    counts = {"full_lot": 0, "work_scope": 0, "skipped_no_geojson": 0, "errors": 0}
    imported = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for row in rows:
            if args.limit and imported >= args.limit:
                break
            cid = row["id"]
            geojson_path = SRC / "geojson" / f"{cid}.geojson"
            if not geojson_path.exists():
                counts["skipped_no_geojson"] += 1
                continue

            scope = classify_scope(row)
            if args.full_lot_only and scope != "full_lot":
                continue

            feature = json.loads(geojson_path.read_text())
            # Importer expects a FeatureCollection.
            fc = {"type": "FeatureCollection", "features": [feature]}
            trace_file = tmp_dir / f"{cid}.geojson"
            trace_file.write_text(json.dumps(fc))

            case_id = f"propaving_{cid}"
            out_case = cases_dir / case_id
            bounds = row["actualBounds"]
            size = row["imageSize"]
            mpp = meters_per_pixel(bounds, size["width"])

            extra_source = {
                "imagerySource": "google-static-maps",
                "imageryStatus": "excluded_not_redistributable",
                "captureZoom": row.get("zoom"),
            }
            extra_label_source = {
                "scope": scope,
                "humanTracedSquareFeet": row.get("squareFeet"),
                "cutoutCount": row.get("cutoutCount"),
            }
            if row.get("categoryName"):
                extra_label_source["category"] = row["categoryName"]

            try:
                create_case_from_trace(
                    trace_path=trace_file,
                    out_dir=out_case,
                    case_id=case_id,
                    image_width=size["width"],
                    image_height=size["height"],
                    coordinate_space="geographic_wgs84",
                    bounds=bounds,
                    meters_per_pixel=mpp,
                    extra_source=extra_source,
                    extra_label_source=extra_label_source,
                )
            except Exception as exc:  # noqa: BLE001 - report and continue
                counts["errors"] += 1
                print(f"  ! {case_id}: {exc}")
                continue

            tasks = ["click_connected_polygon"]
            if scope == "work_scope":
                tasks.append("scope_polygon")  # planned task; this trace fits it
            manifest_lines.append(
                json.dumps(
                    {
                        "caseId": case_id,
                        "split": row.get("split", "train"),
                        "scope": scope,
                        "tasks": tasks,
                        "metadataPath": f"cases/{case_id}/metadata.json",
                        "imagePath": None,
                        "license": "guide / needs_gold_review; imagery pending (NAIP)",
                        "tags": ["human_trace_guide", scope, "imagery_excluded"],
                    }
                )
            )
            counts[scope] += 1
            imported += 1

    (OUT / "manifest.jsonl").write_text("\n".join(manifest_lines) + ("\n" if manifest_lines else ""))

    print(f"Imported {imported} cases -> {OUT}")
    print(f"  full_lot={counts['full_lot']}  work_scope={counts['work_scope']}")
    if counts["skipped_no_geojson"]:
        print(f"  skipped (no geojson)={counts['skipped_no_geojson']}")
    if counts["errors"]:
        print(f"  errors={counts['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
