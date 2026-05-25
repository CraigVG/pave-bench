import json

from pavebench.importers.human_trace import create_case_from_trace


def test_create_case_from_trace_marks_trace_as_review_guide(tmp_path):
    trace_path = tmp_path / "trace.geojson"
    trace_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"sourceMeasurementId": "m_123"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[1, 1], [9, 1], [9, 9], [1, 9], [1, 1]],
                                [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]],
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "case"

    create_case_from_trace(
        trace_path=trace_path,
        out_dir=out_dir,
        case_id="human_trace_case",
        image_width=10,
        image_height=10,
    )

    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["caseId"] == "human_trace_case"
    assert metadata["labelSource"]["kind"] == "human_traced_paved_surface"
    assert metadata["labelSource"]["role"] == "guide"
    assert metadata["labelSource"]["reviewStatus"] == "needs_gold_review"
    assert metadata["labelSource"]["sourceMeasurementId"] == "m_123"
    assert metadata["gold"]["boundary"] == [[1.0, 1.0], [9.0, 1.0], [9.0, 9.0], [1.0, 9.0]]
    assert metadata["gold"]["cutouts"] == [[[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0]]]
    assert (out_dir / "gold.geojson").exists()
