"""Unit tests for services.hand_math using synthetic landmarks."""
import math
from types import SimpleNamespace as P

import pytest

from services.hand_math import distance, flexion_reading, interior_angle, open_close_reading


def hand(**pts):
    """21 origin landmarks with overrides, e.g. hand(i4=P(x=0, y=0))."""
    lms = [P(x=0.0, y=0.0) for _ in range(21)]
    for k, v in pts.items():
        lms[int(k[1:])] = v
    return lms


def test_distance():
    assert distance(P(x=0, y=0), P(x=0.3, y=0.4)) == pytest.approx(0.5)


@pytest.mark.parametrize("c, expected", [
    (P(x=2, y=0), 180),   # straight finger
    (P(x=1, y=1), 90),    # right angle
    (P(x=0, y=0), 0),     # fully folded back
])
def test_interior_angle(c, expected):
    assert interior_angle(P(x=0, y=0), P(x=1, y=0), c) == pytest.approx(expected)


def test_interior_angle_wraps_above_180():
    # raw difference of 270 deg must fold to 90
    a, b, c = P(x=0, y=-1), P(x=0, y=0), P(x=-1, y=0)
    assert interior_angle(a, b, c) == pytest.approx(90)


def test_flexion_reading_truncates_and_formats():
    ang = math.radians(100.9)
    lms = hand(i5=P(x=1, y=0), i6=P(x=0, y=0), i7=P(x=math.cos(ang), y=math.sin(ang)))
    assert flexion_reading(lms) == (100, "Flexion: 100°")


@pytest.mark.parametrize("dist, value, state", [
    (0.02, 0, "Closed"),     # clamped below range
    (0.23, 51, "Closed"),    # inside 0.05-0.4
    (0.2825, 66, "Open"),
    (0.9, 100, "Open"),      # clamped above range
])
def test_open_close_reading(dist, value, state):
    lms = hand(i4=P(x=0, y=0), i20=P(x=dist, y=0))
    assert open_close_reading(lms) == (value, f"Hand: {state} ({value}%)")
