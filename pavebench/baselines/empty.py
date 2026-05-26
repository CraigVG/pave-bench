from __future__ import annotations

import json
from pathlib import Path

from ..manifest import load_manifest
from ..schemas import Case, require_scoreable_case


def _empty_prediction(case: Case, task: str) -> dict:
    return {
        "caseId": case.case_id,
        "task": task,
        "track": "pure_segmentation",
        "boundary": [],
        "cutouts": [],
        "latencyMs": 0,
        "costUsd": 0,
        "metadata": {
            "baseline": "empty",
        },
    }


def write_empty_predictions(manifest_path: str | Path, out_path: str | Path, allow_guide: bool = False) -> None:
    rows = load_manifest(manifest_path)
    output_lines: list[str] = []
    for row in rows:
        require_scoreable_case(row.case, allow_guide=allow_guide)
        tasks = row.tasks or ["click_connected_polygon"]
        for task in tasks:
            output_lines.append(json.dumps(_empty_prediction(row.case, task), separators=(",", ":")))

    destination = Path(out_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
