"""Strict JSON loader with immutable precomputed cell lookup tables."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
from core.constants import Cell, CODES
from core.state import State
from core.tiles import Bridge, Switch, SwitchMode, SwitchType, TileType


class LevelError(ValueError):
    """Invalid level; messages include source and source line."""


@dataclass(frozen=True)
class Level:
    id: int
    name: str
    grid: tuple[str, ...]
    tiles: tuple[tuple[TileType, ...], ...]
    start: Cell
    goal: Cell
    bridges: tuple[Bridge, ...]
    switches: tuple[Switch, ...]
    bridge_bits: tuple[tuple[int, ...], ...]
    switch_indices: tuple[tuple[int, ...], ...]
    initial_bridges: int
    _json: str = field(repr=False)

    @property
    def meta(self) -> dict[str, Any]:
        """Return a detached metadata copy; caller cannot mutate the level."""
        return dict(self.to_dict().get("meta", {}))

    @property
    def height(self) -> int:
        """Number of rows."""
        return len(self.grid)

    @property
    def width(self) -> int:
        """Number of columns."""
        return len(self.grid[0])

    def to_dict(self) -> dict[str, Any]:
        """Return detached JSON data, including private solution metadata."""
        data: dict[str, Any] = json.loads(self._json)
        return data

    @classmethod
    def load(cls, path: str | Path) -> Level:
        """Load UTF-8 JSON and include accurate JSON/grid line diagnostics."""
        source = Path(path)
        try:
            text = source.read_text(encoding="utf-8")
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LevelError(f"{source}:line {exc.lineno}: {exc.msg}") from exc
        try:
            return cls.from_dict(data, str(source))
        except LevelError as exc:
            message = str(exc)
            # Semantic errors name a grid row when relevant; otherwise use the key line.
            import re

            row = re.search(r"grid row (\d+)", message)
            line = 1
            if row:
                target = data["grid"][int(row.group(1))]
                line = next(
                    (i for i, s in enumerate(text.splitlines(), 1) if json.dumps(target) in s), 1
                )
            else:
                for key in ("switches", "bridges", "legend", "grid", "meta"):
                    if key in message:
                        line = next(
                            (i for i, s in enumerate(text.splitlines(), 1) if f'"{key}"' in s), 1
                        )
                        break
            raise LevelError(message.replace(":line 1:", f":line {line}:")) from exc

    @classmethod
    def from_dict(cls, data: dict[str, Any], source: str = "<dict>") -> Level:
        """Validate structure, references, tile membership and initial support."""

        def require(ok: bool, message: str) -> None:
            if not ok:
                raise LevelError(f"{source}:line 1: {message}")

        try:
            require(isinstance(data, dict), "level must be an object")
            require(isinstance(data["grid"], (list, tuple)), "grid must be an array of rows")
            grid = tuple(data["grid"])
            require(
                bool(grid) and all(isinstance(s, str) and s for s in grid), "grid must be nonempty"
            )
            require(all(len(s) == len(grid[0]) for s in grid), "grid rows must have equal width")
            h, w = len(grid), len(grid[0])
            legend = {k: TileType(v) for k, v in data["legend"].items()}
            require(all(len(k) == 1 for k in legend), "legend keys must be single characters")
            for r, row in enumerate(grid):
                require(all(ch in legend for ch in row), f"grid row {r}: unknown legend character")
            tiles = tuple(tuple(legend[ch] for ch in row) for row in grid)

            def positions(tile: TileType) -> list[Cell]:
                return [(r, c) for r in range(h) for c in range(w) if tiles[r][c] == tile]

            starts, goals = positions(TileType.START), positions(TileType.GOAL)
            require(len(starts) == len(goals) == 1, "grid needs exactly one start and one goal")

            def cell(value: Any) -> Cell:
                require(
                    isinstance(value, (list, tuple))
                    and len(value) == 2
                    and all(type(v) is int for v in value),
                    "cell must contain two integers",
                )
                r, c = value
                require(0 <= r < h and 0 <= c < w, f"cell {(r, c)} outside grid")
                return r, c

            bridges: list[Bridge] = []
            bits = [[0] * w for _ in range(h)]
            ids: set[int] = set()
            initial = 0
            for obj in data.get("bridges", []):
                i = obj["id"]
                require(
                    type(i) is int and 0 <= i < 64 and i not in ids,
                    "bridges: unique id in [0,63] required",
                )
                ids.add(i)
                require(type(obj.get("open", False)) is bool, "bridges.open must be boolean")
                cells = tuple(cell(v) for v in obj["cells"])
                require(bool(cells), "bridges.cells cannot be empty")
                for r, c in cells:
                    require(
                        tiles[r][c] == TileType.BRIDGE and bits[r][c] == 0,
                        f"bridges: grid row {r}: bridge cell must belong to exactly one bridge",
                    )
                    bits[r][c] = 1 << i
                opened = obj.get("open", False)
                bridges.append(Bridge(i, cells, opened))
                if opened:
                    initial |= 1 << i
            require(
                all(bits[r][c] for r, c in positions(TileType.BRIDGE)),
                "bridges: unassigned bridge tile",
            )
            switches: list[Switch] = []
            indices = [[-1] * w for _ in range(h)]
            kind_tiles = {
                SwitchType.SOFT: TileType.SOFT,
                SwitchType.HEAVY: TileType.HEAVY,
                SwitchType.SPLIT: TileType.SPLIT,
            }
            for obj in data.get("switches", []):
                r, c = cell(obj["cell"])
                kind, mode = SwitchType(obj["type"]), SwitchMode(obj["mode"])
                require(
                    tiles[r][c] == kind_tiles[kind] and indices[r][c] == -1,
                    f"switches: grid row {r}: type mismatch or duplicate switch",
                )
                targets = tuple(obj.get("targets", []))
                require(
                    all(type(i) is int and i in ids for i in targets)
                    and len(targets) == len(set(targets)),
                    "switches: invalid/duplicate bridge targets",
                )
                require(
                    obj.get("set", "open") in ("open", "closed"), "switches.set must be open/closed"
                )
                require(
                    mode != SwitchMode.PERMANENT or "set" in obj, "switches: permanent requires set"
                )
                require(
                    mode != SwitchMode.TOGGLE or "set" not in obj,
                    "switches: toggle cannot have set",
                )
                cubes = tuple(cell(v) for v in obj.get("cubes", []))
                if kind == SwitchType.SPLIT:
                    require(
                        len(cubes) == 2 and cubes[0] != cubes[1],
                        "switches: split needs distinct cubes",
                    )
                    require(
                        all(
                            tiles[a][b] != TileType.VOID
                            and (tiles[a][b] != TileType.BRIDGE or bool(initial & bits[a][b]))
                            for a, b in cubes
                        ),
                        "switches: split destinations need initial support",
                    )
                else:
                    require(not cubes, "switches: cubes only allowed on split")
                indices[r][c] = len(switches)
                switches.append(
                    Switch((r, c), kind, mode, targets, obj.get("set") == "open", cubes)
                )
            require(
                all(indices[r][c] >= 0 for t in kind_tiles.values() for r, c in positions(t)),
                "switches: missing switch definition",
            )
            require(type(data["id"]) is int and data["id"] > 0, "id must be a positive integer")
            require(isinstance(data["name"], str) and bool(data["name"]), "name required")
            meta = data.get("meta", {})
            require(isinstance(meta, dict), "meta must be an object")
            if "group" in meta:
                require(
                    type(meta["group"]) is int and meta["group"] in (1, 2, 3, 4),
                    "meta.group must be 1-4",
                )
            if "difficulty" in meta:
                require(
                    type(meta["difficulty"]) is int and 1 <= meta["difficulty"] <= 5,
                    "meta.difficulty must be 1-5",
                )
            if "solution" in meta:
                require(
                    isinstance(meta["solution"], str)
                    and all(ch in CODES for ch in meta["solution"]),
                    "meta.solution: use UDLRW only",
                )
                require(
                    type(meta.get("optimal_moves")) is int
                    and meta["optimal_moves"] == len(meta["solution"]),
                    "meta: solution length mismatch",
                )
            return cls(
                data["id"],
                data["name"],
                grid,
                tiles,
                starts[0],
                goals[0],
                tuple(bridges),
                tuple(switches),
                tuple(tuple(row) for row in bits),
                tuple(tuple(row) for row in indices),
                initial,
                json.dumps(data),
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            if isinstance(exc, LevelError):
                raise
            raise LevelError(f"{source}:line 1: {exc}") from exc

    def tile_at(self, r: int, c: int) -> TileType:
        """Out-of-bounds cells are void."""
        return self.tiles[r][c] if 0 <= r < self.height and 0 <= c < self.width else TileType.VOID

    def is_supported(self, cell: Cell, bridges: int) -> bool:
        """O(1) support query for the given bridge configuration."""
        r, c = cell
        tile = self.tile_at(r, c)
        return tile != TileType.VOID and (
            tile != TileType.BRIDGE or bool(bridges & self.bridge_bits[r][c])
        )

    def initial_state(self) -> State:
        """Standing block at start with initial bridge mask."""
        return State((self.start,), bridges=self.initial_bridges)
