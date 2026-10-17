"""Single source of truth for movement and ordered rule resolution."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from core.constants import Action, Cell, DELTAS, DIRECTIONS, EventType, Orientation, Status
from core.costs import CostModel, action_cost
from core.level import Level
from core.state import State
from core.tiles import SwitchMode, SwitchType, TileType

@dataclass(frozen=True)
class Event:
    type: EventType
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Flatten JSON-friendly event payload."""
        return {"type": self.type.value, **self.data}

@dataclass
class StepResult:
    state: State | None
    status: Status
    events: list[Event]
    cost: float

def _roll(state: State, action: Action) -> tuple[Cell, ...]:
    r, c = state.cells[0]
    dr, dc = DELTAS[action]
    if state.orientation == Orientation.STANDING:
        if dr:
            return ((r-2,c),(r-1,c)) if dr < 0 else ((r+1,c),(r+2,c))
        return ((r,c-2),(r,c-1)) if dc < 0 else ((r,c+1),(r,c+2))
    if state.orientation == Orientation.LYING_H:
        return ((r,c-1),) if dc < 0 else ((r,c+2),) if dc > 0 else ((r+dr,c),(r+dr,c+1))
    return ((r-1,c),) if dr < 0 else ((r+2,c),) if dr > 0 else ((r,c+dc),(r+1,c+dc))

def is_goal(level: Level, state: State) -> bool:
    """Only a whole standing block can win."""
    return state.is_standing_at(level.goal)

def step(level: Level, state: State, action: Action,
         cost_model: CostModel = "risk") -> StepResult:
    """Resolve roll, support, fragile, switches, support, split/merge, goal.

    SWAP is a control-only action: cost 1, no tile reactivation or merge.
    Invalid SWAP/overlap return LOST. Rules never mutate input objects.
    """
    action = Action(action)
    events: list[Event] = []
    def event(kind: EventType, **data: Any) -> None:
        events.append(Event(kind, data))
    def lost(cells: tuple[Cell, ...], reason: str) -> StepResult:
        event(EventType.FALL, cells=cells, reason=reason)
        return StepResult(None, Status.LOST, events, 1.0)
    if action == Action.SWAP:
        if not state.split:
            return lost(state.cells, "swap_requires_split")
        after = State(state.cells, True, 1-state.active, state.bridges)
        event(EventType.SWAP, active=after.active, cells=after.cells)
        return StepResult(after, Status.PLAYING, events, action_cost(level,state,action,after,cost_model))
    if state.split:
        raw = list(state.cells)
        r, c = raw[state.active]
        dr, dc = DELTAS[action]
        raw[state.active] = r+dr, c+dc
        cells = tuple(raw)
    else:
        cells = _roll(state, action)
    event(EventType.ROLL, from_cells=state.cells, to_cells=cells, direction=action.value,
          from_orientation=state.orientation.value,
          to_orientation=(Orientation.SPLIT.value if state.split else
                          Orientation.STANDING.value if len(cells)==1 else
                          Orientation.LYING_H.value if cells[0][0]==cells[1][0] else Orientation.LYING_V.value),
          cube_index=state.active if state.split else None)
    if len(set(cells)) != len(cells) or not all(level.is_supported(c,state.bridges) for c in cells):
        return lost(cells, "unsupported_or_overlap")
    after = State(cells, state.split, state.active, state.bridges)
    if not after.split and len(after.cells)==1 and level.tile_at(*after.cells[0])==TileType.FRAGILE:
        event(EventType.FRAGILE, cell=after.cells[0])
        return StepResult(None, Status.LOST, events, 1.0)
    bridges = after.bridges
    split_cells: tuple[Cell, ...] = ()
    for r, c in after.cells:  # canonical row-major order, once per occupied switch
        index = level.switch_indices[r][c]
        if index < 0:
            continue
        switch = level.switches[index]
        if switch.type != SwitchType.SOFT and not after.is_standing_at((r,c)):
            continue
        event(EventType.SWITCH, cell=(r,c), switch_type=switch.type.value)
        for target in switch.targets:
            old = bool(bridges & (1 << target))
            new = not old if switch.mode == SwitchMode.TOGGLE else switch.set_open
            bridges = (bridges | (1 << target)) if new else (bridges & ~(1 << target))
            if old != new:
                event(EventType.BRIDGE, bridge_id=target, open=new)
        if switch.type == SwitchType.SPLIT:
            split_cells = switch.cubes
    after = State(after.cells, after.split, after.active, bridges)
    if not all(level.is_supported(c, bridges) for c in after.cells):
        return lost(after.cells, "bridge_closed_under_block")
    if split_cells:
        event(EventType.SPLIT, from_cells=after.cells, to_cells=split_cells, active_cell=split_cells[0])
        if not all(level.is_supported(c, bridges) for c in split_cells):
            return lost(split_cells, "unsupported_split_destination")
        after = State(split_cells, True, 0, bridges)
    if after.split and sum(abs(a-b) for a,b in zip(*after.cells)) == 1:
        after = State(after.cells, False, 0, bridges)
        event(EventType.MERGE, cells=after.cells, orientation=after.orientation.value)
    won = is_goal(level, after)
    if won:
        event(EventType.WIN, cell=level.goal)
    return StepResult(after, Status.WON if won else Status.PLAYING, events,
                      action_cost(level, state, action, after, cost_model))

def successors(level: Level, state: State, cost_model: CostModel = "risk") -> list[tuple[Action, State, float]]:
    """Return unique actions with non-losing destinations, including winning ones."""
    if is_goal(level, state):
        return []
    result = []
    for action in (*DIRECTIONS, Action.SWAP) if state.split else DIRECTIONS:
        transition = step(level,state,action,cost_model)
        if transition.state is not None:
            result.append((action,transition.state,transition.cost))
    return result

def legal_actions(level: Level, state: State) -> list[Action]:
    """Return actions that do not lose immediately."""
    return [a for a,_,_ in successors(level,state)]
