from pavebench.reporting import summarize_results


def test_summarize_results_groups_by_track_and_reports_p90_area_delta():
    results = [
        {"track": "vlm_polygon", "iou": 0.9, "area_delta_pct": 0.01, "passed": True},
        {"track": "vlm_polygon", "iou": 0.8, "area_delta_pct": 0.20, "passed": False},
        {"track": "pure_segmentation", "iou": 0.7, "area_delta_pct": 0.10, "passed": False},
    ]

    summary = summarize_results(results)

    assert summary["cases"] == 3
    assert summary["passes"] == 1
    assert summary["meanIou"] == 0.8
    assert summary["p90AreaDeltaPct"] == 0.20
    assert summary["byTrack"]["vlm_polygon"]["cases"] == 2
    assert summary["byTrack"]["vlm_polygon"]["passes"] == 1
    assert summary["byTrack"]["pure_segmentation"]["meanIou"] == 0.7
