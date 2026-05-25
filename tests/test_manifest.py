import json

from pavebench.manifest import load_manifest


def test_load_manifest_resolves_metadata_paths(tmp_path):
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
                "tags": ["toy"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = load_manifest(manifest_path)

    assert len(rows) == 1
    assert rows[0].case.case_id == "demo"
    assert rows[0].tasks == ["click_connected_polygon"]
    assert rows[0].metadata_path == case_dir / "metadata.json"
