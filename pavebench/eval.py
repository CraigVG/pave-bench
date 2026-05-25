from __future__ import annotations

from .geometry import point_in_polygon, polygon_area, rasterize_polygon
from .schemas import Case, EvalResult, PolygonPrediction

PASS_IOU = 0.86
PASS_AREA_DELTA = 0.08
PASS_CUTOUT_DELTA = 2


def mask_iou(truth: list[list[int]], pred: list[list[int]]) -> float:
    if len(truth) != len(pred) or any(len(t_row) != len(p_row) for t_row, p_row in zip(truth, pred)):
        raise ValueError("truth and pred masks must have matching dimensions")

    intersection = 0
    union = 0
    for truth_row, pred_row in zip(truth, pred):
        for truth_value, pred_value in zip(truth_row, pred_row):
            truth_on = bool(truth_value)
            pred_on = bool(pred_value)
            if truth_on and pred_on:
                intersection += 1
            if truth_on or pred_on:
                union += 1
    return 1.0 if union == 0 else intersection / union


def cutout_score(gt_count: int, pred_count: int) -> float:
    if gt_count == 0:
        return max(0.0, 1.0 - pred_count * 0.2)
    return max(0.0, 1.0 - min(1.0, abs(pred_count - gt_count) / gt_count))


def evaluate_polygon_prediction(case: Case, prediction: PolygonPrediction) -> EvalResult:
    truth_mask = rasterize_polygon(case.gt_boundary, case.gt_cutouts, case.image_width, case.image_height)
    pred_mask = rasterize_polygon(prediction.boundary, prediction.cutouts, case.image_width, case.image_height)
    iou = mask_iou(truth_mask, pred_mask)

    gt_area = polygon_area(case.gt_boundary, case.gt_cutouts)
    pred_area = polygon_area(prediction.boundary, prediction.cutouts)
    area_delta = 0.0 if gt_area == 0 and pred_area == 0 else abs(pred_area - gt_area) / max(gt_area, 1e-12)

    target_click_contained = True
    if case.clicks:
        click = case.clicks[0]
        target_click_contained = point_in_polygon((click.x, click.y), prediction.boundary, prediction.cutouts)

    gt_cutouts = len(case.gt_cutouts)
    pred_cutouts = len(prediction.cutouts)
    cutouts_ok = abs(gt_cutouts - pred_cutouts) <= PASS_CUTOUT_DELTA
    passed = iou >= PASS_IOU and area_delta <= PASS_AREA_DELTA and cutouts_ok and target_click_contained

    return EvalResult(
        case_id=case.case_id,
        task=prediction.task,
        track=prediction.track,
        iou=iou,
        gt_area_px=gt_area,
        pred_area_px=pred_area,
        area_delta_pct=area_delta,
        gt_cutout_count=gt_cutouts,
        pred_cutout_count=pred_cutouts,
        cutout_score=cutout_score(gt_cutouts, pred_cutouts),
        target_click_contained=target_click_contained,
        passed=passed,
    )
