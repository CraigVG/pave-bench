import json

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
    assert report["summary"]["cases"] == 1
    assert report["summary"]["passes"] == 1
    assert report["summary"]["meanIou"] == 1


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
