import json

from pavebench.baselines.empty import write_empty_predictions


def test_write_empty_predictions_emits_one_prediction_per_manifest_task(tmp_path):
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
                "tasks": ["semantic_mask", "click_connected_polygon"],
                "metadataPath": "cases/demo/metadata.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "empty.jsonl"

    write_empty_predictions(manifest_path, out_path)

    predictions = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert [prediction["task"] for prediction in predictions] == ["semantic_mask", "click_connected_polygon"]
    assert all(prediction["boundary"] == [] for prediction in predictions)
    assert all(prediction["metadata"]["baseline"] == "empty" for prediction in predictions)
