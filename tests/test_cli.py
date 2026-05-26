import json
import pytest

from pavebench.cli import main


def test_cli_scores_prediction_jsonl(tmp_path):
    case_path = tmp_path / "metadata.json"
    predictions_path = tmp_path / "predictions.jsonl"
    out_path = tmp_path / "scores.json"

    case_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [],
                },
                "clicks": [{"id": "main", "x": 2, "y": 2}],
            }
        ),
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "task": "click_connected_polygon",
                "track": "vlm_polygon",
                "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                "cutouts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["score", "--case", str(case_path), "--predictions", str(predictions_path), "--out", str(out_path)]) == 0

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["summary"]["cases"] == 1
    assert report["summary"]["passes"] == 1
    assert report["results"][0]["iou"] == 1


def test_cli_scores_manifest_jsonl(tmp_path):
    case_dir = tmp_path / "cases" / "demo"
    case_dir.mkdir(parents=True)
    case_path = case_dir / "metadata.json"
    predictions_path = tmp_path / "predictions.jsonl"
    manifest_path = tmp_path / "manifest.jsonl"
    out_path = tmp_path / "scores.json"

    case_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [],
                },
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "split": "dev",
                "tasks": ["semantic_mask", "click_connected_polygon"],
                "metadataPath": "cases/demo/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "task": "click_connected_polygon",
                "track": "vlm_polygon",
                "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                "cutouts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["score-manifest", "--manifest", str(manifest_path), "--predictions", str(predictions_path), "--out", str(out_path)]) == 0

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["summary"]["cases"] == 2
    assert report["summary"]["passes"] == 1
    assert report["summary"]["missingPredictions"] == 1
    assert report["summary"]["meanIou"] == 0.5


def test_cli_refuses_guide_cases_without_explicit_allow_guide(tmp_path):
    case_path = tmp_path / "metadata.json"
    predictions_path = tmp_path / "predictions.jsonl"
    out_path = tmp_path / "scores.json"

    case_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "labelSource": {"role": "guide", "reviewStatus": "needs_gold_review"},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [],
                },
            }
        ),
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "task": "click_connected_polygon",
                "track": "vlm_polygon",
                "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                "cutouts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="needs gold review"):
        main(["score", "--case", str(case_path), "--predictions", str(predictions_path), "--out", str(out_path)])


def test_cli_can_score_guide_cases_when_explicitly_allowed(tmp_path):
    case_path = tmp_path / "metadata.json"
    predictions_path = tmp_path / "predictions.jsonl"
    out_path = tmp_path / "scores.json"

    case_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "labelSource": {"role": "guide", "reviewStatus": "needs_gold_review"},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [],
                },
            }
        ),
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "task": "click_connected_polygon",
                "track": "vlm_polygon",
                "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                "cutouts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["score", "--allow-guide", "--case", str(case_path), "--predictions", str(predictions_path), "--out", str(out_path)]) == 0
    assert json.loads(out_path.read_text(encoding="utf-8"))["summary"]["passes"] == 1


def test_cli_reports_missing_manifest_predictions_as_failures(tmp_path):
    case_dir = tmp_path / "cases" / "demo"
    case_dir.mkdir(parents=True)
    (case_dir / "metadata.json").write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [],
                },
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "split": "dev",
                "tasks": ["click_connected_polygon"],
                "metadataPath": "cases/demo/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    predictions_path = tmp_path / "predictions.jsonl"
    predictions_path.write_text("", encoding="utf-8")
    out_path = tmp_path / "scores.json"

    assert main(["score-manifest", "--manifest", str(manifest_path), "--predictions", str(predictions_path), "--out", str(out_path)]) == 0

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["summary"]["cases"] == 1
    assert report["summary"]["passes"] == 0
    assert report["summary"]["missingPredictions"] == 1
    assert report["results"][0]["error"] == "missing_prediction"


def test_cli_writes_oracle_predictions(tmp_path):
    case_dir = tmp_path / "cases" / "demo"
    case_dir.mkdir(parents=True)
    (case_dir / "metadata.json").write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {"boundary": [[1, 1], [9, 1], [9, 9], [1, 9]], "cutouts": []},
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "split": "dev",
                "tasks": ["click_connected_polygon"],
                "metadataPath": "cases/demo/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "oracle.jsonl"

    assert main(["oracle", "--manifest", str(manifest_path), "--out", str(out_path)]) == 0

    assert json.loads(out_path.read_text(encoding="utf-8"))["caseId"] == "demo"


def test_cli_writes_empty_baseline_predictions(tmp_path):
    case_dir = tmp_path / "cases" / "demo"
    case_dir.mkdir(parents=True)
    (case_dir / "metadata.json").write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {"boundary": [[1, 1], [9, 1], [9, 9], [1, 9]], "cutouts": []},
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "caseId": "demo",
                "split": "dev",
                "tasks": ["click_connected_polygon"],
                "metadataPath": "cases/demo/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "empty.jsonl"

    assert main(["empty", "--manifest", str(manifest_path), "--out", str(out_path)]) == 0

    prediction = json.loads(out_path.read_text(encoding="utf-8"))
    assert prediction["caseId"] == "demo"
    assert prediction["boundary"] == []
