// Bellman path simplification for two-phase maze solving.
//
// During Phase 1 the robot records every intersection decision as one of:
//   'L' (left)  'R' (right)  'S' (straight)  'B' (dead-end / turned back)
//
// Whenever the robot backs out of a dead-end and makes the NEXT turn, the
// three-entry pattern (before, 'B', after) collapses into a single equivalent
// turn.  For example: going Left, hitting a dead-end, then turning Right is
// exactly the same as having turned Back at the original intersection, so
// L-B-R → B.  Simplifying continuously as the path is built means Phase 2
// sees only the optimal sequence, with no dead-end detours at all.
//
// Derivation (robot heading North, intersection offers N/S/E/W exits):
//   L B R  → went W, returned heading E, went S  → net = B
//   L B S  → went W, returned heading E, went E  → net = R
//   L B L  → went W, returned heading E, went N  → net = S
//   R B L  → went E, returned heading W, went S  → net = B
//   R B S  → went E, returned heading W, went W  → net = L
//   R B R  → went E, returned heading W, went N  → net = S
//   S B L  → went N, returned heading S, went E  → net = R
//   S B R  → went N, returned heading S, went W  → net = L
//   S B S  → went N, returned heading S, went S  → net = B

static char simplifyTurn(char before, char after) {
  if (before == 'L' && after == 'R') return 'B';
  if (before == 'L' && after == 'S') return 'R';
  if (before == 'L' && after == 'L') return 'S';
  if (before == 'R' && after == 'L') return 'B';
  if (before == 'R' && after == 'S') return 'L';
  if (before == 'R' && after == 'R') return 'S';
  if (before == 'S' && after == 'L') return 'R';
  if (before == 'S' && after == 'R') return 'L';
  if (before == 'S' && after == 'S') return 'B';
  return '\0';
}

// Collapse all reducible (x B y) triplets from the end of `path[]` inward.
// Runs in a loop because one simplification can expose another:
//   e.g. "L B L B R" → "S B R" → "L"
static void trySimplifyPath() {
  while (pathLength >= 3 && path[pathLength - 2] == 'B') {
    char simplified = simplifyTurn(path[pathLength - 3], path[pathLength - 1]);
    if (simplified == '\0') break;
    pathLength -= 3;
    path[pathLength++] = simplified;
    path[pathLength]   = '\0';
  }
}

// Append a decision to `path[]` and immediately try to simplify the suffix.
// Simplification only triggers after a non-B turn (needs a complete x-B-y triple).
void recordAndSimplify(char decision) {
  path[pathLength++] = decision;
  path[pathLength]   = '\0';
  if (decision != 'B') trySimplifyPath();
}

// Finalise: copy the simplified path into `optimizedPath[]` and print it.
void buildOptimizedPath() {
  optimizedLength = pathLength;
  for (int i = 0; i < pathLength; i++) optimizedPath[i] = path[i];
  optimizedPath[optimizedLength] = '\0';

  Serial.print(F("Recorded path:  ")); Serial.println(path);
  Serial.print(F("Optimized path: ")); Serial.println(optimizedPath);
  Serial.print(F("Steps in run:   ")); Serial.println(optimizedLength);
}
