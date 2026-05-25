from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .baselines.oracle import write_oracle_predictions
from .eval import evaluate_polygon_prediction
from .importers.human_trace import create_case_from_trace
from .manifest import load_manifest
from .reporting import summarize_results
from .schemas import PolygonPrediction, load_case_from_metadata


def _points(raw_points: list[list[float]]) -> list[tuple[float, float]]:
    return [(float(point[0]), float(point[1])) for point in raw_points]


def _prediction_from_json(data: dict) -> PolygonPrediction:
    return PolygonPrediction(
        case_id=str(data["caseId"]),
        task=str(data["task"]),
        track=data["track"],
        boundary=_points(data["boundary"]),
        cutouts=[_points(cutout) for cutout in data.get("cutouts", [])],
        latency_ms=data.get("latencyMs"),
        cost_usd=data.get("costUsd"),
        metadata=dict(data.get("metadata", {})),
    )


def _score(args: argparse.Namespace) -> int:
    case = load_case_from_metadata(args.case)
    predictions_path = Path(args.predictions)
    results = []
    for line in predictions_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        prediction = _prediction_from_json(json.loads(line))
        if prediction.case_id != case.case_id:
            continue
        results.append(asdict(evaluate_polygon_prediction(case, prediction)))

    report = {
        "summary": {
            "cases": len(results),
            "passes": sum(1 for result in results if result["passed"]),
            "meanIou": sum(result["iou"] for result in results) / len(results) if results else 0,
        },
        "results": results,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


def _read_predictions(path: str | Path) -> list[PolygonPrediction]:
    predictions: list[PolygonPrediction] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            predictions.append(_prediction_from_json(json.loads(line)))
    return predictions


def _report(results: list[dict]) -> dict:
    return {
        "summary": summarize_results(results),
        "results": results,
    }


def _score_manifest(args: argparse.Namespace) -> int:
    rows = load_manifest(args.manifest)
    predictions = _read_predictions(args.predictions)
    results = []
    for row in rows:
        for prediction in predictions:
            if prediction.case_id != row.case_id:
                continue
            if row.tasks and prediction.task not in row.tasks:
                continue
            results.append(asdict(evaluate_polygon_prediction(row.case, prediction)))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_report(results), indent=2) + "\n", encoding="utf-8")
    return 0


def _oracle(args: argparse.Namespace) -> int:
    write_oracle_predictions(args.manifest, args.out)
    return 0


def _case_from_trace(args: argparse.Namespace) -> int:
    create_case_from_trace(args.trace, args.out_dir, args.case_id, args.image_width, args.image_height)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pavebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score = subparsers.add_parser("score", help="Score prediction JSONL against one case metadata file")
    score.add_argument("--case", required=True, help="Path to case metadata.json")
    score.add_argument("--predictions", required=True, help="Path to prediction JSONL")
    score.add_argument("--out", required=True, help="Path to write JSON report")
    score.set_defaults(func=_score)

    score_manifest = subparsers.add_parser("score-manifest", help="Score prediction JSONL against a manifest")
    score_manifest.add_argument("--manifest", required=True, help="Path to manifest JSONL")
    score_manifest.add_argument("--predictions", required=True, help="Path to prediction JSONL")
    score_manifest.add_argument("--out", required=True, help="Path to write JSON report")
    score_manifest.set_defaults(func=_score_manifest)

    oracle = subparsers.add_parser("oracle", help="Write oracle predictions from manifest gold geometry")
    oracle.add_argument("--manifest", required=True, help="Path to manifest JSONL")
    oracle.add_argument("--out", required=True, help="Path to write prediction JSONL")
    oracle.set_defaults(func=_oracle)

    trace = subparsers.add_parser("case-from-trace", help="Create review-guide case files from a human trace GeoJSON")
    trace.add_argument("--trace", required=True, help="Path to human trace GeoJSON")
    trace.add_argument("--case-id", required=True, help="Case id for the generated benchmark case")
    trace.add_argument("--image-width", required=True, type=int, help="Benchmark image width in pixels")
    trace.add_argument("--image-height", required=True, type=int, help="Benchmark image height in pixels")
    trace.add_argument("--out-dir", required=True, help="Directory to write metadata.json and gold.geojson")
    trace.set_defaults(func=_case_from_trace)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
