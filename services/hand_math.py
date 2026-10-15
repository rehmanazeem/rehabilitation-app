"""Pure landmark maths for the exercise metrics.

No camera, MediaPipe or OpenCV imports here: every function takes objects with
normalized ``x``/``y`` attributes (MediaPipe landmarks or any stand-in), so the
maths can be unit-tested with synthetic points.
"""
import math
from typing import Protocol

import numpy as np

# Landmark indices (MediaPipe Hands, 21-point model)
THUMB_TIP, PINKY_TIP = 4, 20
INDEX_MCP, INDEX_PIP, INDEX_DIP = 5, 6, 7

# Thumb-tip to pinky-tip distance (normalized) mapped onto 0-100 % openness
OPEN_DIST_RANGE = (0.05, 0.4)
# Openness below this percentage is reported as "Closed"
CLOSED_BELOW = 65


class Point(Protocol):
    """Anything with normalized image coordinates (e.g. a MediaPipe landmark)."""
    x: float
    y: float


def distance(p1: Point, p2: Point) -> float:
    """Return the 2D Euclidean distance between two normalized landmarks."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def interior_angle(a: Point, b: Point, c: Point) -> float:
    """Return the interior angle (degrees, 0-180) at vertex ``b``."""
    ang = math.degrees(math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x))
    ang = abs(ang)
    if ang > 180:
        ang = 360 - ang
    return ang


def flexion_reading(lms: list[Point]) -> tuple[int, str]:
    """Index-finger flexion (landmarks 5-6-7) as ``(degrees, status_text)``."""
    value = int(interior_angle(lms[INDEX_MCP], lms[INDEX_PIP], lms[INDEX_DIP]))
    return value, f"Flexion: {value}°"


def open_close_reading(lms: list[Point]) -> tuple[int, str]:
    """Hand openness (thumb tip to pinky tip) as ``(percent, status_text)``."""
    dist = distance(lms[THUMB_TIP], lms[PINKY_TIP])
    value = int(np.interp(dist, OPEN_DIST_RANGE, [0, 100]))
    state = "Closed" if value < CLOSED_BELOW else "Open"
    return value, f"Hand: {state} ({value}%)"
