import unittest

from maze_solver import (
    DEAD_END, FOUR_WAY, LEFT_AND_STRAIGHT, LEFT_ONLY, RIGHT_AND_STRAIGHT,
    RIGHT_ONLY, STRAIGHT_ONLY, T_JUNCTION, choose_direction,
    encode_intersection, record_and_simplify, simplify_turn,
)


class EncodeIntersectionTest(unittest.TestCase):
    def test_all_eight_combinations(self):
        cases = {
            (False, False, False): DEAD_END,
            (False, False, True): STRAIGHT_ONLY,
            (False, True, False): RIGHT_ONLY,
            (True, False, False): LEFT_ONLY,
            (True, True, False): T_JUNCTION,
            (True, False, True): LEFT_AND_STRAIGHT,
            (False, True, True): RIGHT_AND_STRAIGHT,
            (True, True, True): FOUR_WAY,
        }
        for (left, right, straight), expected in cases.items():
            with self.subTest(left=left, right=right, straight=straight):
                self.assertEqual(encode_intersection(left, right, straight), expected)


class ChooseDirectionTest(unittest.TestCase):
    def test_left_hand_priority(self):
        self.assertEqual(choose_direction(FOUR_WAY), 'L')
        self.assertEqual(choose_direction(LEFT_AND_STRAIGHT), 'L')
        self.assertEqual(choose_direction(T_JUNCTION), 'L')
        self.assertEqual(choose_direction(LEFT_ONLY), 'L')
        self.assertEqual(choose_direction(RIGHT_AND_STRAIGHT), 'S')
        self.assertEqual(choose_direction(STRAIGHT_ONLY), 'S')
        self.assertEqual(choose_direction(RIGHT_ONLY), 'R')
        self.assertEqual(choose_direction(DEAD_END), 'B')


class SimplifyTurnTest(unittest.TestCase):
    def test_derivation_table(self):
        # Table straight from the header comment in path_optimizer.ino.
        expected = {
            ('L', 'R'): 'B', ('L', 'S'): 'R', ('L', 'L'): 'S',
            ('R', 'L'): 'B', ('R', 'S'): 'L', ('R', 'R'): 'S',
            ('S', 'L'): 'R', ('S', 'R'): 'L', ('S', 'S'): 'B',
        }
        for (before, after), expected_result in expected.items():
            with self.subTest(before=before, after=after):
                self.assertEqual(simplify_turn(before, after), expected_result)

    def test_unlisted_pairs_return_none(self):
        self.assertIsNone(simplify_turn('B', 'L'))
        self.assertIsNone(simplify_turn('L', 'B'))
        self.assertIsNone(simplify_turn('B', 'B'))


class RecordAndSimplifyTest(unittest.TestCase):
    def test_single_dead_end_collapses(self):
        path = []
        for decision in "LBR":
            record_and_simplify(path, decision)
        self.assertEqual(path, ['B'])

    def test_cascading_simplification(self):
        # "L B L B R" -> "S B R" -> "L", per path_optimizer.ino's comment.
        path = []
        for decision in "LBLBR":
            record_and_simplify(path, decision)
        self.assertEqual(path, ['L'])

    def test_double_dead_end_does_not_simplify_across_two_backs(self):
        path = []
        for decision in "BBL":
            record_and_simplify(path, decision)
        self.assertEqual(path, ['B', 'B', 'L'])

    def test_straight_runs_are_left_untouched(self):
        path = []
        for decision in "SRS":
            record_and_simplify(path, decision)
        self.assertEqual(path, ['S', 'R', 'S'])

    def test_empty_path_with_single_backtrack(self):
        path = []
        record_and_simplify(path, 'B')
        self.assertEqual(path, ['B'])


if __name__ == '__main__':
    unittest.main()
