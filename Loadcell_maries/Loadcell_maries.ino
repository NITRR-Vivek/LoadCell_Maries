#include <EEPROM.h>
#include <BluetoothSerial.h>
#include "HX711.h"

const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 4;
const char *pin = "1234";
String device_name = "ESP32-LoadCell";

HX711 scale;

float loaded_val;
float weight;
float zero_val;
float CLF;

bool send_weight = false;

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(500000);
  Serial.println("LoadCell Interfacing with ESP32 ");
  SerialBT.begin(device_name);
  Serial.printf("The device with name \"%s\" is started.\nNow you can pair it with Bluetooth!\n", device_name.c_str());
  #ifdef USE_PIN
    SerialBT.setPin(pin);
    Serial.println("Using PIN");
  #endif
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN); 
  scale.tare();               
}

void loop() {

  handleSerialCommunication(Serial);
  handleSerialCommunication(SerialBT);

  if (send_weight) {
    Serial.println(scale.get_units(3), 1);
    SerialBT.println(scale.get_units(3), 1);
  }
}
void handleSerialCommunication(Stream& stream){
  if (stream.available() > 0) {
    String command = stream.readStringUntil('\n');
    command.trim(); // Remove leading and trailing whitespaces
    processCommand(command);
  }
}

void processCommand(String command) {
  if (command == "ON") {
      EEPROM.begin(sizeof(CLF));
      EEPROM.get(0, CLF);
      EEPROM.end();
      scale.set_scale(CLF);
      send_weight = true;
    } else if (command == "OFF") {
      send_weight = false;
    } else if (command.equals("TARE")) {
      scale.tare();
    } else if (command.equals("ZERO_LOAD")) {
      zero_val = scale.get_units(5);
      SerialBT.println(zero_val);
      Serial.println(zero_val);
    } else if (command.equals("LOADED_VALUE")) { 
      loaded_val = scale.get_units(5);
      Serial.println(loaded_val);
      SerialBT.println(loaded_val);
    } else if (command.equals("GET_LOAD")) {
      while (!Serial.available()) {
        delay(10);
      }
      weight = Serial.parseFloat();
      // Serial.println(weight);
    } else if (command.equals("CALIBRATION_FACTOR")) {
      if (weight != 0.0) {
        CLF = (loaded_val - zero_val) / weight;
        Serial.println(CLF);
        SerialBT.println(CLF);
        
      } else {
        EEPROM.begin(sizeof(CLF)); 
        EEPROM.get(0, CLF); 
        EEPROM.end(); 
        Serial.print("Error: Weight is zero, cannot calculate CLF. Previously Loaded CLF is: ");
        Serial.println(CLF);
        SerialBT.print("Error: Weight is zero, cannot calculate CLF. Previously Loaded CLF is: ");
        SerialBT.println(CLF);

      }
    } else if (command.equals("SET_CALIBRATION")) {
      if (weight != 0.0) {
      // Write CLF value to flash memory
        EEPROM.begin(sizeof(CLF));
        EEPROM.put(0, CLF);
        bool success = EEPROM.commit();
        EEPROM.end();
        if (success) {
          Serial.println("Calibration factor successfully set.");
          SerialBT.println("Calibration factor successfully set.");
        } else {
          Serial.println("Error: Failed to write calibration factor to EEPROM.");
          SerialBT.println("Error: Failed to write calibration factor to EEPROM.");
        }
      }else {
        Serial.println("Error: Weight is zero, cannot set the Calibration factor");
        SerialBT.println("Error: Weight is zero, cannot set the Calibration factor");
      }
    } else if (command.equals("SET_THIS")){
        CLF = -310.47;
        EEPROM.begin(sizeof(CLF));
        EEPROM.put(0, CLF);
        bool success = EEPROM.commit();
        EEPROM.end();
        if (success) {
          Serial.println("Calibration factor is -310.47 set.");
          SerialBT.println("Calibration factor is -310.47 set.");
        } else {
          Serial.println("Error: Failed to write calibration factor to EEPROM.");
          SerialBT.println("Error: Failed to write calibration factor to EEPROM.");
        }
    }
}
