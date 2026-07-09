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


def ring_area(ring: Sequence[Point]) -> float:
    """Public accessor for the absolute planar area of a single ring."""

    return _ring_area(ring)


def polygon_area(boundary: Sequence[Point], cutouts: Sequence[Sequence[Point]] | None = None) -> float:
    """Return planar polygon area in pixel units, subtracting interior rings."""

    hole_area = sum(_ring_area(hole) for hole in cutouts or [])
    return max(0.0, _ring_area(boundary) - hole_area)


def covered_fraction(
    target: Sequence[Point],
    covers: Sequence[Sequence[Point]],
    grid_cap: int = 160,
) -> float:
    """Fraction of ``target``'s area that falls inside the union of ``covers``.

    Samples a capped grid over ``target``'s bounding box so the cost is bounded
    regardless of image size (real ortho cases are thousands of pixels wide).
    Used for area-weighted cutout-recovery scoring.
    """

    target = [(float(x), float(y)) for x, y in target]
    if len(target) < 3 or not covers:
        return 0.0
    min_x, min_y, max_x, max_y = bbox_for_polygon(target)
    span_x = max(max_x - min_x, 1e-9)
    span_y = max(max_y - min_y, 1e-9)
    steps_x = max(1, min(grid_cap, int(round(span_x))))
    steps_y = max(1, min(grid_cap, int(round(span_y))))
    inside_target = 0
    inside_both = 0
    for i in range(steps_x):
        x = min_x + span_x * (i + 0.5) / steps_x
        for j in range(steps_y):
            y = min_y + span_y * (j + 0.5) / steps_y
            if not point_in_ring((x, y), target):
                continue
            inside_target += 1
            if any(point_in_ring((x, y), cover) for cover in covers):
                inside_both += 1
    if inside_target == 0:
        return 0.0
    return inside_both / inside_target


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


def _point_to_segment_distance(point: Point, a: Point, b: Point) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _min_edge_distance(
    point: Point,
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None = None,
) -> float:
    best = float("inf")
    rings = [list(boundary)] + [list(hole) for hole in cutouts or []]
    for ring in rings:
        closed = _closed_ring(ring)
        for a, b in zip(closed, closed[1:]):
            best = min(best, _point_to_segment_distance(point, a, b))
    return best


def interior_point(
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None = None,
    grid: int = 24,
) -> Point:
    """Return a point guaranteed to lie inside the polygon (outside any cutout).

    Coordinate-system agnostic — works for pixel or geographic (lng, lat) rings.
    Tries the vertex centroid first, then a grid-scan pole-of-inaccessibility
    (the interior sample farthest from any edge) for concave or holed lots.
    """

    pts = [(float(x), float(y)) for x, y in boundary]
    if len(pts) < 3:
        raise ValueError("Cannot find interior point of a degenerate polygon")

    centroid = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    if point_in_polygon(centroid, boundary, cutouts):
        return centroid

    min_x, min_y, max_x, max_y = bbox_for_polygon(boundary, cutouts)
    best: Point | None = None
    best_dist = -1.0
    for i in range(grid):
        for j in range(grid):
            x = min_x + (max_x - min_x) * (i + 0.5) / grid
            y = min_y + (max_y - min_y) * (j + 0.5) / grid
            if not point_in_polygon((x, y), boundary, cutouts):
                continue
            dist = _min_edge_distance((x, y), boundary, cutouts)
            if dist > best_dist:
                best_dist = dist
                best = (x, y)
    if best is None:
        # Degenerate sliver the grid missed; fall back to the first edge midpoint.
        return ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
    return best


def rasterize_polygon(
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None,
    width: int,
    height: int,
) -> list[list[int]]:
    """Rasterize a polygon to a 0/1 mask using pixel centers (pure Python).

    Correct and dependency-free but O(width*height*edges); use
    :func:`rasterize_polygon_image` for real ortho-sized cases.
    """

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    mask: list[list[int]] = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            row.append(1 if point_in_polygon((x + 0.5, y + 0.5), boundary, cutouts) else 0)
        mask.append(row)
    return mask


def rasterize_polygon_image(
    boundary: Sequence[Point],
    cutouts: Sequence[Sequence[Point]] | None,
    width: int,
    height: int,
):
    """Rasterize a polygon-with-holes to a 1-bit PIL image (C-fast).

    Real ortho cases are thousands of pixels wide, where the pure-Python
    rasterizer takes tens of seconds; this fills via ImageDraw instead.
    """

    from PIL import Image, ImageDraw

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    image = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(image)
    boundary_pts = [(float(x), float(y)) for x, y in boundary]
    if len(boundary_pts) >= 3:
        draw.polygon(boundary_pts, fill=1)
    for hole in cutouts or []:
        hole_pts = [(float(x), float(y)) for x, y in hole]
        if len(hole_pts) >= 3:
            draw.polygon(hole_pts, fill=0)
    return image


def mask_to_image(mask: Sequence[Sequence[int]], width: int, height: int):
    """Convert a 0/1 list-of-rows mask into a 1-bit PIL image."""

    from PIL import Image

    image = Image.new("1", (width, height), 0)
    image.putdata([1 if value else 0 for row in mask for value in row])
    return image


def _mask_count(image) -> int:
    return sum(image.convert("L").histogram()[128:])


def mask_image_iou(truth, pred) -> float:
    """IoU between two 1-bit PIL masks via C-backed boolean ops."""

    from PIL import ImageChops

    intersection = _mask_count(ImageChops.logical_and(truth, pred))
    union = _mask_count(ImageChops.logical_or(truth, pred))
    return 1.0 if union == 0 else intersection / union
