import unittest

from maze_generator import add_random_loops, bfs_distance, generate_perfect_maze
from maze_sim import Maze, simulate_phase1, simulate_phase2
from map_optimizer import explored_graph, mapped_path, shortest_cell_path


class MapOptimizerTest(unittest.TestCase):
    def test_route_on_simple_graph(self):
        graph = explored_graph([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0), (0, 1), (0, 2)])
        self.assertEqual(shortest_cell_path(graph, (0, 0), (0, 2)), [(0, 0), (0, 1), (0, 2)])

    def test_replay_matches_shortest_route_through_explored_cells(self):
        for seed in range(40):
            edges = add_random_loops(generate_perfect_maze(8, 8, seed=seed), 8, 8, 10, seed=seed)
            maze, goal = Maze(edges), (7, 7)
            trace = []
            simulate_phase1(maze, (0, 0), 'E', goal, trace=trace)
            expected = len(shortest_cell_path(explored_graph(trace), (0, 0), goal)) - 1
            speed = simulate_phase2(maze, (0, 0), 'E', goal, mapped_path(maze, (0, 0), 'E', goal))
            with self.subTest(seed=seed):
                self.assertEqual(speed, expected)
                self.assertGreaterEqual(speed, bfs_distance(edges, (0, 0), goal))

    def test_strictly_beats_left_hand_on_some_braided_mazes(self):
        gains = 0
        for seed in range(40):
            edges = add_random_loops(generate_perfect_maze(8, 8, seed=seed), 8, 8, 10, seed=seed)
            maze, goal = Maze(edges), (7, 7)
            lh_path, _ = simulate_phase1(maze, (0, 0), 'E', goal)
            lh = simulate_phase2(maze, (0, 0), 'E', goal, lh_path)
            gains += simulate_phase2(maze, (0, 0), 'E', goal, mapped_path(maze, (0, 0), 'E', goal)) < lh
        self.assertGreater(gains, 0)

    def test_never_slower_than_left_hand_path(self):
        for seed in range(40):
            edges = add_random_loops(generate_perfect_maze(8, 8, seed=seed), 8, 8, 10, seed=seed)
            maze, goal = Maze(edges), (7, 7)
            lh_path, _ = simulate_phase1(maze, (0, 0), 'E', goal)
            lh = simulate_phase2(maze, (0, 0), 'E', goal, lh_path)
            mapped = simulate_phase2(maze, (0, 0), 'E', goal, mapped_path(maze, (0, 0), 'E', goal))
            self.assertLessEqual(mapped, lh)


if __name__ == '__main__':
    unittest.main()
