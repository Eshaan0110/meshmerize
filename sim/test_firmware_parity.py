"""Checks that maze_solver.py still matches the firmware sources.

The Python port is only a useful stand-in if it agrees with the .ino code, so
these tests parse the decision tables straight out of meshmerize_sketch/ and
compare them with the port. If someone edits a table on one side only, this
fails.
"""
import itertools
import re
import unittest
from pathlib import Path

from maze_solver import choose_direction, encode_intersection, simplify_turn

SKETCH = Path(__file__).resolve().parent.parent / "meshmerize_sketch"


def _read(name):
    return (SKETCH / name).read_text(encoding="utf-8")


def _function_body(source, signature):
    start = source.index(signature)
    open_brace = source.index("{", start)
    depth = 0
    for i in range(open_brace, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[open_brace + 1:i]
    raise AssertionError("unbalanced braces in " + signature)


class SimplifyTableParityTest(unittest.TestCase):
    def test_table_matches_firmware(self):
        body = _function_body(_read("path_optimizer.ino"), "char simplifyTurn(")
        rules = re.findall(
            r"before == '(\w)' && after == '(\w)'\) return '(\w)'", body)
        self.assertEqual(len(rules), 9)
        firmware = {(b, a): r for b, a, r in rules}
        for before, after in itertools.product("LRSB", repeat=2):
            with self.subTest(before=before, after=after):
                self.assertEqual(simplify_turn(before, after),
                                 firmware.get((before, after)))


class ChooseDirectionParityTest(unittest.TestCase):
    def test_every_type_matches_firmware(self):
        body = _function_body(_read("maze_runner.ino"), "char chooseDirection(")
        cases = {int(n): c for n, c in re.findall(r"case (\d+): return '(\w)'", body)}
        default = re.search(r"default: return '(\w)'", body).group(1)
        for itype in range(8):
            with self.subTest(intersection_type=itype):
                self.assertEqual(choose_direction(itype),
                                 cases.get(itype, default))


class CheckIntersectionParityTest(unittest.TestCase):
    def test_encoding_matches_firmware(self):
        body = _function_body(_read("maze_runner.ino"), "int checkIntersection(")
        rules = re.findall(r"if \(([LRS &]+?)\)\s+return (\d);", body)
        self.assertEqual(len(rules), 7)
        for left, right, straight in itertools.product([False, True], repeat=3):
            env = {"L": left, "R": right, "S": straight}
            expected = 0
            for cond, code in rules:
                if eval(cond.replace("&&", " and "), {"__builtins__": {}}, env):
                    expected = int(code)
                    break
            with self.subTest(left=left, right=right, straight=straight):
                self.assertEqual(encode_intersection(left, right, straight),
                                 expected)


if __name__ == "__main__":
    unittest.main()
