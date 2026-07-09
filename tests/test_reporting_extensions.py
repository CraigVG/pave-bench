from pavebench.reporting import latency_class, summarize_results, summarize_stall_results


def test_latency_class_thresholds():
    assert latency_class(9_000) == "INSTANT"
    assert latency_class(10_000) == "INSTANT"
    assert latency_class(30_000) == "FAST"
    assert latency_class(90_000) == "BATCH"
    assert latency_class(None) == "unknown"


def _area_row(**overrides):
    row = {
        "track": "pure_segmentation",
        "iou": 0.9,
        "area_delta_pct": 0.05,
        "passed": True,
        "gt_sqft": 1000.0,
        "pred_sqft": 1050.0,
        "cutout_recovery": 0.8,
        "cutout_expected": 3,
        "latency_ms": 4000,
        "cost_usd": 0.02,
        "gsd_tier": "<=8cm",
        "split": "dev",
    }
    row.update(overrides)
    return row


def test_area_summary_reports_latency_class_gsd_tier_and_split():
    results = [
        _area_row(),
        _area_row(gsd_tier=">15cm", latency_ms=80_000, passed=False, area_delta_pct=0.20),
    ]
    summary = summarize_results(results)
    assert summary["cases"] == 2
    # p95 latency of {4000, 80000} nearest-rank -> 80000 -> BATCH.
    assert summary["latencyClass"] == "BATCH"
    assert summary["medianSqftDelta"] == 50.0
    assert summary["meanCutoutRecovery"] == 0.8
    assert set(summary["byGsdTier"]) == {"<=8cm", ">15cm"}
    assert summary["byGsdTier"]["<=8cm"]["latencyClass"] == "INSTANT"
    assert summary["bySplit"]["dev"]["cases"] == 2


def test_stall_summary_aggregates_count_and_location_metrics():
    results = [
        {
            "track": "hybrid_production",
            "abs_count_error_pct": 5.0,
            "count_error_pct": 5.0,
            "precision": 0.9,
            "recall": 0.8,
            "f1": 0.85,
            "median_location_error_m": 1.3,
            "passed": True,
            "latency_ms": 1000,
            "cost_usd": 0.0,
            "gsd_tier": "<=8cm",
            "split": "dev",
        },
        {
            "track": "hybrid_production",
            "abs_count_error_pct": 15.0,
            "count_error_pct": -15.0,
            "precision": None,
            "recall": None,
            "f1": None,
            "median_location_error_m": None,
            "passed": False,
            "latency_ms": 2000,
            "cost_usd": 0.0,
            "gsd_tier": ">15cm",
            "split": "dev",
        },
    ]
    summary = summarize_stall_results(results)
    assert summary["cases"] == 2
    assert summary["passes"] == 1
    assert summary["medianAbsCountErrorPct"] == 10.0
    assert summary["casesWithMarkers"] == 1
    assert summary["meanPrecision"] == 0.9
    assert summary["medianLocationErrorM"] == 1.3
    assert set(summary["byGsdTier"]) == {"<=8cm", ">15cm"}
