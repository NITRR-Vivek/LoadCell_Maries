import tkinter as tk
from tkinter import ttk,Scrollbar
from tkinter import Text
import webbrowser
from hyperlink import URL
from PIL import Image, ImageTk
import pyperclip, os, sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
        # PyInstaller creates a temp folder and stores path in _MEIPAS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
class DocumentationTab:
    def __init__(self, parent):
        self.parent = parent
        self.documentation_tab = ttk.Frame(self.parent)
        self.arduino_code_1 = """
        
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
        
        """
        self.arduino_code_2 = """
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


        """

    def create_documentation_tab(self):

        self.parent.add(self.documentation_tab,text="Doc")
        self.documentation_tab.grid_rowconfigure(0, weight=1)
        self.documentation_tab.grid_columnconfigure(0, weight=1)

        self.scrollable_frame = tk.Frame(self.documentation_tab,bg='blue')
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        self.canvas = tk.Canvas(self.scrollable_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add a scrollbar to the canvas
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.documentation_frame = ttk.Frame(self.canvas)
        self.documentation_frame.config(style="Background.TFrame")
        self.documentation_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.documentation_frame, anchor='center')

        circuit_label = ttk.Label(self.documentation_frame, text="Circuit Diagram", font=("Arial", 16, "bold"), background="white")
        circuit_label.pack(pady=10,anchor="w")
         
        circuit_image = Image.open(resource_path("assets\\circuit.jpg"))
        circuit_image_resized = circuit_image.resize((820, 460))
         
        circuit_photo = ImageTk.PhotoImage(circuit_image_resized)
        circuit_image_label = tk.Label(self.documentation_frame, image=circuit_photo)
        circuit_image_label.image = circuit_photo
        circuit_image_label.pack(fill="both", expand=True, padx=20,pady=10,anchor='center')
 
        circuit_connection = ttk.Label(self.documentation_frame, text="Circuit Connection:", font=("Arial", 16, "bold"), background="white")
        circuit_connection.pack(pady=10,anchor="w")

        connection_text = """
        1. Connection for LoadCell to HX711 Sensor:-
                → Red Wire to E+
                → Black Wire to E-
                → White Wire to A-
                → Green Wire to A+

        2. Connection for HX711 Sensor to ESP32:-
                → GND to GND
                → DT to D2
                → SCK to D4
                → VCC to 3V3

        3. Connect the USB power to ESP32
        """
        circuit_connection_text = tk.Text(self.documentation_frame, wrap="word",bg="white", font=("verdana", 12))
        circuit_connection_text.pack(fill='both',pady=10, expand=True,anchor='w')
        circuit_connection_text.insert("1.0", connection_text)

        steps_label = ttk.Label(self.documentation_frame, text="Step-by-step process:", font=("Arial", 16, "bold"), background="white")
        steps_label.pack(pady=10,anchor="w")

        steps_text = """
        1. Install and open LoadCell.exe software.

        2. Plug the USB cable to the Computer.

        3. If Load Cell is not Caliberated.
            ↪ First Copy and push the ESP32 code below to Check the Caliberation Factor

            ► Check the USB Connection.
            ► Go to DashBoard Tab in the LoadCell.exe Software.
            ► Connect to the Com port if not showing then refresh it.
            ► Go to Setup Tab 
            ► Click on Ok in the Popup Shown
            ► Click on Zeroload Button after 2 sec Ensuring that no Weight is present.
            ► Enter the Value of Known Load to be put on the LoadCell.
            ► Place the Known Load on the LoadCell and Click on Enter after waiting for 2 sec.
            ► Click on Caliberate Button to Know the Caliberation Factor.

            ⛳ The Copy and push the Below ESP32 Code for Weight Measurement replacing the Value of CLF with above obtained caliberation Factor.

        4. If Load Cell is Caliberated.
            ↪ Open the Dashboard Tab

            ► Check the USB Connection.
            ► Connect to the Com port if not showing then refresh it.
            ► Click on START Button to Start taking the weight reading.
            ► Click on STOP Button to Stop taking the weight reading.
            ► Click on TARE Button to reset the Scale to Zero.
            ► Check the Error Log Box for any errors in functioning.

         
        """
        steps_text_label = tk.Label(self.documentation_frame, text=steps_text, justify="left", bg="white", font=("verdana", 12))
        steps_text_label.pack(fill='both',pady=10, expand=True,anchor='w')

        # After the "Step-by-step process" section, add a Text widget for displaying Arduino code
        arduino_code_caliberate = ttk.Label(self.documentation_frame, text="Arduino Code for Caliberation:", font=("Arial", 16, "bold"), background="white")
        arduino_code_caliberate.pack(pady=10, anchor="w")

        arduino1_frame = ttk.Frame(self.documentation_frame)
        arduino1_frame.pack(padx=10, pady=10, fill="both", expand=True, anchor='w')

        # Create a Text widget for displaying Arduino code 1
        arduino_code_caliberate_text = Text(arduino1_frame, wrap="word", bg="white", font=("Courier", 12))
        arduino_code_caliberate_text.pack(side="left", padx=10, pady=10, fill="both", expand=True)

        arduino_code_caliberate_text.insert("1.0", self.arduino_code_1)
        arduino_code_caliberate_text.config(state="disabled", highlightthickness=0, bd=0)

        # Scrollbar for Arduino code 1
        arduino1_scrollbar = Scrollbar(arduino1_frame, orient="vertical", command=arduino_code_caliberate_text.yview)
        arduino1_scrollbar.pack(side="right", fill="y")
        arduino_code_caliberate_text.configure(yscrollcommand=arduino1_scrollbar.set)

        # Copy button for Arduino code 1
        copy_button_1 = ttk.Button(arduino1_frame, text="Copy Arduino Code for calibration", command=self.copy_arduino_code_1)
        copy_button_1.pack(pady=10)

        arduino2_frame = ttk.Frame(self.documentation_frame)
        arduino2_frame.pack(padx=10, pady=10, fill="both", expand=True, anchor='w')

        # Create a Text widget for displaying Arduino code 2
        arduino_code_weight_text = Text(arduino2_frame, wrap="word", bg="white", font=("Courier", 12))
        arduino_code_weight_text.pack(side="left", padx=10, pady=10, fill="both", expand=True)

        arduino_code_weight_text.insert("1.0", self.arduino_code_2)
        arduino_code_weight_text.config(state="disabled", highlightthickness=0, bd=0)

        # Scrollbar for Arduino code 2
        arduino2_scrollbar = Scrollbar(arduino2_frame, orient="vertical", command=arduino_code_weight_text.yview)
        arduino2_scrollbar.pack(side="right", fill="y")
        arduino_code_weight_text.configure(yscrollcommand=arduino2_scrollbar.set)

        # Copy button for Arduino code 2
        copy_button_2 = ttk.Button(arduino2_frame, text="Copy Arduino Code for weight", command=self.copy_arduino_code_2)
        copy_button_2.pack(pady=10)

        # Troubleshooting section
        troubleshooting_label = ttk.Label(self.documentation_frame, text="Troubleshooting:", font=("Arial", 16, "bold"), background="white")
        troubleshooting_label.pack(pady=10, anchor="w")

        troubleshooting_text = """
        If you encounter any issues while using the software, please try the following troubleshooting steps:

        • Check if the load cell is properly connected to the USB port.

        • Ensure that the correct COM port is selected from the dropdown menu.

        • Verify that the load cell is powered and functioning correctly.

        • Check the Error Log Box for any Errors in Functioning.

        • Restart the software and try reconnecting the load cell.

        • Re-Upload the ESP32 Code and Restart the software and try reconnecting the load cell.

        * If still not connecting then check USB serial for Arduino in Device Manager of Your Windows. If not 
          Showing the option then Install CP210x software from internet for ESP32 and CP310x for ESP8266, Arduino UNO etc. then try again.
        """
        troubleshooting_text_label = tk.Label(self.documentation_frame, text=troubleshooting_text, justify="left", bg="white", font=("Arial", 12))
        troubleshooting_text_label.pack(pady=10,fill="both", expand=True)

        # About Us section
        about_us_label = ttk.Label(self.documentation_frame, text="About Us:", font=("Arial", 16, "bold"), background="white")
        about_us_label.pack(pady=10, anchor="w")

        about_us_text = """
        LoadCellApp is developed by Vivek Kumar at NIT Raipur.

        GitHub Repository: github.com/NITRR-Vivek/LoadCell_Maries

        For any inquiries or support, please contact us at:

        • Email: vkumar.btech2022.bme@nitrr.ac.in

        • Phone: +91-9431504216

        • Connect through LinkedIn: www.linkedin.com/in/vivekadvikk
        """

        # Create a Text widget for displaying the text
        about_us_text_widget = Text(self.documentation_frame, wrap="word", bg="white", font=("Arial", 12))
        about_us_text_widget.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        # Insert the text with hyperlinks
        about_us_text_widget.insert("1.0", about_us_text)
        about_us_text_widget.config(state="disabled")

        # Add hyperlinks to the email, website, and GitHub repository
        about_us_text_widget.tag_add("git_link", "4.27", "4.65")
        about_us_text_widget.tag_add("email_link", "8.17", "8.49")
        about_us_text_widget.tag_add("website_link", "12.36", "12.71")

        about_us_text_widget.tag_config("git_link", foreground="blue", underline=True)
        about_us_text_widget.tag_bind("git_link", "<Button-1>", lambda event: self.open_link("https://github.com/NITRR-Vivek/LoadCell_Maries"))

        about_us_text_widget.tag_config("email_link", foreground="blue", underline=True)
        about_us_text_widget.tag_bind("email_link", "<Button-1>", lambda event: self.open_link("mailto:vkumar.btech2022.bme@nitrr.ac.in"))

        about_us_text_widget.tag_config("website_link", foreground="blue", underline=True)
        about_us_text_widget.tag_bind("website_link", "<Button-1>", lambda event: self.open_link("https://www.linkedin.com/in/vivekadvikk/"))
    
    def open_link(self, url):
        webbrowser.open_new(url)   
    def copy_arduino_code_1(self): 
        pyperclip.copy(self.arduino_code_1)       
    def copy_arduino_code_2(self): 
        pyperclip.copy(self.arduino_code_2)       

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")