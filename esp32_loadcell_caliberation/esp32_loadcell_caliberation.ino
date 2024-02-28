
#include "HX711.h"

const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 4;

float loaded_val;
float weight;
float zero_val;
float CLF;

HX711 scale;

 void setup() {
  Serial.begin(57600);
  Serial.println("Load Cell Interfacing with ESP32 ");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.tare();
}

void loop() {
 if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command.equals("ZERO_LOAD")) {
      zero_val = scale.get_units(5);
      Serial.println(zero_val);
    } else if (command.equals("LOADED_VALUE")) { 
      loaded_val = scale.get_units(5);
      Serial.println(loaded_val);
    } else if (command.equals("GET_LOAD")) {
    
        while (!Serial.available()) {
            delay(100);
        }
        weight = Serial.parseFloat();
        // Serial.println(weight);

        } else if (command.equals("CALIBRATION_FACTOR")){

            if (weight != 0.0) {
              CLF = (loaded_val - zero_val) / weight;
              Serial.println(CLF);
            } else {
              Serial.println("Error: Weight is zero, cannot calculate CLF");
              }
        }
    }
    delay(200);
}


        