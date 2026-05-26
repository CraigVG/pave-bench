from __future__ import annotations

from collections import defaultdict
from typing import Any


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 10) if values else 0.0


def _percentile_nearest_rank(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    rank = max(1, round((percentile / 100) * len(sorted_values)))
    return sorted_values[min(len(sorted_values) - 1, rank - 1)]


def _summarize_group(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cases": len(results),
        "passes": sum(1 for result in results if result["passed"]),
        "missingPredictions": sum(1 for result in results if result.get("error") == "missing_prediction"),
        "emptyPredictions": sum(1 for result in results if result.get("error") == "empty_prediction"),
        "invalidPolygons": sum(1 for result in results if result.get("error") == "invalid_polygon"),
        "meanIou": _mean([float(result["iou"]) for result in results]),
        "meanAreaDeltaPct": _mean([float(result["area_delta_pct"]) for result in results]),
        "p90AreaDeltaPct": _percentile_nearest_rank([float(result["area_delta_pct"]) for result in results], 90),
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize_group(results)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        groups[str(result.get("track", "unknown"))].append(result)
    summary["byTrack"] = {track: _summarize_group(track_results) for track, track_results in sorted(groups.items())}
    return summary
