// H-bridge motor control with forward/reverse support and encoder ISRs.
// Turns use a pivot-until-line strategy: spin until the center sensors
// re-acquire the new line segment, removing dependency on fixed timing.

void driveMotors(int left, int right) {
  if (left >= 0) {
    analogWrite(LEFT_MOTOR_PIN1, constrain(left,  0, 255));
    analogWrite(LEFT_MOTOR_PIN2, 0);
  } else {
    analogWrite(LEFT_MOTOR_PIN1, 0);
    analogWrite(LEFT_MOTOR_PIN2, constrain(-left, 0, 255));
  }

  if (right >= 0) {
    analogWrite(RIGHT_MOTOR_PIN1, constrain(right,  0, 255));
    analogWrite(RIGHT_MOTOR_PIN2, 0);
  } else {
    analogWrite(RIGHT_MOTOR_PIN1, 0);
    analogWrite(RIGHT_MOTOR_PIN2, constrain(-right, 0, 255));
  }
}

void stopMotors() {
  analogWrite(LEFT_MOTOR_PIN1,  0);
  analogWrite(LEFT_MOTOR_PIN2,  0);
  analogWrite(RIGHT_MOTOR_PIN1, 0);
  analogWrite(RIGHT_MOTOR_PIN2, 0);
}

// Encoder ISRs — counts used for odometry and precise speed regulation.
void leftEncoderISR()  { leftEncoderCount++;  }
void rightEncoderISR() { rightEncoderCount++; }

// ---- Internal pivot helper ----
// Pivots at the given power for at least holdMs, then waits until the two
// centre sensors are back on a white line (re-acquisition).
static void pivotUntilLine(int leftPwr, int rightPwr, uint16_t holdMs) {
  driveMotors(leftPwr, rightPwr);
  delay(holdMs);
  do {
    qtr.readLineWhite(sensorValues);
  } while (sensorValues[3] < LINE_THRESHOLD && sensorValues[4] < LINE_THRESHOLD);
  stopMotors();
  lastError = 0;
}

// ---- Phase 1 turns (conservative speed) ----
void turnLeft()   { pivotUntilLine(-BASE_SPEED_PHASE1,  BASE_SPEED_PHASE1, 150); }
void turnRight()  { pivotUntilLine( BASE_SPEED_PHASE1, -BASE_SPEED_PHASE1, 150); }
void turnAround() { pivotUntilLine( BASE_SPEED_PHASE1, -BASE_SPEED_PHASE1, 260); }

// ---- Phase 2 turns (higher speed) ----
void turnLeftFast()  { pivotUntilLine(-BASE_SPEED_PHASE2,  BASE_SPEED_PHASE2, 110); }
void turnRightFast() { pivotUntilLine( BASE_SPEED_PHASE2, -BASE_SPEED_PHASE2, 110); }

// Drive forward a short burst to place the robot's pivot point over the
// intersection centre before rotating, improving turn accuracy.
void advanceToCenter() {
  driveMotors(baseSpeed, baseSpeed);
  delay(80);
}
