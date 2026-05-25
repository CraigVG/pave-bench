from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .geometry import Point

Track = Literal[
    "pure_segmentation",
    "vlm_polygon",
    "image_generation_mask",
    "hybrid_production",
]


@dataclass(frozen=True)
class Click:
    click_id: str
    x: float
    y: float


@dataclass(frozen=True)
class Case:
    case_id: str
    image_width: int
    image_height: int
    gt_boundary: list[Point]
    gt_cutouts: list[list[Point]] = field(default_factory=list)
    clicks: list[Click] = field(default_factory=list)
    label_source: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolygonPrediction:
    case_id: str
    task: str
    track: Track
    boundary: list[Point]
    cutouts: list[list[Point]] = field(default_factory=list)
    latency_ms: int | None = None
    cost_usd: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    task: str
    track: str
    iou: float
    gt_area_px: float
    pred_area_px: float
    area_delta_pct: float
    gt_cutout_count: int
    pred_cutout_count: int
    cutout_score: float
    target_click_contained: bool
    passed: bool


def _points(raw_points: list[list[float]]) -> list[Point]:
    return [(float(point[0]), float(point[1])) for point in raw_points]


def load_case_from_metadata(path: str | Path) -> Case:
    metadata_path = Path(path)
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    image_size = data["imageSize"]
    gold = data["gold"]
    clicks = [
        Click(click_id=str(click["id"]), x=float(click["x"]), y=float(click["y"]))
        for click in data.get("clicks", [])
    ]
    return Case(
        case_id=str(data["caseId"]),
        image_width=int(image_size["width"]),
        image_height=int(image_size["height"]),
        gt_boundary=_points(gold["boundary"]),
        gt_cutouts=[_points(cutout) for cutout in gold.get("cutouts", [])],
        clicks=clicks,
        label_source=dict(data.get("labelSource", {})),
    )
