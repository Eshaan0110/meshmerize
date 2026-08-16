"""Random maze generation and independent graph utilities for stress-testing
maze_solver.py / maze_sim.py against ground truth.

generate_perfect_maze() builds a spanning tree over an R x C grid, so there
is exactly one simple path between any two cells -- a property the stress
tests in test_maze_stress.py lean on to check that the exploration +
simplification pipeline actually reproduces the graph's true shortest path,
not just "doesn't crash". add_random_loops() turns such a tree into a
braided maze (multiple possible paths) for termination-only stress testing.
"""

import random
from collections import deque
from typing import List, Optional, Tuple

Cell = Tuple[int, int]
Edge = Tuple[Cell, Cell]

_ALL_DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_CANONICAL_DELTAS = [(1, 0), (0, 1)]  # down, right -- avoids double-counting pairs


def generate_perfect_maze(rows: int, cols: int, seed: Optional[int] = None) -> List[Edge]:
    """Randomized DFS (recursive backtracker), iterative to avoid recursion
    limits on large grids. Returns the spanning-tree edge list."""
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be >= 1")

    rng = random.Random(seed)
    start: Cell = (0, 0)
    visited = {start}
    stack = [start]
    edges: List[Edge] = []

    while stack:
        current = stack[-1]
        neighbors = [
            (current[0] + dr, current[1] + dc)
            for dr, dc in _ALL_DELTAS
            if 0 <= current[0] + dr < rows and 0 <= current[1] + dc < cols
            and (current[0] + dr, current[1] + dc) not in visited
        ]
        if not neighbors:
            stack.pop()
            continue
        nxt = rng.choice(neighbors)
        edges.append((current, nxt))
        visited.add(nxt)
        stack.append(nxt)

    return edges


def add_random_loops(edges: List[Edge], rows: int, cols: int, extra: int,
                      seed: Optional[int] = None) -> List[Edge]:
    """Adds up to `extra` random edges between adjacent cells not already
    connected, turning a perfect maze into a braided one with loops."""
    rng = random.Random(seed)
    existing = {frozenset(e) for e in edges}
    candidates = []
    for r in range(rows):
        for c in range(cols):
            for dr, dc in _CANONICAL_DELTAS:
                nb = (r + dr, c + dc)
                if 0 <= nb[0] < rows and 0 <= nb[1] < cols:
                    pair = frozenset({(r, c), nb})
                    if pair not in existing:
                        candidates.append(((r, c), nb))
                        existing.add(pair)

    rng.shuffle(candidates)
    return list(edges) + candidates[:extra]


def bfs_distance(edges: List[Edge], start: Cell, goal: Cell) -> int:
    """Shortest path length (in cell-to-cell steps) between start and goal,
    computed independently of the maze-solving algorithm under test."""
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    if start == goal:
        return 0

    frontier = deque([start])
    distance = {start: 0}
    while frontier:
        cell = frontier.popleft()
        for neighbor in adjacency.get(cell, []):
            if neighbor not in distance:
                distance[neighbor] = distance[cell] + 1
                if neighbor == goal:
                    return distance[neighbor]
                frontier.append(neighbor)

    raise ValueError(f"{goal} is not reachable from {start}")
