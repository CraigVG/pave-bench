import math

from pavebench.eval import evaluate_polygon_prediction, mask_iou
from pavebench.schemas import Case, Click, PolygonPrediction


def test_mask_iou_scores_overlap():
    truth = [[1, 1, 0], [0, 0, 0]]
    pred = [[1, 0, 0], [1, 0, 0]]

    assert mask_iou(truth, pred) == 1 / 3


def test_evaluate_polygon_prediction_scores_perfect_click_connected_case():
    case = Case(
        case_id="demo",
        image_width=10,
        image_height=10,
        gt_boundary=[(1, 1), (9, 1), (9, 9), (1, 9)],
        gt_cutouts=[[(4, 4), (6, 4), (6, 6), (4, 6)]],
        clicks=[Click(click_id="main", x=2, y=2)],
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="click_connected_polygon",
        track="vlm_polygon",
        boundary=case.gt_boundary,
        cutouts=case.gt_cutouts,
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert result.iou == 1
    assert result.target_click_contained
    assert result.gt_cutout_count == 1
    assert result.pred_cutout_count == 1
    assert result.passed


def test_evaluate_polygon_prediction_flags_wrong_clicked_component():
    case = Case(
        case_id="demo",
        image_width=12,
        image_height=8,
        gt_boundary=[(1, 1), (5, 1), (5, 5), (1, 5)],
        gt_cutouts=[],
        clicks=[Click(click_id="main", x=2, y=2)],
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="click_connected_polygon",
        track="pure_segmentation",
        boundary=[(7, 1), (11, 1), (11, 5), (7, 5)],
        cutouts=[],
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert result.iou == 0
    assert not result.target_click_contained
    assert not result.passed


def test_evaluate_polygon_prediction_reports_area_delta():
    case = Case(
        case_id="demo",
        image_width=10,
        image_height=10,
        gt_boundary=[(1, 1), (5, 1), (5, 5), (1, 5)],
        gt_cutouts=[],
        clicks=[],
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="semantic_mask",
        track="vlm_polygon",
        boundary=[(1, 1), (9, 1), (9, 5), (1, 5)],
        cutouts=[],
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert math.isclose(result.area_delta_pct, 1.0)


def test_evaluate_polygon_prediction_reports_square_feet_when_resolution_is_known():
    case = Case(
        case_id="demo",
        image_width=10,
        image_height=10,
        gt_boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
        gt_cutouts=[],
        clicks=[],
        meters_per_pixel=0.3048,
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="semantic_mask",
        track="vlm_polygon",
        boundary=[(0, 0), (5, 0), (5, 10), (0, 10)],
        cutouts=[],
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert math.isclose(result.gt_sqft, 100.0)
    assert math.isclose(result.pred_sqft, 50.0)


def test_evaluate_polygon_prediction_marks_invalid_polygon_as_failure():
    case = Case(
        case_id="demo",
        image_width=10,
        image_height=10,
        gt_boundary=[(1, 1), (9, 1), (9, 9), (1, 9)],
        gt_cutouts=[],
        clicks=[],
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="click_connected_polygon",
        track="vlm_polygon",
        boundary=[(1, 1), (9, 9)],
        cutouts=[],
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert not result.passed
    assert result.error == "invalid_polygon"


def test_evaluate_polygon_prediction_marks_empty_polygon_separately():
    case = Case(
        case_id="demo",
        image_width=10,
        image_height=10,
        gt_boundary=[(1, 1), (9, 1), (9, 9), (1, 9)],
        gt_cutouts=[],
        clicks=[],
    )
    prediction = PolygonPrediction(
        case_id="demo",
        task="click_connected_polygon",
        track="pure_segmentation",
        boundary=[],
        cutouts=[],
    )

    result = evaluate_polygon_prediction(case, prediction)

    assert not result.passed
    assert result.error == "empty_prediction"
