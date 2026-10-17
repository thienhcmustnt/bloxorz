from __future__ import annotations
import csv
from pathlib import Path
from PIL import Image
from bench.run_bench import benchmark, COLUMNS, numbers
from bench.plots import plot_results
from core.level import Level
from solvers.runner import ALGORITHMS


def test_fake_benchmark_and_figures(tmp_path, monkeypatch):
    monkeypatch.setitem(ALGORITHMS, "fixture", "tests.fake_solver:solve")
    root = Path(__file__).resolve().parents[1]
    levels = [Level.load(root / "levels" / f"level_{i:02d}.json") for i in [1, 5, 7, 10]]
    rows = benchmark(["fixture"], levels, repeat=2, out=tmp_path)
    assert len(rows) == 4
    for level, row in zip(levels, rows):
        assert row["found"] and row["solution_length"] == level.meta["optimal_moves"]
        assert row["peak_memory_kb"] > 0 and row["search_time_s"] > 0
    with (tmp_path / "results.csv").open() as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == COLUMNS
    figures = plot_results(tmp_path / "results.csv", tmp_path)
    assert len(figures) == 4
    for path in figures:
        with Image.open(path) as image:
            assert image.width >= 3000 and image.height >= 1800
    assert "| fixture |" in (tmp_path / "summary.md").read_text()


def test_stub_skip(tmp_path, capsys):
    root = Path(__file__).resolve().parents[1]
    assert (
        benchmark(["bfs"], [Level.load(root / "levels" / "level_01.json")], repeat=1, out=tmp_path)
        == []
    )
    assert "WARNING" in capsys.readouterr().err
    plot_results(tmp_path / "results.csv", tmp_path)
    assert "No implemented solver" in (tmp_path / "summary.md").read_text()


def test_id_ranges():
    assert numbers(["1-4", "7,10"]) == {1, 2, 3, 4, 7, 10}
