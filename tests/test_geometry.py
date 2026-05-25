from pavebench.geometry import (
    bbox_for_polygon,
    polygon_area,
    point_in_polygon,
    rasterize_polygon,
)


def test_polygon_area_subtracts_cutouts():
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    hole = [(2, 2), (4, 2), (4, 4), (2, 4)]

    assert polygon_area(outer, [hole]) == 96


def test_point_in_polygon_excludes_holes():
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    hole = [(2, 2), (4, 2), (4, 4), (2, 4)]

    assert point_in_polygon((1, 1), outer, [hole])
    assert not point_in_polygon((3, 3), outer, [hole])
    assert not point_in_polygon((11, 3), outer, [hole])


def test_rasterize_polygon_handles_cutout_pixels():
    outer = [(1, 1), (7, 1), (7, 7), (1, 7)]
    hole = [(3, 3), (5, 3), (5, 5), (3, 5)]

    mask = rasterize_polygon(outer, [hole], width=8, height=8)

    assert mask[1][1] == 1
    assert mask[3][3] == 0
    assert mask[0][0] == 0


def test_bbox_for_polygon_includes_holes():
    outer = [(5, 5), (8, 5), (8, 8), (5, 8)]
    hole = [(1, 2), (2, 2), (2, 3), (1, 3)]

    assert bbox_for_polygon(outer, [hole]) == (1, 2, 8, 8)
