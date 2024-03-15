#include <EEPROM.h>
#include <BluetoothSerial.h>
#include "HX711.h"

const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 4;
const char *pin = "1234";
String device_name = "ESP32-LoadCell";

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Bluetooth not available or not enabled. It is only available for the ESP32 chip.
#endif


HX711 scale;

float loaded_val;
float weight;
float zero_val;
float CLF;

bool send_weight = false;

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
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
  //USB Serial Comm
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove leading and trailing whitespaces
    processCommand(command);
  }
  
  // Bluetooth Serial Comm
  if (SerialBT.available() > 0) {
    String command = SerialBT.readStringUntil('\n');
    command.trim(); // Remove leading and trailing whitespaces
    processCommand(command);
  }

  if (send_weight) {
    Serial.println(scale.get_units(10), 1);
    scale.power_down();
    delay(10);
    scale.power_up();
  }
}

void processCommand(String command) {
  if (command == "ON") {
      // Read CLF value from flash memory and set the scale
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
      Serial.println(zero_val);
    } else if (command.equals("LOADED_VALUE")) { 
      loaded_val = scale.get_units(5);
      Serial.println(loaded_val);
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
      } else {
        Serial.println("Error: Weight is zero, cannot calculate CLF");
      }
    } else if (command.equals("SET_CALIBRATION")) {
      // Write CLF value to flash memory
      EEPROM.begin(sizeof(CLF));
      EEPROM.put(0, CLF);
      EEPROM.commit();
      EEPROM.end();
    }
}
