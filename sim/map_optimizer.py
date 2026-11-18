"""Map-based alternative to the dead-end-collapsing optimizer.

Left-hand-rule exploration on a braided maze can leave loops in the
recorded path, so the blind replay is longer than necessary. Here the
explored cell graph is kept during phase 1, BFS picks the shortest route
through the cells that were actually visited, and that route is converted
back into the same L/S/R/B decision list that simulate_phase2 replays.
This quantifies how much a flood-fill style optimizer would gain.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from maze_sim import (BACK, LEFT_TURN, RIGHT_TURN, Cell, Maze, MazeUnsolvableError,
                      _direction_between, _move, simulate_phase1)
from maze_solver import STRAIGHT_ONLY, encode_intersection


def explored_graph(trace: List[Cell]) -> Dict[Cell, Set[Cell]]:
    """Adjacency of every cell-to-cell move made during exploration."""
    graph: Dict[Cell, Set[Cell]] = {}
    for a, b in zip(trace, trace[1:]):
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    return graph


def shortest_cell_path(graph: Dict[Cell, Set[Cell]], start: Cell, goal: Cell) -> List[Cell]:
    prev: Dict[Cell, Optional[Cell]] = {start: None}
    frontier = deque([start])
    while frontier:
        cell = frontier.popleft()
        if cell == goal:
            break
        for nb in sorted(graph.get(cell, ())):
            if nb not in prev:
                prev[nb] = cell
                frontier.append(nb)
    if goal not in prev:
        raise MazeUnsolvableError("goal not reachable in the explored map")
    route = []
    cell: Optional[Cell] = goal
    while cell is not None:
        route.append(cell)
        cell = prev[cell]
    return route[::-1]


def cells_to_decisions(maze: Maze, route: List[Cell], start_heading: str) -> List[str]:
    """One decision per real decision point along `route`, in the form
    simulate_phase2 consumes (plain corridors contribute nothing)."""
    decisions: List[str] = []
    heading = start_heading
    for here, nxt in zip(route, route[1:]):
        exits = maze.exits(here)
        left_dir, right_dir = LEFT_TURN[heading], RIGHT_TURN[heading]
        new_heading = _direction_between(here, nxt)
        if encode_intersection(left_dir in exits, right_dir in exits, heading in exits) != STRAIGHT_ONLY:
            if new_heading == left_dir:
                decisions.append('L')
            elif new_heading == right_dir:
                decisions.append('R')
            elif new_heading == heading:
                decisions.append('S')
            else:
                decisions.append('B')
        heading = new_heading
    return decisions


def mapped_path(maze: Maze, start: Cell, start_heading: str, goal: Cell) -> List[str]:
    """Explore with the left-hand rule, then return the decision list for
    the shortest route through the explored map."""
    trace: List[Cell] = []
    simulate_phase1(maze, start, start_heading, goal, trace=trace)
    route = shortest_cell_path(explored_graph(trace), start, goal)
    return cells_to_decisions(maze, route, start_heading)
