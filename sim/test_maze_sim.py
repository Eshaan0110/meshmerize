import unittest

from maze_sim import Maze, MazeUnsolvableError, simulate_phase1, simulate_phase2


class StraightCorridorTest(unittest.TestCase):
    def test_no_turns_recorded_on_a_plain_corridor(self):
        maze = Maze([((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (0, 3))])
        path, steps = simulate_phase1(maze, (0, 0), 'E', (0, 3))
        self.assertEqual(path, [])
        self.assertEqual(steps, 3)


class DeadEndBranchTest(unittest.TestCase):
    """A maze with a dead-end spur off the main corridor. The left-hand
    rule explores the spur first (it's a left turn before the straight
    option), backtracks, and the optimizer must fold that detour away so
    phase 2 drives straight past it instead of re-exploring it."""

    def _maze(self):
        return Maze([
            ((0, 0), (0, 1)),
            ((0, 1), (0, 2)),
            ((0, 1), (-1, 1)),   # dead-end spur north of (0,1)
            ((0, 2), (1, 2)),
            ((1, 2), (2, 2)),
            ((2, 2), (2, 3)),
        ])

    def test_phase1_explores_spur_but_optimized_path_omits_it(self):
        maze = self._maze()
        path, steps = simulate_phase1(maze, (0, 0), 'E', (2, 3))
        self.assertEqual(path, ['S', 'R', 'L'])
        self.assertEqual(steps, 7)  # includes the there-and-back trip up the spur

    def test_phase2_blind_replay_skips_the_spur_entirely(self):
        maze = self._maze()
        optimized_path, _ = simulate_phase1(maze, (0, 0), 'E', (2, 3))
        steps = simulate_phase2(maze, (0, 0), 'E', (2, 3), optimized_path)
        self.assertEqual(steps, 5)  # shorter: no detour up the dead end
        self.assertLess(steps, 7)


class UnsolvableMazeTest(unittest.TestCase):
    def test_goal_never_reached_raises(self):
        maze = Maze([((0, 0), (0, 1))])
        with self.assertRaises(MazeUnsolvableError):
            simulate_phase1(maze, (0, 0), 'E', (5, 5), max_steps=20)


if __name__ == '__main__':
    unittest.main()
