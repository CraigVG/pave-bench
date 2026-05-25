import json

from pavebench.schemas import Case, load_case_from_metadata


def test_load_case_from_metadata_preserves_human_trace_source(tmp_path):
    metadata = {
        "caseId": "demo_human_trace",
        "imageSize": {"width": 10, "height": 10},
        "labelSource": {
            "kind": "human_traced_paved_surface",
            "role": "guide",
            "reviewStatus": "needs_gold_review",
        },
        "gold": {
            "boundary": [[1, 1], [9, 1], [9, 9], [1, 9]],
            "cutouts": [],
        },
        "clicks": [{"id": "main", "x": 3, "y": 3}],
    }
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")

    case = load_case_from_metadata(path)

    assert isinstance(case, Case)
    assert case.case_id == "demo_human_trace"
    assert case.label_source["kind"] == "human_traced_paved_surface"
    assert case.label_source["role"] == "guide"
    assert case.clicks[0].click_id == "main"
