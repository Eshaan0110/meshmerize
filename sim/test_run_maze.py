import contextlib
import io
import unittest

from run_maze import format_batch, main, run_once


class RunOnceTest(unittest.TestCase):
    def test_perfect_maze_speed_run_is_optimal(self):
        for seed in range(10):
            r = run_once(6, 6, seed, 0, 'E')
            self.assertIsNone(r['error'])
            self.assertEqual(r['speed'], r['optimal'])

    def test_same_seed_is_reproducible(self):
        self.assertEqual(run_once(5, 5, 7, 3, 'E'), run_once(5, 5, 7, 3, 'E'))


class FormatBatchTest(unittest.TestCase):
    def test_summary_counts_failures_and_suboptimal(self):
        rows = [
            {'seed': 0, 'optimal': 10, 'explore': 30, 'speed': 10, 'error': None},
            {'seed': 1, 'optimal': 10, 'explore': 30, 'speed': 14, 'error': None},
            {'seed': 2, 'optimal': 10, 'explore': None, 'speed': None, 'error': 'stuck'},
        ]
        out = format_batch(rows)
        self.assertIn('+4 over optimal', out)
        self.assertIn('FAIL: stuck', out)
        self.assertIn('3 mazes: 2 solved, 1 optimal, 1 failed', out)


class MainTest(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_single_run_prints_both_phases(self):
        code, out = self._run(['--rows', '4', '--cols', '4', '--seed', '1'])
        self.assertEqual(code, 0)
        self.assertIn('Exploration', out)
        self.assertIn('Speed run', out)

    def test_batch_on_perfect_mazes_exits_zero(self):
        code, out = self._run(['--rows', '5', '--cols', '5', '--batch', '5'])
        self.assertEqual(code, 0)
        self.assertIn('5 mazes: 5 solved, 5 optimal, 0 failed', out)


if __name__ == '__main__':
    unittest.main()
