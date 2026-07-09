import math

from pavebench.schemas import Case, StallCountPrediction
from pavebench.stalls import (
    evaluate_stall_prediction,
    match_stalls,
    missing_stall_result,
    stall_centroid,
)


def _case(**overrides):
    base = dict(
        case_id="lot",
        image_width=100,
        image_height=100,
        gt_boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
        meters_per_pixel=0.1,
        native_meters_per_pixel=0.1,
        gt_stall_count=10,
    )
    base.update(overrides)
    return Case(**base)


def test_stall_centroid_handles_points_and_boxes():
    assert stall_centroid([4, 6]) == (4.0, 6.0)
    assert stall_centroid([[0, 0], [2, 0], [2, 2], [0, 2]]) == (1.0, 1.0)


def test_count_error_pct_is_signed_and_pass_uses_ten_percent():
    case = _case(gt_stall_count=100)
    prediction = StallCountPrediction(case_id="lot", task="stall_count", track="hybrid_production", count=108)
    result = evaluate_stall_prediction(case, prediction)
    assert math.isclose(result.count_error_pct, 8.0)
    assert math.isclose(result.abs_count_error_pct, 8.0)
    assert result.passed

    over = StallCountPrediction(case_id="lot", task="stall_count", track="hybrid_production", count=130)
    assert not evaluate_stall_prediction(case, over).passed


def test_match_stalls_is_one_to_one_within_radius():
    predicted = [(0, 0), (10, 0), (0, 0)]
    markers = [(1, 0), (11, 0)]
    matches = match_stalls(predicted, markers, radius_px=2.0)
    matched_preds = {m[0] for m in matches}
    matched_markers = {m[1] for m in matches}
    assert len(matches) == 2
    assert matched_markers == {0, 1}
    # The duplicate predicted point at the origin cannot claim an already-used marker.
    assert 0 in matched_preds and 2 not in matched_preds


def test_location_metrics_use_meters_and_2p7_radius():
    # 0.1 m/px -> 2.7 m radius = 27 px. Markers offset 10 px (1.0 m) from stalls.
    markers = [(20, 20), (40, 20), (60, 20)]
    stalls = [[10, 20], [30, 20], [50, 20]]
    case = _case(gt_stall_count=3, gt_stall_markers=markers, stall_match_radius_m=2.7)
    prediction = StallCountPrediction(
        case_id="lot", task="stall_count", track="hybrid_production", count=3, stalls=stalls
    )
    result = evaluate_stall_prediction(case, prediction)
    assert result.has_markers
    assert result.matched == 3
    assert math.isclose(result.precision, 1.0)
    assert math.isclose(result.recall, 1.0)
    assert math.isclose(result.median_location_error_m, 1.0, rel_tol=1e-6)


def test_markers_without_resolution_downgrade_gracefully():
    case = _case(meters_per_pixel=None, native_meters_per_pixel=None, gt_stall_markers=[(1, 1)])
    prediction = StallCountPrediction(
        case_id="lot", task="stall_count", track="hybrid_production", count=10, stalls=[[1, 1]]
    )
    result = evaluate_stall_prediction(case, prediction)
    assert not result.has_markers
    assert result.error == "no_resolution_for_location_metrics"
    # Count-based scoring still works.
    assert result.count_error_pct == 0.0


def test_missing_stall_result_marks_failure():
    result = missing_stall_result(_case(gt_stall_count=10), "stall_count")
    assert result.error == "missing_prediction"
    assert not result.passed
    assert result.abs_count_error_pct == 100.0
