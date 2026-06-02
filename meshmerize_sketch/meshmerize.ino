#include <QTRSensors.h>

// ===== Pin Definitions =====
#define LEFT_MOTOR_PIN1   2
#define LEFT_MOTOR_PIN2   3
#define RIGHT_MOTOR_PIN1  4
#define RIGHT_MOTOR_PIN2  5
#define LEFT_ENCODER_PIN  18
#define RIGHT_ENCODER_PIN 19
#define START_BUTTON_PIN  20

// ===== Sensor Configuration =====
QTRSensors qtr;
const uint8_t SENSOR_COUNT = 8;
uint16_t sensorValues[SENSOR_COUNT];
const uint16_t LINE_THRESHOLD = 900;

// ===== PD Control =====
float KP = 0.12f;
float KD = 0.55f;
int lastError = 0;

// ===== Motor Speed State =====
int leftSpeed  = 0;
int rightSpeed = 0;
const int BASE_SPEED_PHASE1 = 130;
const int BASE_SPEED_PHASE2 = 200;
int baseSpeed = BASE_SPEED_PHASE1;

// ===== Path Storage =====
// Recorded during exploration; simplified in-place by Bellman's algorithm.
char path[200];
int  pathLength = 0;
char optimizedPath[200];
int  optimizedLength = 0;

// ===== Encoder Counts (updated by ISRs) =====
volatile long leftEncoderCount  = 0;
volatile long rightEncoderCount = 0;

// ===== Phase State Machine =====
enum Phase {
  PHASE_CALIBRATE,
  PHASE_EXPLORE,
  PHASE_OPTIMIZE,
  PHASE_SPEEDRUN,
  PHASE_DONE
};
Phase currentPhase = PHASE_CALIBRATE;
int phase2Step = 0;

// ----------------------------------------

void setup() {
  Serial.begin(115200);

  // Motor H-bridge pins
  pinMode(LEFT_MOTOR_PIN1,  OUTPUT);
  pinMode(LEFT_MOTOR_PIN2,  OUTPUT);
  pinMode(RIGHT_MOTOR_PIN1, OUTPUT);
  pinMode(RIGHT_MOTOR_PIN2, OUTPUT);

  // Encoder interrupts for odometry
  pinMode(LEFT_ENCODER_PIN,  INPUT_PULLUP);
  pinMode(RIGHT_ENCODER_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENCODER_PIN),  leftEncoderISR,  RISING);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENCODER_PIN), rightEncoderISR, RISING);

  // Active-low start button
  pinMode(START_BUTTON_PIN, INPUT_PULLUP);

  // QTR sensor array
  qtr.setTypeRC();
  qtr.setSensorPins((const uint8_t[]){30, 31, 32, 33, 34, 35, 36, 37}, SENSOR_COUNT);

  calibrateSensors();

  Serial.println(F("Calibration complete."));
  Serial.println(F("Press button or send 'g' over Serial to start Phase 1."));

  // Block until start signal
  while (digitalRead(START_BUTTON_PIN) == HIGH) {
    if (Serial.available() && Serial.read() == 'g') break;
    delay(10);
  }
  delay(300);

  path[0]          = '\0';
  optimizedPath[0] = '\0';
  currentPhase     = PHASE_EXPLORE;
  Serial.println(F("Phase 1: Exploration started."));
}

void loop() {
  switch (currentPhase) {
    case PHASE_EXPLORE:  exploreLoop();        break;
    case PHASE_OPTIMIZE: optimizeAndPrepare(); break;
    case PHASE_SPEEDRUN: speedRunLoop();       break;
    case PHASE_DONE:     stopMotors();         break;
    default:                                   break;
  }
}

void calibrateSensors() {
  Serial.println(F("Calibrating — sweep robot over the line..."));
  for (uint16_t i = 0; i < 400; i++) {
    qtr.calibrate();
    delay(20);
  }
}
