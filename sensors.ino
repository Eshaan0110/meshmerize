#include <QTRSensors.h>

// Sensor array
QTRSensors qtr;
const uint8_t SensorCount = 8;
uint16_t sensorValues[SensorCount];

void setup(){
  // Configure sensor array
  qtr.setTypeRC();
  qtr.setSensorPins((const uint8_t[]){30, 31, 32, 33, 34, 35, 36, 37}, SensorCount);
  
  calibrateSensors();

  Serial.begin(9600);
}

void loop(){
  // Read sensor values
  uint16_t position = qtr.readLineWhite(sensorValues);

  for(int i = 0; i < SensorCount; i++){
    Serial.print(sensorValues[i]);
    Serial.print("\t");
  }
  Serial.println();
}

void calibrateSensors(){
  for (uint16_t i = 0; i < 400; i++){
    qtr.calibrate();
    delay(20);
  }
}
