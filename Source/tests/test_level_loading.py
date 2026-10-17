from __future__ import annotations
from pathlib import Path
import copy
import pytest
from core.level import Level, LevelError
from tests.conftest import make_level

FILES = sorted((Path(__file__).parents[1] / "levels").glob("level_*.json"))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_load(path):
    level = Level.load(path)
    assert level.meta["group"] in (1, 2, 3, 4)
    detached = level.to_dict()
    detached["grid"][0] = "broken"
    assert level.to_dict()["grid"][0] != "broken"


def test_fifteen():
    assert len(FILES) == 15


@pytest.mark.parametrize(
    "modify",
    [
        lambda d: d.update(grid=["S##G", "##"]),
        lambda d: d.update(grid="SG"),
        lambda d: d.update(meta=[]),
        lambda d: d.update(meta={"group": 0}),
        lambda d: d.update(meta={"difficulty": 6}),
        lambda d: d.update(grid=["SSG"]),
        lambda d: d.update(grid=["S?G"]),
        lambda d: d.update(grid=["SBG"]),
        lambda d: d.update(grid=["SoG"]),
        lambda d: d.update(bridges=[{"id": 0, "cells": [[0, 0]]}]),
        lambda d: d.update(
            switches=[{"cell": [0, 1], "type": "soft", "mode": "broken", "targets": []}]
        ),
        lambda d: d.update(meta={"solution": "R?", "optimal_moves": 2}),
    ],
)
def test_invalid(modify):
    data = copy.deepcopy(make_level(["S##G"]).to_dict())
    modify(data)
    with pytest.raises(LevelError, match="test.json:line"):
        Level.from_dict(data, "test.json")


def test_file_line_diagnostic(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text('{\n"grid": ["S?G"],\n"id":1,"name":"bad",\n"legend":{"S":"start","G":"goal"}\n}')
    with pytest.raises(LevelError, match="line 2"):
        Level.load(f)
