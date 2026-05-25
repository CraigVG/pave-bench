from __future__ import annotations

import json
from pathlib import Path

from ..manifest import load_manifest
from ..schemas import Case


def _coords(points: list[tuple[float, float]]) -> list[list[float]]:
    return [[float(x), float(y)] for x, y in points]


def _oracle_prediction(case: Case, task: str) -> dict:
    return {
        "caseId": case.case_id,
        "task": task,
        "track": "hybrid_production",
        "boundary": _coords(case.gt_boundary),
        "cutouts": [_coords(cutout) for cutout in case.gt_cutouts],
        "latencyMs": 0,
        "costUsd": 0,
        "metadata": {
            "baseline": "oracle",
            "usesGoldGeometry": True,
        },
    }


def write_oracle_predictions(manifest_path: str | Path, out_path: str | Path) -> None:
    rows = load_manifest(manifest_path)
    output_lines: list[str] = []
    for row in rows:
        tasks = row.tasks or ["click_connected_polygon"]
        for task in tasks:
            output_lines.append(json.dumps(_oracle_prediction(row.case, task), separators=(",", ":")))

    destination = Path(out_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
