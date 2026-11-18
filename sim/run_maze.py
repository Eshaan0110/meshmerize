"""Command-line driver for the offline solver.

Generates a maze, runs both phases, and prints either the full ASCII
rendering (single run) or a summary table (--batch N seeds), comparing the
speed-run length against the BFS optimum so regressions are easy to spot.

    python run_maze.py --rows 8 --cols 8 --seed 3
    python run_maze.py --rows 10 --cols 10 --loops 6 --batch 50
"""

import argparse
import sys
from typing import List, Optional

from maze_generator import add_random_loops, bfs_distance, generate_perfect_maze
from maze_sim import Maze, MazeUnsolvableError, simulate_phase1, simulate_phase2
from map_optimizer import mapped_path
from maze_viz import render_run


def build_maze(rows: int, cols: int, seed: Optional[int], loops: int):
    edges = generate_perfect_maze(rows, cols, seed=seed)
    if loops:
        edges = add_random_loops(edges, rows, cols, loops, seed=seed)
    return edges


def run_once(rows: int, cols: int, seed: Optional[int], loops: int, heading: str) -> dict:
    """Returns stats for one generated maze; 'error' is set if a phase failed."""
    edges = build_maze(rows, cols, seed, loops)
    start, goal = (0, 0), (rows - 1, cols - 1)
    result = {'seed': seed, 'optimal': bfs_distance(edges, start, goal),
              'explore': None, 'speed': None, 'mapped': None, 'error': None}
    maze = Maze(edges)
    try:
        path, result['explore'] = simulate_phase1(maze, start, heading, goal)
        result['speed'] = simulate_phase2(maze, start, heading, goal, path)
        result['mapped'] = simulate_phase2(maze, start, heading, goal,
                                           mapped_path(maze, start, heading, goal))
    except MazeUnsolvableError as exc:
        result['error'] = str(exc)
    return result


def format_batch(results: List[dict]) -> str:
    lines = [f"{'seed':>6} {'optimal':>8} {'explore':>8} {'speed':>6} {'mapped':>7}  status"]
    for r in results:
        if r['error']:
            status = f"FAIL: {r['error']}"
        elif r['speed'] == r['optimal']:
            status = 'optimal'
        else:
            status = f"+{r['speed'] - r['optimal']} over optimal"
        lines.append(f"{r['seed']!s:>6} {r['optimal']:>8} {r['explore']!s:>8} {r['speed']!s:>6} {r.get('mapped')!s:>7}  {status}")
    ok = [r for r in results if not r['error']]
    optimal = sum(1 for r in ok if r['speed'] == r['optimal'])
    gained = sum(r['speed'] - r['mapped'] for r in ok if r.get('mapped') is not None)
    lines.append(f"map-based replay saves {gained} steps over the left-hand path in total")
    lines.append(f"{len(results)} mazes: {len(ok)} solved, {optimal} optimal, "
                 f"{len(results) - len(ok)} failed")
    return '\n'.join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--rows', type=int, default=6)
    parser.add_argument('--cols', type=int, default=6)
    parser.add_argument('--seed', type=int, default=0, help='seed (first seed when --batch)')
    parser.add_argument('--loops', type=int, default=0,
                        help='extra edges to braid the maze (0 = perfect maze)')
    parser.add_argument('--heading', choices=['N', 'E', 'S', 'W'], default='E')
    parser.add_argument('--batch', type=int, default=0,
                        help='run N consecutive seeds and print a summary table')
    args = parser.parse_args(argv)

    if args.batch:
        results = [run_once(args.rows, args.cols, args.seed + i, args.loops, args.heading)
                   for i in range(args.batch)]
        print(format_batch(results))
        return 1 if any(r['error'] for r in results) else 0

    edges = build_maze(args.rows, args.cols, args.seed, args.loops)
    try:
        print(render_run(edges, args.rows, args.cols, (0, 0), args.heading,
                         (args.rows - 1, args.cols - 1)))
    except MazeUnsolvableError as exc:
        print(f"unsolvable: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
