// Phase 1: Left-Hand Rule exploration with live path simplification.
// Phase 2: High-speed re-run using the pre-computed optimal path.

// ===== SHARED HELPERS =====

// Returns intersection type based on current sensorValues[]:
//   0 = dead end          1 = straight only
//   2 = right only        3 = left only
//   4 = T-junction (L+R)  5 = right + straight
//   6 = left + straight   7 = 4-way
int checkIntersection() {
  bool L = sensorValues[0] > LINE_THRESHOLD;
  bool R = sensorValues[7] > LINE_THRESHOLD;
  bool S = sensorValues[3] > LINE_THRESHOLD || sensorValues[4] > LINE_THRESHOLD;

  if (L && R && S) return 7;
  if (L && S)      return 6;
  if (R && S)      return 5;
  if (L && R)      return 4;
  if (L)           return 3;
  if (R)           return 2;
  if (S)           return 1;
  return 0;
}

// Maze end: ≥6 sensors simultaneously white → wide end-zone marker.
bool isMazeEnd() {
  int whiteCount = 0;
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    if (sensorValues[i] > LINE_THRESHOLD) whiteCount++;
  }
  return whiteCount >= 6;
}


// ===== PHASE 1: EXPLORATION =====

// Left-hand rule: prefer L > S > R > B.
// Guarantees exit from any simply-connected maze.
static char chooseDirection(int intersectionType) {
  switch (intersectionType) {
    case 7: return 'L';
    case 6: return 'L';
    case 5: return 'S';
    case 4: return 'L';
    case 3: return 'L';
    case 2: return 'R';
    case 1: return 'S';
    default: return 'B';
  }
}

static void executeDecision(char decision) {
  switch (decision) {
    case 'L': turnLeft();   break;
    case 'R': turnRight();  break;
    case 'B': turnAround(); break;
    default:                break;
  }
}

void exploreLoop() {
  uint16_t position = qtr.readLineWhite(sensorValues);

  if (isMazeEnd()) {
    Serial.println(F("End marker found — switching to path optimisation."));
    stopMotors();
    delay(500);
    currentPhase = PHASE_OPTIMIZE;
    return;
  }

  // PD line-following
  int error      = (int)position - 3500;
  int derivative = error - lastError;
  int motorSpeed = (int)(KP * error + KD * derivative);

  leftSpeed  = constrain(baseSpeed + motorSpeed, 50, 255);
  rightSpeed = constrain(baseSpeed - motorSpeed, 50, 255);

  int iType = checkIntersection();

  if (iType != 1) {
    // Advance to intersection centre before turning
    advanceToCenter();
    qtr.readLineWhite(sensorValues);
    iType = checkIntersection();

    char decision = chooseDirection(iType);
    executeDecision(decision);
    recordAndSimplify(decision);

    Serial.print(F("Intersection "));
    Serial.print(iType);
    Serial.print(F(" -> "));
    Serial.print(decision);
    Serial.print(F("  path: "));
    Serial.println(path);
  } else {
    driveMotors(leftSpeed, rightSpeed);
  }

  lastError = error;
}


// ===== PHASE TRANSITION =====

void optimizeAndPrepare() {
  buildOptimizedPath();
  Serial.println(F("Speed run begins in 3 s..."));
  delay(3000);

  baseSpeed    = BASE_SPEED_PHASE2;
  phase2Step   = 0;
  lastError    = 0;
  currentPhase = PHASE_SPEEDRUN;
}


// ===== PHASE 2: OPTIMISED SPEED RUN =====

void speedRunLoop() {
  uint16_t position = qtr.readLineWhite(sensorValues);

  if (isMazeEnd()) {
    Serial.println(F("Speed run complete!"));
    stopMotors();
    currentPhase = PHASE_DONE;
    return;
  }

  // PD line-following at phase-2 base speed
  int error      = (int)position - 3500;
  int derivative = error - lastError;
  int motorSpeed = (int)(KP * error + KD * derivative);

  driveMotors(constrain(baseSpeed + motorSpeed, 50, 255),
              constrain(baseSpeed - motorSpeed, 50, 255));
  lastError = error;

  // Once all pre-computed decisions are consumed, just follow the line to the end.
  if (phase2Step >= optimizedLength) return;

  int iType = checkIntersection();
  if (iType == 1 || iType == 0) return;  // not at a decision point

  advanceToCenter();
  qtr.readLineWhite(sensorValues);

  char decision = optimizedPath[phase2Step++];

  Serial.print(F("Step "));
  Serial.print(phase2Step);
  Serial.print(F(": "));
  Serial.println(decision);

  switch (decision) {
    case 'L': turnLeftFast();  break;
    case 'R': turnRightFast(); break;
    case 'B': turnAround();    break;
    default:                   break;
  }
  lastError = 0;
}
