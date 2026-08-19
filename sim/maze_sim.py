"""Grid-based maze simulator that drives maze_solver.py the same way the
robot's two firmware phases do, without needing real hardware:

  Phase 1 (exploration) - left-hand-rule wall following, recording and
  simplifying the path as it goes (record_and_simplify), until the goal
  cell is reached.

  Phase 2 (speed run) - blind replay of the simplified path: at every real
  decision point the next recorded turn is taken; plain corridors are just
  driven through. This mirrors the `iType == 1 || iType == 0` "not a
  decision point" shortcut in speedRunLoop() in maze_runner.ino.

A maze is defined as a set of undirected edges between orthogonally
adjacent (row, col) grid cells.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from maze_solver import DEAD_END, STRAIGHT_ONLY, choose_direction, encode_intersection, record_and_simplify

Cell = Tuple[int, int]

DELTA = {'N': (-1, 0), 'E': (0, 1), 'S': (1, 0), 'W': (0, -1)}
LEFT_TURN = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}
RIGHT_TURN = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
BACK = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}


def _direction_between(a: Cell, b: Cell) -> str:
    delta = (b[0] - a[0], b[1] - a[1])
    for direction, d in DELTA.items():
        if d == delta:
            return direction
    raise ValueError(f"cells {a} and {b} are not orthogonally adjacent")


def _move(cell: Cell, heading: str) -> Cell:
    dr, dc = DELTA[heading]
    return (cell[0] + dr, cell[1] + dc)


class Maze:
    def __init__(self, edges: List[Tuple[Cell, Cell]]):
        self._open: Dict[Cell, Set[str]] = defaultdict(set)
        for a, b in edges:
            direction = _direction_between(a, b)
            self._open[a].add(direction)
            self._open[b].add(BACK[direction])

    def exits(self, cell: Cell) -> Set[str]:
        return self._open.get(cell, set())


class MazeUnsolvableError(RuntimeError):
    pass


def simulate_phase1(maze: Maze, start: Cell, start_heading: str, goal: Cell,
                     max_steps: int = 2000, trace: Optional[List[Cell]] = None) -> Tuple[List[str], int]:
    """Runs left-hand-rule exploration to the goal. Returns (path, steps)
    where `path` is the live-simplified decision list (mirrors path[] /
    optimizedPath[] in the firmware, since they're built from the same
    record_and_simplify calls). If `trace` is given, every cell visited
    (including start and goal) is appended to it in order, for visualization."""
    pos, heading = start, start_heading
    path: List[str] = []
    if trace is not None:
        trace.append(pos)

    for steps in range(1, max_steps + 1):
        if pos == goal:
            return path, steps - 1

        exits = maze.exits(pos)
        left_dir, right_dir, straight_dir = LEFT_TURN[heading], RIGHT_TURN[heading], heading
        itype = encode_intersection(left_dir in exits, right_dir in exits, straight_dir in exits)

        if itype == STRAIGHT_ONLY:
            pos = _move(pos, heading)
            if trace is not None:
                trace.append(pos)
            continue

        decision = choose_direction(itype)
        record_and_simplify(path, decision)

        heading = {'L': left_dir, 'R': right_dir, 'S': straight_dir}.get(decision, BACK[heading])
        pos = _move(pos, heading)
        if trace is not None:
            trace.append(pos)

    raise MazeUnsolvableError("exploration did not reach the goal within max_steps")


def simulate_phase2(maze: Maze, start: Cell, start_heading: str, goal: Cell,
                     optimized_path: List[str], max_steps: int = 2000,
                     trace: Optional[List[Cell]] = None) -> int:
    """Blindly replays `optimized_path`, consuming one entry per real
    decision point. Returns the number of steps taken to reach the goal.
    If `trace` is given, every cell visited (including start and goal) is
    appended to it in order, for visualization."""
    pos, heading = start, start_heading
    step_idx = 0
    if trace is not None:
        trace.append(pos)

    for steps in range(1, max_steps + 1):
        if pos == goal:
            return steps - 1

        exits = maze.exits(pos)
        left_dir, right_dir, straight_dir = LEFT_TURN[heading], RIGHT_TURN[heading], heading
        itype = encode_intersection(left_dir in exits, right_dir in exits, straight_dir in exits)

        if itype == DEAD_END and step_idx >= len(optimized_path):
            raise MazeUnsolvableError("blind replay drove into an unrecorded dead end")

        if itype == STRAIGHT_ONLY or step_idx >= len(optimized_path):
            pos = _move(pos, heading)
            if trace is not None:
                trace.append(pos)
            continue

        decision = optimized_path[step_idx]
        step_idx += 1
        heading = {'L': left_dir, 'R': right_dir, 'S': straight_dir}.get(decision, BACK[heading])
        pos = _move(pos, heading)
        if trace is not None:
            trace.append(pos)

    raise MazeUnsolvableError("speed run did not reach the goal within max_steps")
