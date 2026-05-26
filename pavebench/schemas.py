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
    meters_per_pixel: float | None = None


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
class MaskPrediction:
    case_id: str
    task: str
    track: Track
    mask: list[list[int]]
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
    gt_sqft: float | None
    pred_sqft: float | None
    area_delta_pct: float
    gt_cutout_count: int
    pred_cutout_count: int
    cutout_score: float
    target_click_contained: bool
    passed: bool
    error: str | None = None


def _points(raw_points: list[list[float]]) -> list[Point]:
    return [(float(point[0]), float(point[1])) for point in raw_points]


def load_case_from_metadata(path: str | Path) -> Case:
    metadata_path = Path(path)
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    image_size = data["imageSize"]
    gold = data.get("gold") or data.get("guide")
    if not gold:
        raise ValueError(f"Case {data.get('caseId', metadata_path)} has no gold or guide geometry")
    source = data.get("source", {})
    meters_per_pixel = data.get("resolutionMetersPerPixel", source.get("resolutionMetersPerPixel"))
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
        meters_per_pixel=float(meters_per_pixel) if meters_per_pixel is not None else None,
    )


def needs_gold_review(case: Case) -> bool:
    role = str(case.label_source.get("role", "")).lower()
    review_status = str(case.label_source.get("reviewStatus", "")).lower()
    return role == "guide" or review_status in {"needs_gold_review", "rejected"}


def require_scoreable_case(case: Case, allow_guide: bool = False) -> None:
    if needs_gold_review(case) and not allow_guide:
        raise ValueError(
            f"Case {case.case_id} needs gold review; pass --allow-guide only for dry-run guide scoring."
        )
