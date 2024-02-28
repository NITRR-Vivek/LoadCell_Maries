#include "HX711.h"

const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 4;

float CLF = -311.24;

HX711 scale;

bool send_weight = false;

 void setup() {
  Serial.begin(57600);
  Serial.println("Load Cell Interfacing with ESP32 ");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(CLF);
  scale.tare();
}

void loop() {
 if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove leading and trailing whitespaces
    if (command.equals("TARE")) {
      scale.tare();
    }else if (command.equals("ON")) {
      send_weight = true;
 
    } else if (command.equals("OFF")) {
      send_weight = false;
 
    } 
  }
  if (send_weight) {
    Serial.println(scale.get_units(10), 1);
    scale.power_down();			        // put the ADC in sleep mode
    delay(1000);
    scale.power_up();
  } 
}
