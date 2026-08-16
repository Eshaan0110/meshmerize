import unittest

from maze_generator import add_random_loops, bfs_distance, generate_perfect_maze
from maze_sim import Maze, simulate_phase1, simulate_phase2

HEADINGS = ['N', 'E', 'S', 'W']


class PerfectMazeStressTest(unittest.TestCase):
    """Across many random spanning-tree mazes, phase 2's optimized path must
    reproduce the graph's true shortest path: a spanning tree has exactly
    one simple path between any two cells, so every dead-end detour the
    left-hand-rule exploration takes has to fully cancel out under
    record_and_simplify. This is the property test_maze_sim.py's
    hand-built examples only spot-check on one maze each."""

    SIZES = [(3, 3), (4, 4), (5, 5), (6, 8), (8, 5), (10, 10)]
    SEEDS = range(8)

    def test_optimized_path_matches_graph_shortest_path(self):
        for rows, cols in self.SIZES:
            for seed in self.SEEDS:
                edges = generate_perfect_maze(rows, cols, seed=seed)
                maze = Maze(edges)
                start, goal = (0, 0), (rows - 1, cols - 1)
                if start == goal:
                    continue
                expected = bfs_distance(edges, start, goal)

                for heading in HEADINGS:
                    with self.subTest(rows=rows, cols=cols, seed=seed, heading=heading):
                        optimized_path, explore_steps = simulate_phase1(maze, start, heading, goal)
                        speed_steps = simulate_phase2(maze, start, heading, goal, optimized_path)

                        self.assertEqual(speed_steps, expected)
                        self.assertLessEqual(speed_steps, explore_steps)


class BraidedMazeStressTest(unittest.TestCase):
    """Loopy mazes aren't guaranteed to give the left-hand rule the
    shortest path, but exploration and the blind replay must still both
    reach the goal -- in particular phase 2 must never drive into a dead
    end that phase 1's optimizer failed to record."""

    def test_phase1_and_phase2_always_reach_the_goal(self):
        for seed in range(20):
            edges = generate_perfect_maze(6, 6, seed=seed)
            edges = add_random_loops(edges, 6, 6, extra=6, seed=seed + 1000)
            maze = Maze(edges)
            start, goal = (0, 0), (5, 5)

            with self.subTest(seed=seed):
                optimized_path, explore_steps = simulate_phase1(maze, start, 'N', goal)
                speed_steps = simulate_phase2(maze, start, 'N', goal, optimized_path)

                self.assertGreaterEqual(explore_steps, 0)
                self.assertGreaterEqual(speed_steps, 0)


if __name__ == '__main__':
    unittest.main()
