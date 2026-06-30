import json

from pavebench.geometry import point_in_polygon
from pavebench.importers.human_trace import create_case_from_trace
from pavebench.schemas import load_case_from_metadata


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
    assert metadata["guide"]["boundary"] == [[1.0, 1.0], [9.0, 1.0], [9.0, 9.0], [1.0, 9.0]]
    assert metadata["guide"]["cutouts"] == [[[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0]]]
    assert "gold" not in metadata
    assert (out_dir / "guide.geojson").exists()
    assert not (out_dir / "gold.geojson").exists()


def _square_with_hole_trace(tmp_path):
    trace_path = tmp_path / "trace.geojson"
    trace_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"measurementId": "m_geo"},
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
    return trace_path


def test_auto_click_falls_inside_polygon_and_outside_hole(tmp_path):
    out_dir = tmp_path / "case"
    create_case_from_trace(
        trace_path=_square_with_hole_trace(tmp_path),
        out_dir=out_dir,
        case_id="geo_case",
        image_width=10,
        image_height=10,
    )
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert len(metadata["clicks"]) == 1
    click = metadata["clicks"][0]
    boundary = [[1, 1], [9, 1], [9, 9], [1, 9]]
    hole = [[4, 4], [6, 4], [6, 6], [4, 6]]
    # The centroid (5,5) is inside the hole, so the importer must pick a real interior point.
    assert point_in_polygon((click["x"], click["y"]), boundary, [hole])


def test_carries_explicit_clicks_and_geo_provenance(tmp_path):
    out_dir = tmp_path / "case"
    create_case_from_trace(
        trace_path=_square_with_hole_trace(tmp_path),
        out_dir=out_dir,
        case_id="geo_case",
        image_width=1280,
        image_height=1024,
        clicks=[{"id": "main", "x": 2.0, "y": 2.0}],
        coordinate_space="geographic_wgs84",
        bounds={"north": 1.0, "south": 0.0, "east": 1.0, "west": 0.0},
        meters_per_pixel=0.3,
        extra_source={"imagerySource": "google-static-maps"},
        extra_label_source={"scope": "full_lot"},
    )
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["clicks"] == [{"id": "main", "x": 2.0, "y": 2.0}]
    assert metadata["coordinateSpace"] == "geographic_wgs84"
    assert metadata["bounds"]["north"] == 1.0
    assert metadata["resolutionMetersPerPixel"] == 0.3
    assert metadata["source"]["imagerySource"] == "google-static-maps"
    assert metadata["labelSource"]["scope"] == "full_lot"
    # Still loads through the schema layer with the extra provenance keys present.
    case = load_case_from_metadata(out_dir / "metadata.json")
    assert case.clicks[0].click_id == "main"
    assert case.meters_per_pixel == 0.3
    assert case.label_source["role"] == "guide"


def test_empty_clicks_when_requested(tmp_path):
    out_dir = tmp_path / "case"
    create_case_from_trace(
        trace_path=_square_with_hole_trace(tmp_path),
        out_dir=out_dir,
        case_id="geo_case",
        image_width=10,
        image_height=10,
        clicks=[],
    )
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["clicks"] == []
