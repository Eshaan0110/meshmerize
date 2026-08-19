"""ASCII rendering of a maze plus an overlaid cell path, for eyeballing what
the exploration and speed-run phases actually did instead of reading raw
(row, col) tuples.

Usable as a library (`render_maze`, `render_run`) or as a script:

    python maze_viz.py --rows 6 --cols 6 --seed 1
"""

import argparse
from typing import Iterable, List, Optional, Sequence, Set, Tuple

Cell = Tuple[int, int]
Edge = Tuple[Cell, Cell]


def _edge_set(edges: Iterable[Edge]) -> Set[frozenset]:
    return {frozenset(e) for e in edges}


def _connected(connected: Set[frozenset], rows: int, cols: int, a: Cell, b: Cell) -> bool:
    for cell in (a, b):
        if not (0 <= cell[0] < rows and 0 <= cell[1] < cols):
            return False
    return frozenset((a, b)) in connected


def render_maze(edges: Iterable[Edge], rows: int, cols: int,
                 trace: Optional[Sequence[Cell]] = None,
                 start: Optional[Cell] = None, goal: Optional[Cell] = None) -> str:
    """Renders an ASCII grid: '+---+' walls, 'S'/'G' for start/goal, '*' for
    cells visited in `trace`. Falls back to trace[0]/trace[-1] for start/goal
    if they aren't given explicitly."""
    connected = _edge_set(edges)
    trace_cells = set(trace) if trace else set()
    if start is None and trace:
        start = trace[0]
    if goal is None and trace:
        goal = trace[-1]

    lines: List[str] = []
    for r in range(rows):
        top = ['+']
        for c in range(cols):
            top.append('   ' if _connected(connected, rows, cols, (r - 1, c), (r, c)) else '---')
            top.append('+')
        lines.append(''.join(top))

        mid = []
        for c in range(cols):
            mid.append(' ' if _connected(connected, rows, cols, (r, c - 1), (r, c)) else '|')
            cell = (r, c)
            if cell == start:
                mid.append(' S ')
            elif cell == goal:
                mid.append(' G ')
            elif cell in trace_cells:
                mid.append(' * ')
            else:
                mid.append('   ')
        mid.append('|')
        lines.append(''.join(mid))

    bottom = ['+']
    for _ in range(cols):
        bottom.append('---+')
    lines.append(''.join(bottom))

    return '\n'.join(lines)


def render_run(edges: Iterable[Edge], rows: int, cols: int, start: Cell,
               start_heading: str, goal: Cell) -> str:
    """Runs both solver phases and renders exploration + speed-run grids side
    by side (as stacked text blocks), along with the optimized path and step
    counts. Raises MazeUnsolvableError if either phase can't reach the goal."""
    from maze_sim import Maze, simulate_phase1, simulate_phase2

    maze = Maze(list(edges))
    explore_trace: List[Cell] = []
    optimized_path, explore_steps = simulate_phase1(maze, start, start_heading, goal, trace=explore_trace)

    speed_trace: List[Cell] = []
    speed_steps = simulate_phase2(maze, start, start_heading, goal, optimized_path, trace=speed_trace)

    sections = [
        f"Exploration ({explore_steps} steps):",
        render_maze(edges, rows, cols, trace=explore_trace, start=start, goal=goal),
        "",
        f"Optimized path: {optimized_path}",
        "",
        f"Speed run ({speed_steps} steps):",
        render_maze(edges, rows, cols, trace=speed_trace, start=start, goal=goal),
    ]
    return '\n'.join(sections)


def _main() -> None:
    from maze_generator import generate_perfect_maze

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=int, default=6)
    parser.add_argument('--cols', type=int, default=6)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--heading', choices=['N', 'E', 'S', 'W'], default='E')
    args = parser.parse_args()

    edges = generate_perfect_maze(args.rows, args.cols, seed=args.seed)
    start = (0, 0)
    goal = (args.rows - 1, args.cols - 1)
    print(render_run(edges, args.rows, args.cols, start, args.heading, goal))


if __name__ == '__main__':
    _main()
