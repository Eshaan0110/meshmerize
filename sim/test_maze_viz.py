import unittest

from maze_viz import render_maze, render_run


class RenderMazeTest(unittest.TestCase):
    def test_open_corridor_has_no_internal_walls(self):
        edges = [((0, 0), (0, 1)), ((0, 1), (0, 2))]
        rendered = render_maze(edges, rows=1, cols=3)
        lines = rendered.splitlines()
        self.assertEqual(lines[0], '+---+---+---+')
        self.assertEqual(lines[1], '|           |')
        self.assertEqual(lines[2], '+---+---+---+')

    def test_missing_edge_draws_internal_wall(self):
        edges = [((0, 0), (0, 1))]  # no edge between (0,1) and (0,2)
        rendered = render_maze(edges, rows=1, cols=3)
        lines = rendered.splitlines()
        self.assertEqual(lines[1], '|       |   |')

    def test_start_goal_and_trace_markers(self):
        edges = [((0, 0), (0, 1)), ((0, 1), (0, 2))]
        rendered = render_maze(edges, rows=1, cols=3, trace=[(0, 0), (0, 1), (0, 2)])
        lines = rendered.splitlines()
        self.assertEqual(lines[1], '| S   *   G |')

    def test_explicit_start_goal_override_trace_endpoints(self):
        edges = [((0, 0), (0, 1)), ((0, 1), (0, 2))]
        rendered = render_maze(edges, rows=1, cols=3, trace=[(0, 1)], start=(0, 0), goal=(0, 2))
        lines = rendered.splitlines()
        self.assertEqual(lines[1], '| S   *   G |')


class RenderRunTest(unittest.TestCase):
    def test_reports_both_phases_and_a_shorter_speed_run(self):
        edges = [
            ((0, 0), (0, 1)),
            ((0, 1), (0, 2)),
            ((0, 1), (-1, 1)),
            ((0, 2), (1, 2)),
            ((1, 2), (2, 2)),
            ((2, 2), (2, 3)),
        ]
        rendered = render_run(edges, rows=3, cols=4, start=(0, 0), start_heading='E', goal=(2, 3))
        self.assertIn('Exploration (7 steps):', rendered)
        self.assertIn("Optimized path: ['S', 'R', 'L']", rendered)
        self.assertIn('Speed run (5 steps):', rendered)


if __name__ == '__main__':
    unittest.main()
