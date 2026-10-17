"""Canonical, immutable state; active identifies a position after sorting."""
from __future__ import annotations
from dataclasses import dataclass
from core.constants import Cell, Orientation

@dataclass(frozen=True)
class State:
    cubes: tuple[Cell, ...]
    split: bool = False
    active: int = 0
    bridges: int = 0

    def __post_init__(self) -> None:
        raw = tuple((int(r), int(c)) for r, c in self.cubes)
        if len(raw) not in (1, 2) or len(set(raw)) != len(raw):
            raise ValueError("State needs one cell or two distinct cells")
        if self.bridges < 0 or (self.split and (len(raw) != 2 or self.active not in (0, 1))):
            raise ValueError("Invalid split, active or bridges")
        cells = tuple(sorted(raw))
        if not self.split and len(cells) == 2:
            if sum(abs(a-b) for a, b in zip(*cells)) != 1:
                raise ValueError("Unsplit cells must be adjacent")
        active = cells.index(raw[self.active]) if self.split else 0
        object.__setattr__(self, "cubes", cells)
        object.__setattr__(self, "active", active)

    @property
    def cells(self) -> tuple[Cell, ...]:
        """Occupied board cells (standing stores one footprint cell)."""
        return self.cubes

    @property
    def orientation(self) -> Orientation:
        """Derive orientation; it is never a separate mutable field."""
        if self.split:
            return Orientation.SPLIT
        if len(self.cubes) == 1:
            return Orientation.STANDING
        return Orientation.LYING_H if self.cubes[0][0] == self.cubes[1][0] else Orientation.LYING_V

    def is_standing_at(self, cell: Cell) -> bool:
        """Whether the complete block stands at cell."""
        return not self.split and self.cubes == (cell,)
