"""Independent rigid-body oracle: rotate all 8 vertices around a bottom edge."""

from __future__ import annotations
import itertools
import random
import math
from core.constants import Action
from core.state import State
from core.rules import step
from tests.conftest import make_level


def physical_roll(cells, action):
    x0 = min(c for r, c in cells)
    z0 = min(r for r, c in cells)
    dx = max(c for r, c in cells) - x0 + 1
    dz = max(r for r, c in cells) - z0 + 1
    dy = 2 if len(cells) == 1 else 1
    vertices = list(itertools.product((x0, x0 + dx), (0, dy), (z0, z0 + dz)))
    # Axis uses x,y,z with y upwards; no orientation transition table.
    if action in (Action.LEFT, Action.RIGHT):
        pivot = (x0 if action == Action.LEFT else x0 + dx, 0, z0)
        axis = (0, 0, 1)
        angle = math.pi / 2 if action == Action.LEFT else -math.pi / 2
    else:
        pivot = (x0, 0, z0 if action == Action.UP else z0 + dz)
        axis = (1, 0, 0)
        angle = -math.pi / 2 if action == Action.UP else math.pi / 2
    result = []
    for vertex in vertices:
        v = tuple(a - b for a, b in zip(vertex, pivot))
        u = axis
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        dot = sum(a * b for a, b in zip(u, v))
        result.append(
            tuple(
                pivot[i]
                + v[i] * math.cos(angle)
                + cross[i] * math.sin(angle)
                + u[i] * dot * (1 - math.cos(angle))
                for i in range(3)
            )
        )
    lo = [round(min(v[i] for v in result)) for i in range(3)]
    hi = [round(max(v[i] for v in result)) for i in range(3)]
    assert lo[1] == 0
    return tuple((r, c) for r in range(lo[2], hi[2]) for c in range(lo[0], hi[0]))


def test_3000_rigid_body_rolls():
    rng = random.Random(739)
    for _ in range(3000):
        r, c = rng.randrange(1, 9), rng.randrange(1, 9)
        orientation = rng.randrange(3)
        cells = (
            ((r, c),)
            if orientation == 0
            else ((r, c), (r, c + 1))
            if orientation == 1
            else ((r, c), (r + 1, c))
        )
        board = [["#" if rng.random() > 0.2 else "." for _ in range(12)] for _ in range(12)]
        for a, b in cells:
            board[a][b] = "#"
        board[0][0] = "S"
        board[11][11] = "G"
        level = make_level(["".join(row) for row in board])
        action = rng.choice(list(Action)[:4])
        expected = physical_roll(cells, action)
        result = step(level, State(cells), action)
        supported = all(0 <= a < 12 and 0 <= b < 12 and board[a][b] != "." for a, b in expected)
        assert (result.state is not None) == supported
        if supported:
            assert result.state.cells == expected
