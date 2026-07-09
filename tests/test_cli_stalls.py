import json

from pavebench.cli import main


def _write_stall_case(case_path):
    case_path.write_text(
        json.dumps(
            {
                "caseId": "lot",
                "imageSize": {"width": 100, "height": 100},
                "resolutionMetersPerPixel": 0.1,
                "imagery": {"nativeGsdMeters": 0.1},
                "gold": {"boundary": [[0, 0], [100, 0], [100, 100], [0, 100]], "cutouts": []},
                "stallGold": {
                    "count": 4,
                    "matchRadiusMeters": 2.7,
                    "markers": [[20, 20], [40, 20], [60, 20], [80, 20]],
                },
            }
        ),
        encoding="utf-8",
    )


def test_cli_scores_stall_count_task(tmp_path):
    case_path = tmp_path / "metadata.json"
    _write_stall_case(case_path)
    predictions = tmp_path / "pred.jsonl"
    predictions.write_text(
        json.dumps(
            {
                "caseId": "lot",
                "task": "stall_count",
                "track": "hybrid_production",
                "count": 4,
                "stalls": [[21, 20], [41, 20], [61, 20], [81, 20]],
                "latencyMs": 1200,
                "costUsd": 0.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "score.json"
    assert main(["score", "--case", str(case_path), "--predictions", str(predictions), "--out", str(out)]) == 0

    report = json.loads(out.read_text(encoding="utf-8"))
    assert "stallSummary" in report
    stall = report["stallSummary"]
    assert stall["cases"] == 1
    assert stall["passes"] == 1
    assert stall["meanPrecision"] == 1.0
    assert stall["medianLocationErrorM"] is not None
    assert report["stallResults"][0]["pred_count"] == 4


def test_cli_manifest_flags_missing_stall_prediction(tmp_path):
    case_dir = tmp_path / "cases" / "lot"
    case_dir.mkdir(parents=True)
    _write_stall_case(case_dir / "metadata.json")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "caseId": "lot",
                "split": "dev",
                "tasks": ["stall_count"],
                "metadataPath": "cases/lot/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    predictions = tmp_path / "pred.jsonl"
    predictions.write_text("", encoding="utf-8")
    out = tmp_path / "score.json"
    assert main(["score-manifest", "--manifest", str(manifest), "--predictions", str(predictions), "--out", str(out)]) == 0

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["stallSummary"]["missingPredictions"] == 1
    assert report["stallResults"][0]["error"] == "missing_prediction"
