# LoadCell
Hello EveryOne, This repository is all about a custom weight measurement system and analysis using a arduino device, a LoadCell sensor and a software.

This is a LoadCell Software made my me for taking the input of LoadCell reading through the USB Serial port and one can analyse it for weight or can be analysed for force. The Weight data measured through this can also be saved for future use.
<div style="text-align:center;">
  <img src="https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/LoadCell.gif" width="600" height="318.75" />
</div>

----
# Contents
- [Contents](#contents)
- [Steps](#steps)
- [Connections and Wiring](#connections-and-wiring)
- [Links and Downloads](#links-and-downloads)
- [Arduino Code](#arduino-code)
- [Screenshots](#screenshots)
# Steps
Please follow these steps carefully :-
- Please make the Circuit Connections as given below and download the drivers as per device.
- Download the Setup file for the software given below.
- Load the code below to the arduino device also code is present inside the documentation tab of the LoadCell software.
- Open the LoadCell Software.
- Check the Calibration factor of your LoadCell device.
- If it is not calibrated then set it using the LoadCell software once.
- Check all the wiring and Connections and then connect the usb port.
- Click on the start button and wait for 2-3 sec so that LoadCell Sensor can become stable.
- CLick on TARE button if it is not stable at 0.
- Now put the weight on the LoadCell and Measure it.
- Click Stop button whenever wants to stop.
- On Clicking on stop button a prompt will be opened for saving the measured reading in CSV file.
- Click on Yes to save the readings otherwise Click on No.
- Enter the Filename and and Folder location to save the reading in csv file with fist column date and time and next column weight reading.


# Connections and Wiring
----
![Circuit Diagram](https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/circuit.png)

----
# Links and Downloads
1. Link for ESP32 Device Manager Board
```shell
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```
2. Download the [CP2102 Driver](https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip) for ESP32 and [CH340 Driver](https://sparks.gogo.co.nz/assets/_site_/downloads/CH34x_Install_Windows_v3_4.zip) for ESP8266 or Arduino for Serial Port Communication.
3. Download the [Software Setup](https://drive.google.com/drive/folders/11rlzUg8vEsF-RtYvvoQi67E6c0J1mg2v?usp=drive_link) File

# Arduino Code
1. ESP32 Code for LoadCell.
```arduino
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

```

# Screenshots
----
Fig1: Installing the Setup File of this software

![Installing the Setup File of this software](https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/2.png)
----
Fig2: Main Screen for Discovering and connecting USB Serial Ports

![Main Screen](https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/main_screen.png)
----
Fig3: Setup Screen for Calibration Factor of LoadCell

![Setup Screen](https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/setup.png)
----
Fig4: Measuring Weights using LoadCell-ESP32-USB-Port

![Measuring Weights](https://github.com/NITRR-Vivek/LoadCell_Maries/blob/main/screenshots/weights.png)
----
