#include <QTRSensors.h>

// Motor and encoder pins
#define LEFT_MOTOR_PIN1 2
#define LEFT_MOTOR_PIN2 3
#define RIGHT_MOTOR_PIN1 4
#define RIGHT_MOTOR_PIN2 5
#define LEFT_ENCODER_PIN 18
#define RIGHT_ENCODER_PIN 19

// PD constants
#define KP 0.1
#define KD 0.5

// Sensor array
QTRSensors qtr;
const uint8_t SensorCount = 8;
uint16_t sensorValues[SensorCount];

// Motor control variables
int leftSpeed = 0;
int rightSpeed = 0;
const int baseSpeed = 150;

// Error variable
int lastError = 0;

// Maze solving variables
char path[100];
int pathLength = 0;

// Threshold to detect white line
const int threshold = 900;

void setup(){
  // Pin configurations
  pinMode(LEFT_MOTOR_PIN1, OUTPUT);
  pinMode(LEFT_MOTOR_PIN2, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN1, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN2, OUTPUT);
  pinMode(LEFT_ENCODER_PIN, INPUT_PULLUP);
  pinMode(RIGHT_ENCODER_PIN, INPUT_PULLUP);

  // Configure sensor array
  qtr.setTypeRC();
  qtr.setSensorPins((const uint8_t[]){30, 31, 32, 33, 34, 35, 36, 37}, SensorCount);
  
  calibrateSensors();

  Serial.begin(9600);
}

void loop(){
  // Read sensor values
  uint16_t position = qtr.readLineWhite(sensorValues);

  // PD calculation
  int error = position - 3500;
  int derivative = error - lastError;
  int motorSpeed = KP * error + KD * derivative;

  leftSpeed = baseSpeed + motorSpeed;
  rightSpeed = baseSpeed - motorSpeed;

  leftSpeed = constrain(leftSpeed, 50, 255);
  rightSpeed = constrain(rightSpeed, 50, 255);

  // Check for intersection
  int intersectionType = checkIntersection();
  if (intersectionType != 1){
    handleIntersection(intersectionType);
  }

  // Always use PID-controlled motor speeds
  driveMotors(leftSpeed, rightSpeed);

  lastError = error;
}

void calibrateSensors(){
  for (uint16_t i = 0; i < 400; i++){
    qtr.calibrate();
    delay(20);
  }
}

void driveMotors(int left, int right){
  // H-bridge: negative speed drives the motor in reverse via the second pin
  if (left >= 0) {
    analogWrite(LEFT_MOTOR_PIN1, constrain(left, 0, 255));
    analogWrite(LEFT_MOTOR_PIN2, 0);
  } else {
    analogWrite(LEFT_MOTOR_PIN1, 0);
    analogWrite(LEFT_MOTOR_PIN2, constrain(-left, 0, 255));
  }

  if (right >= 0) {
    analogWrite(RIGHT_MOTOR_PIN1, constrain(right, 0, 255));
    analogWrite(RIGHT_MOTOR_PIN2, 0);
  } else {
    analogWrite(RIGHT_MOTOR_PIN1, 0);
    analogWrite(RIGHT_MOTOR_PIN2, constrain(-right, 0, 255));
  }
}

int checkIntersection(){
  bool left = sensorValues[0] > threshold;
  bool right = sensorValues[7] > threshold;
  bool straight = (sensorValues[3] > threshold || sensorValues[4] > threshold);
  
  if (left && right && straight) return 7;  // 4-way intersection
  if (left && straight) return 6;
  if (right && straight) return 5;
  if (left && right) return 4; // T junction
  if (left) return 3;
  if (right) return 2;
  if (straight) return 1; // no intersection
  if (!left && !right && !straight) return 0; // dead end
}

void handleIntersection(int intersectionType){
  // Slow down or stop briefly
  int currentLeft = leftSpeed;
  int currentRight = rightSpeed;
  driveMotors(currentLeft / 2, currentRight / 2);
  delay(50);

  switch (intersectionType){
    case 7: // 4-way intersection
    case 6: // Left and straight
    case 4: // T junction
    case 3: // Left only
      turnLeft();
      path[pathLength++] = 'L';
      break;
    case 5: // Right and straight
      // Continue straight
      path[pathLength++] = 'S';
      break;
    case 2: // Right only
      turnRight();
      path[pathLength++] = 'R';
      break;
    case 0: // Dead end
      turnAround();
      path[pathLength++] = 'B';
      break;
  }

  // Resume PID-controlled speed
  driveMotors(currentLeft, currentRight);
}

void turnLeft(){
  while (sensorValues[0] > threshold || sensorValues[1] > threshold){
    qtr.readLineWhite(sensorValues);
    int error = sensorValues[0] - sensorValues[7];
    int derivative = error - lastError;
    int motorSpeed = KP * error + KD * derivative;
    
    leftSpeed = -baseSpeed + motorSpeed;
    rightSpeed = baseSpeed + motorSpeed;
    
    leftSpeed = constrain(leftSpeed, -255, 255);
    rightSpeed = constrain(rightSpeed, -255, 255);
    
    driveMotors(leftSpeed, rightSpeed);
    
    lastError = error;
  }
}

void turnRight(){
  while (sensorValues[7] > threshold || sensorValues[6] > threshold){
    qtr.readLineWhite(sensorValues);
    int error = sensorValues[7] - sensorValues[0];
    int derivative = error - lastError;
    int motorSpeed = KP * error + KD * derivative;
    
    leftSpeed = baseSpeed + motorSpeed;
    rightSpeed = -baseSpeed + motorSpeed;
    
    leftSpeed = constrain(leftSpeed, -255, 255);
    rightSpeed = constrain(rightSpeed, -255, 255);
    
    driveMotors(leftSpeed, rightSpeed);
    
    lastError = error;
  }
}

void turnAround(){
  // First, turn right until we lose the line
  while (sensorValues[3] > threshold || sensorValues[4] > threshold){
    qtr.readLineWhite(sensorValues);
    driveMotors(baseSpeed, -baseSpeed);
  }
  // Then, turn right until we find the line again
  while (sensorValues[3] < threshold && sensorValues[4] < threshold){
    qtr.readLineWhite(sensorValues);
    driveMotors(baseSpeed, -baseSpeed);
  }
}
