"""Portable re-implementation of the path-recording/simplification logic in
meshmerize_sketch/maze_runner.ino and meshmerize_sketch/path_optimizer.ino.

The embedded code only runs on real hardware, so the exploration and Bellman
path-simplification logic has never been exercised outside of a physical
maze run. This module ports the pure decision logic (no sensors, no motors)
so it can be driven by maze_sim.py and covered by an offline test suite.
"""

from typing import List, Optional

# Intersection types, matching checkIntersection() in maze_runner.ino
DEAD_END = 0
STRAIGHT_ONLY = 1
RIGHT_ONLY = 2
LEFT_ONLY = 3
T_JUNCTION = 4
RIGHT_AND_STRAIGHT = 5
LEFT_AND_STRAIGHT = 6
FOUR_WAY = 7


def encode_intersection(left: bool, right: bool, straight: bool) -> int:
    """Mirrors checkIntersection(): combine L/S/R sensor bits into a type 0-7."""
    if left and right and straight:
        return FOUR_WAY
    if left and straight:
        return LEFT_AND_STRAIGHT
    if right and straight:
        return RIGHT_AND_STRAIGHT
    if left and right:
        return T_JUNCTION
    if left:
        return LEFT_ONLY
    if right:
        return RIGHT_ONLY
    if straight:
        return STRAIGHT_ONLY
    return DEAD_END


def choose_direction(intersection_type: int) -> str:
    """Mirrors chooseDirection(): left-hand rule, L > S > R > B."""
    return {
        FOUR_WAY: 'L',
        LEFT_AND_STRAIGHT: 'L',
        RIGHT_AND_STRAIGHT: 'S',
        T_JUNCTION: 'L',
        LEFT_ONLY: 'L',
        RIGHT_ONLY: 'R',
        STRAIGHT_ONLY: 'S',
    }.get(intersection_type, 'B')


def simplify_turn(before: str, after: str) -> Optional[str]:
    """Mirrors simplifyTurn(): collapses an (x, B, y) triplet into one turn."""
    table = {
        ('L', 'R'): 'B',
        ('L', 'S'): 'R',
        ('L', 'L'): 'S',
        ('R', 'L'): 'B',
        ('R', 'S'): 'L',
        ('R', 'R'): 'S',
        ('S', 'L'): 'R',
        ('S', 'R'): 'L',
        ('S', 'S'): 'B',
    }
    return table.get((before, after))


def record_and_simplify(path: List[str], decision: str) -> List[str]:
    """Mirrors recordAndSimplify()/trySimplifyPath(): append `decision` to
    `path` and collapse any reducible (x, B, y) suffix, repeatedly.
    Returns the same list object, mutated in place, for convenience.
    """
    path.append(decision)
    if decision == 'B':
        return path

    while len(path) >= 3 and path[-2] == 'B':
        simplified = simplify_turn(path[-3], path[-1])
        if simplified is None:
            break
        del path[-3:]
        path.append(simplified)

    return path
