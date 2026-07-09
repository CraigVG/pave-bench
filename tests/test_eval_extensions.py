import math

from pavebench.eval import cutout_recovery, evaluate_polygon_prediction
from pavebench.schemas import Case, PolygonPrediction


def _case_with_cutouts(cutouts, **overrides):
    base = dict(
        case_id="lot",
        image_width=100,
        image_height=100,
        gt_boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
        gt_cutouts=cutouts,
    )
    base.update(overrides)
    return Case(**base)


def test_cutout_recovery_is_full_when_no_gold_cutouts():
    found, expected, recovery = cutout_recovery([], [])
    assert (found, expected) == (0, 0)
    assert recovery == 1.0


def test_cutout_recovery_area_weighted():
    big = [(10, 10), (50, 10), (50, 50), (10, 50)]  # 1600 px^2
    small = [(80, 80), (85, 80), (85, 85), (80, 85)]  # 25 px^2
    # Predict only the big island.
    found, expected, recovery = cutout_recovery([big, small], [big])
    assert expected == 2
    assert found == 1
    # Recovered area is dominated by the big island: ~1600 / 1625.
    assert recovery > 0.95


def test_cutout_recovery_misses_when_prediction_offset():
    island = [(10, 10), (30, 10), (30, 30), (10, 30)]
    far = [(70, 70), (90, 70), (90, 90), (70, 90)]
    found, expected, recovery = cutout_recovery([island], [far])
    assert (found, expected) == (0, 1)
    assert recovery == 0.0


def test_eval_result_carries_gsd_tier_latency_cost_and_split():
    case = _case_with_cutouts([], meters_per_pixel=0.06, native_meters_per_pixel=0.06, split="dev")
    prediction = PolygonPrediction(
        case_id="lot",
        task="semantic_mask",
        track="pure_segmentation",
        boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
        latency_ms=4200,
        cost_usd=0.018,
    )
    result = evaluate_polygon_prediction(case, prediction)
    assert result.gsd_tier == "<=8cm"
    assert result.latency_ms == 4200
    assert math.isclose(result.cost_usd, 0.018)
    assert result.split == "dev"
    assert result.cutout_recovery == 1.0


def test_native_gsd_drives_tier_even_when_exported_finer():
    # Exported to 6 cm/px but the honest native resolution is 15.2 cm.
    case = _case_with_cutouts([], meters_per_pixel=0.06, native_meters_per_pixel=0.152)
    prediction = PolygonPrediction(
        case_id="lot",
        task="semantic_mask",
        track="pure_segmentation",
        boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
    )
    result = evaluate_polygon_prediction(case, prediction)
    assert result.gsd_tier == ">15cm"
