from __future__ import annotations

from collections.abc import Sequence

Point = tuple[float, float]


def _closed_ring(ring: Sequence[Point]) -> list[Point]:
    points = [(float(x), float(y)) for x, y in ring]
    if len(points) < 3:
        return points
    if points[0] != points[-1]:
        points.append(points[0])
    return points


def _ring_area(ring: Sequence[Point]) -> float:
    points = _closed_ring(ring)
    if len(points) < 4:
        return 0.0
    area = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def polygon_area(boundary: Sequence[Point], cutouts: Sequence[Sequence[Point]] | None = None) -> float:
    """Return planar polygon area in pixel units, subtracting interior rings."""

    hole_area = sum(_ring_area(hole) for hole in cutouts or [])
    return max(0.0, _ring_area(boundary) - hole_area)


def point_in_ring(point: Point, ring: Sequence[Point]) -> bool:
    """Ray-casting point-in-ring test for image/pixel coordinates."""

    x, y = point
    points = _closed_ring(ring)
    inside = False
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if ((y0 > y) != (y1 > y)) and (x < (x1 - x0) * (y - y0) / ((y1 - y0) or 1e-12) + x0):
            inside = not inside
    return inside


def point_in_polygon(
    point: Point,
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None = None,
) -> bool:
    if not point_in_ring(point, boundary):
        return False
    return not any(point_in_ring(point, hole) for hole in cutouts or [])


def bbox_for_polygon(
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None = None,
) -> tuple[float, float, float, float]:
    all_points = list(boundary)
    for hole in cutouts or []:
        all_points.extend(hole)
    if not all_points:
        raise ValueError("Cannot compute bbox for empty polygon")
    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]
    return (min(xs), min(ys), max(xs), max(ys))


def rasterize_polygon(
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None,
    width: int,
    height: int,
) -> list[list[int]]:
    """Rasterize a polygon to a 0/1 mask using pixel centers."""

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    mask: list[list[int]] = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            row.append(1 if point_in_polygon((x + 0.5, y + 0.5), boundary, cutouts) else 0)
        mask.append(row)
    return mask
