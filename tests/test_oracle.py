import json

from pavebench.baselines.oracle import write_oracle_predictions


def test_write_oracle_predictions_uses_gold_geometry(tmp_path):
    case_dir = tmp_path / "cases" / "demo"
    case_dir.mkdir(parents=True)
    (case_dir / "metadata.json").write_text(
        json.dumps(
            {
                "caseId": "demo",
                "imageSize": {"width": 10, "height": 10},
                "gold": {
                    "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
                    "cutouts": [[[4, 4], [6, 4], [6, 6], [4, 6]]],
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
    out_path = tmp_path / "oracle.jsonl"

    write_oracle_predictions(manifest_path, out_path)

    prediction = json.loads(out_path.read_text(encoding="utf-8"))
    assert prediction["caseId"] == "demo"
    assert prediction["track"] == "hybrid_production"
    assert prediction["boundary"] == [[1.0, 1.0], [9.0, 1.0], [9.0, 9.0], [1.0, 9.0]]
    assert prediction["cutouts"] == [[[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0]]]
