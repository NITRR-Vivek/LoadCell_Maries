import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
from collections import deque
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from documentation import DocumentationTab
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os, sys, csv
from datetime import datetime
import threading

show_weight = True
# pyinstaller --name LoadCell --onefile --windowed --icon=icon.ico  --upx-dir="C:\Users\VIVEK KUMAR\Downloads\upx-4.2.2-win64\upx-4.2.2-win64" --clean myapp.py

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
        # PyInstaller creates a temp folder and stores path in _MEIPAS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class LoadCellApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.is_closed = False
        self.weight_value = tk.StringVar()
        self.sample_weight = tk.StringVar()
        self.calibration_factor = tk.StringVar()

        self.title("LoadCell.exe")
        self.minsize(600, 400)
        self.iconbitmap(resource_path('icon.ico'))

        # Create a canvas covering the entire window
        self.canvas = tk.Canvas(self, width=600, height=400)
        self.canvas.pack(fill="both", expand=True)

        # Load and place the background image on the canvas
        self.background_image = Image.open(resource_path("assets\\background.jpg"))
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.background_photo)

        self.notebook = ttk.Notebook(self.canvas)
        self.notebook.pack(fill="both", expand=True)

        self.dash_tab = tk.Frame(self.notebook)
        self.setup_tab = tk.Frame(self.notebook)
        self.documentation_tab = tk.Frame(self.notebook)

        self.notebook.add(self.dash_tab, text="Dashboard")
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.documentation_tab, text="Documentation")

        self.selected_port_var = tk.StringVar()
        self.connect_clicked = False
        self.ser = None
        self.weight_data_queue = deque(maxlen=40)
        self.csv_file = None
        self.csv_writer = None


        self.create_sidebar()
        self.create_dash_tab()
        self.create_setup_tab()
        self.check_connection()

        self.documentation_tab = ttk.Notebook(self.documentation_tab)
        self.documentation_tab.pack(fill="both", expand=True)

        # Create an instance of DocumentationTab
        self.documentation_handler = DocumentationTab(self.documentation_tab)
        self.documentation_handler.create_documentation_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_sidebar(self):
        self.sidebar = tk.Frame(self.dash_tab, bg='#33cccc')
        self.sidebar.pack(side="left", fill="y")
        self.load_ports()

    def load_ports(self):
        sidebar_title_label = tk.Label(self.sidebar, text="USB Connections", font=("verdana", 14, "bold"),
                                        bg='#33cccc')
        sidebar_title_label.pack(pady=8)

        canvas = tk.Canvas(self.sidebar, width=200, height=2, bg="black", highlightthickness=0)
        canvas.pack()
        canvas.create_line(0, 0, 200, 0, width=2)
        canvas.pack(pady=(0, 8))

        ports = serial.tools.list_ports.comports()
        self.port_options = [port.device for port in ports]

        if self.port_options:
            self.selected_port_var.set(self.port_options[0])

            select_port_label = tk.Label(self.sidebar, text="Select COM Port:")
            select_port_label.pack()

            self.port_dropdown = ttk.Combobox(self.sidebar, textvariable=self.selected_port_var,
                                                values=self.port_options)
            self.port_dropdown.pack(pady=10, padx=10)

            self.connect_button = ttk.Button(self.sidebar, text="Connect", command=self.on_connect)
            self.connect_button.pack(pady=10)

            self.disconnect_button = ttk.Button(self.sidebar, text="Disconnect", command=self.on_disconnect,
                                                    state="disabled")
            self.disconnect_button.pack(pady=10)

        else:
            select_port_label = tk.Label(self.sidebar, text="Select COM Port:")
            select_port_label.pack()
            no_ports_label = tk.Label(self.sidebar, text="No COM ports found", font=("Arial", 10, "italic"),
                                        fg="red")
            no_ports_label.pack(pady=10)
            self.connect_clicked = False
            self.refresh_button = ttk.Button(self.sidebar, text="Refresh", command=self.refresh_ports)
            self.refresh_button.pack()

    def on_connect(self):
        if not self.connect_clicked:
            self.connect_clicked = True
            self.ser = self.establish_serial_connection(self.selected_port_var.get(), 500000)
            if self.ser:
                self.display_message(f"Connected to port {self.selected_port_var.get()}")
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.check_connection()
            else:
                if hasattr(self, 'refresh_button'):
                    self.refresh_button.destroy()
                    self.show_refresh_button()
        else:
            self.display_message("Already connected! Please refresh the page to reconnect.") 
            self.show_refresh_button()       

    def check_connection(self):
        if self.ser is not None and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:{}    
            except serial.SerialException as e:
                self.display_message("Serial port error: Kindly check the connection.")
                error_message = f"Serial Port error: {str(e)}"
                self.log_error(error_message) 
                self.ser.close()
                self.show_refresh_button()
            except (AttributeError, tk.TclError):
                print("Error: Object or function is inaccessible")
        self.after(200, self.check_connection)        

    def on_disconnect(self):
        if self.connect_clicked:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
                self.connect_clicked = False
                self.display_message("Disconnected")
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled")
            self.show_refresh_button()    
        else:
            self.display_message("Not connected!")

    def refresh_ports(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self.load_ports()
        
    def show_refresh_button(self):
        self.connect_button.config(state="normal")
        self.connect_clicked = False
        self.refresh_button = ttk.Button(self.sidebar, text="Refresh", command=self.refresh_ports)
        self.refresh_button.pack(pady=10)        
        
    def create_dash_tab(self):
        self.main_area = tk.Frame(self.dash_tab)
        self.main_area.pack(side="right", fill="both", expand=True)

        self.image_label = tk.Label(self.main_area,image=self.background_photo)
        self.image_label.place(relheight=1,relwidth=1)

        # Weight label
        self.weight_label = tk.Label(self.main_area, text="Not Connected!", font=("Arial", 20))
        self.weight_label.pack(pady=20)

        # Weight plot
        self.weight_plot = plt.Figure()
        self.weight_plot_canvas = FigureCanvasTkAgg(self.weight_plot, master=self.main_area)
        self.weight_plot_canvas.get_tk_widget().pack(pady=10, anchor='center')

        self.no_data_label = tk.Label(self.main_area, font=("Arial", 20),fg='red')
        self.no_data_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Green Button (ON)
        self.green_button = tk.Button(self.main_area, text="START", bg="green", fg="white", font=("Arial", 16),
                                        command=self.start_data_collection)
        self.green_button.pack(side="right", padx=40, pady=(5, 40), anchor="s")
        self.green_button.configure(width=10)

        # Red Button (OFF)
        self.red_button = tk.Button(self.main_area, text="STOP", bg="red", fg="white", font=("Arial", 16),
                                    command=self.stop_data_collection)
        self.red_button.pack(side="right", padx=40, pady=(5, 40), anchor="s")
        self.red_button.configure(width=10)
        # BLUE Button (TARE)
        self.blue_button = tk.Button(self.main_area, text="TARE", bg="blue", fg="white", font=("Arial", 16),
                                    command=self.send_tare)
        self.blue_button.pack(side="right", padx=40, pady=(5, 40), anchor="s")
        self.blue_button.configure(width=10)

        self.error_frame = tk.Frame(self.main_area,bg='#cceeff')
        self.error_frame.pack(fill='x',padx=10, pady=10, anchor='se',expand=True)

        self.error_log_label = tk.Label(self.error_frame, text="Log Error Box:", bg='#cceeff',font=("Arial", 16), fg='black')
        self.error_log_label.pack(padx=20,pady=(0, 5), side="top",anchor='w')

        self.error_text = tk.Text(self.error_frame, height=5, width=50)
        self.error_text.pack(padx=20,pady=5, fill='both', side='left', expand=True,anchor='s')

        self.clear_log_button = tk.Button(self.error_frame, text="Clear Log", bg="grey", fg="white", font=("Arial", 12),
                                            command=self.clear_log)
        self.clear_log_button.pack(pady=5, padx=10, side='left',anchor='e')

        self.update_no_data_label_visibility()

    def clear_log(self):
        self.error_text.delete("1.0", tk.END)

    def send_tare(self):
        if self.ser:
            self.ser.write(("TARE").encode('utf-8'))
            self.log_error("TARE Button Clicked")
        else:
            pass

    def update_no_data_label_visibility(self):
        if len(self.weight_data_queue) == 0:
            self.no_data_label.config(text="No data available", fg='red')
        else:
            self.no_data_label.config(text="", fg='green')
             
        self.weight_label.after(1000, self.update_no_data_label_visibility)    

    def log_error(self, error_message):
        self.error_text.insert(tk.END, error_message + "\n")
        self.error_text.see(tk.END)     

    def start_data_collection(self):
        self.weight_data = []
        if self.ser:
            self.ser.write(("ON").encode('utf-8'))
            self.log_error("ON Button Clicked")
            global show_weight
            show_weight = True
            threading.Thread(self.update_weight_display()).start()
        else:
            pass

    def stop_data_collection(self):
        if self.ser:
            self.ser.write(("OFF").encode('utf-8'))
            self.log_error("OFF Button Clicked")
            global show_weight
            show_weight = False
        else:
            pass
        if messagebox.askyesno("Save CSV", "Do you want to save the CSV file?"):
            self.save_csv_file()

    def save_csv_file(self):
        try:
            if self.csv_file:
                self.csv_file.close()
            if not self.weight_data:
                messagebox.showwarning("No Data", "There is no data to save.")
                return    
            default_file_name = f"L-Reading-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"    
            file_path = tk.filedialog.asksaveasfilename(defaultextension=".csv",initialfile=default_file_name, filetypes=[("CSV files", "*.csv")])
            if file_path:
                with open(file_path, 'w', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(['Time', 'Weight (g)'])
                    for data in self.weight_data:
                        csv_writer.writerow(data)
                
                messagebox.showinfo("Success", "CSV file saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV file: {str(e)}")  

    def create_setup_tab(self):
        style = ttk.Style()
        style.configure("Custom.TButton", background="#58A2AA", foreground="#58A2AA",font=("Arial", 18))
        style2 = ttk.Style()
        style2.configure("Red.TButton", background="#58A2AA", foreground="#FF2255",font=("Arial", 18))
    
        self.image_label2 = tk.Label(self.setup_tab,image=self.background_photo)
        self.image_label2.place(relheight=1,relwidth=1)

        self.main_area_setup = tk.Frame(self.setup_tab, bg='#33cccc')
        self.main_area_setup.place(relx=0.5, rely=0.5, anchor="center")
        

        self.title_setup = tk.Label(self.main_area_setup, text="     - Setup the LoadCell Configuration -    ", font=("verdana", 20),bg='#33cccc')
        self.title_setup.grid(row=0, column=0, columnspan=4, padx=10, pady=20, sticky="s")

        self.text_zeroload = tk.Label(self.main_area_setup, text="Click Here When No Load is present in LoadCell :", font=("verdana", 12),bg='#33cccc')
        self.text_zeroload.grid(row=1, column=0, padx=10, pady=20, sticky="w")

        self.zero_load_button = ttk.Button(self.main_area_setup, text="Zero Load", command=lambda: self.send_command("ZERO_LOAD", self.show_tab_message))
        self.zero_load_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.text_set_load = tk.Label(self.main_area_setup, text="Enter the Value of Known Load : ", font=("verdana", 12),bg='#33cccc')
        self.text_set_load.grid(row=2, column=0, padx=10, pady=20, sticky="w")

        self.validate_float_command = self.register(self.validate_float)
        self.sample_weight_entry = tk.Entry(self.main_area_setup, textvariable=self.sample_weight, validate="key", validatecommand=(self.validate_float, '%P'), font=("Arial", 14))
        self.sample_weight_entry.grid(row=2, column=0, padx=2, pady=10, sticky="e")
        self.sample_weight_entry.config(width=12)

        self.get_load_button = ttk.Button(self.main_area_setup, text="Enter", command=lambda: self.get_load("GET_LOAD", self.show_tab_message))
        self.get_load_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.text_loaded_value = tk.Label(self.main_area_setup, text="Place the Known Load and Click Here : ", font=("verdana", 12),bg='#33cccc')
        self.text_loaded_value.grid(row=3, column=0, padx=10, pady=20, sticky="w")

        self.note_loaded_button = ttk.Button(self.main_area_setup, text="Note Loaded Value", command=lambda: self.send_command("LOADED_VALUE", self.show_tab_message))
        self.note_loaded_button.grid(row=3, column=0, padx=2, pady=10, sticky="e")  

        self.caliberate_button = ttk.Button(self.main_area_setup, text="Set Calibration Factor", command=lambda: self.send_command("SET_CALIBRATION", self.show_tab_message), style="Red.TButton")
        self.caliberate_button.grid(row=4, column=0, padx=(5, 20), pady=10,columnspan=2)  
        self.caliberate_button.config(width=20)

        self.caliberate_button = ttk.Button(self.main_area_setup, text="⭐", command=lambda: self.send_command("SET_THIS", self.show_tab_message))
        self.caliberate_button.grid(row=4, column=0, padx=(20,0), pady=10, sticky='w')  

        self.caliberate_button = ttk.Button(self.main_area_setup, text="Get Caliberation Factor", command=lambda: self.send_command("CALIBRATION_FACTOR", self.show_tab_message), style="Custom.TButton")
        self.caliberate_button.grid(row=4, column=1, padx=(20,5), pady=10,columnspan=2)  
        self.caliberate_button.config(width=20)

        self.message_frame = tk.Frame(self.setup_tab, bg='#33cccc')
        self.message_frame.place(relx=0.5, rely=0.8, anchor="center")


        self.show_tab_message = tk.Label(self.message_frame, text='start caliberating...',font=("verdana", 14, "bold"))
        self.show_tab_message.grid(row=7,column=0,columnspan=3,pady=10,padx=10,sticky='s')

    def send_command(self, command, label):
        if self.ser:
            self.ser.reset_input_buffer()  # Clear serial input buffer
            self.ser.write(command.encode('utf-8'))
            self.log_error(f"{command} Button Clicked")

            try:
                get_message = self.ser.readline().decode("utf-8").strip()
                label.config(text=f"{command} : {get_message}")

                self.log_error(get_message)

            except UnicodeDecodeError as e:
                self.log_error(f"UnicodeDecodeError: {e}")
                label.config(text="Decoding Error: Check error log for details")    
        else:
            self.log_error("Serial connection error.")
            label.config(text="Serial connection error.")

    def get_load(self, command, label):
        if self.ser:
            self.ser.reset_input_buffer()  # Clear serial input buffer
            self.show_sample_weight()
            load_value = self.sample_weight_entry.get()
            if load_value:
                try:
                    load_value_float = float(load_value)
                    command = f"{command}\n{load_value_float}\n"
                    self.ser.write(command.encode('utf-8'))
                    self.log_error("Sample Weight Enter Button Clicked")
                except ValueError as e:
                    print("Skipping non-float weight data:", load_value)
                    error_message = f"Error in get_Load data: {str(e)}"
                    self.log_error(error_message)
                    label.config(text="Invalid Entry: Enter a valid number.")
            else:
                label.config(text="Empty or Invalid Entry.")
                self.log_error("Empty or Invalid sample weight entry")    
        else:
            self.log_error("Serial connection not established.")
            label.config(text="Serial connection error.")


    def validate_float(self, new_text):
        if not new_text:
            return True
        
        try:
            float(new_text)
            return True
        except ValueError as e:
            self.log_error(f"Value Error: {e}")
            return False

    def establish_serial_connection(self, port, baudrate):
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            if port is None:
                self.display_message("No port is selected")
            else:
                self.display_message(f"Serial connection established successfully with port {port}.")
            return ser
        except serial.SerialException as e:
            error_message = f"Serial Exception: {str(e)}"
            self.log_error(error_message) 
            if isinstance(e, PermissionError):
                self.display_message("Permission denied. Make sure the port is not already in use and try again.")
            else:
                self.display_message(f"Failed to establish serial connection.")   
            return None

    def update_weight_display(self):
        if show_weight:    
            if self.ser is not None and self.ser.is_open:
                try:
                    if self.ser.in_waiting > 0:
                        weight_data = self.ser.readline().decode("utf-8", errors="replace").strip()
                        try:
                            weight_value = float(weight_data)
                            self.weight_label.config(text=f"Current Weight: {weight_value} grams")
                            self.weight_data_queue.append(weight_value)
                            try:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
                                if show_weight:
                                    self.weight_data.append((timestamp, weight_value))
                            except ValueError as e:
                                error_message = f"Error updating weight data to CSV: {str(e)}"
                                self.log_error(error_message)

                            self.update_weight_plot()

                        except ValueError as e:
                            error_message = f"Serial Exception: {str(e)}"
                            self.log_error(error_message) 
                            self.log_error(f"Skipping non-float weight data: {weight_data}")
                except serial.SerialException as e:
                    self.display_message("Serial port error: Kindly check the connection.")
                    error_message = f"Serial Port error: {str(e)}"
                    self.log_error(error_message) 
                    self.ser.close()
                    self.show_refresh_button()
                except (AttributeError, tk.TclError):
                    print("Error: Object or function is inaccessible")

                finally:
                    if not self.is_closed:
                        self.after(50, self.update_weight_display)

    def update_weight_plot(self):
        try:
            if self.weight_data_queue:
                self.weight_plot.clf()
                axis = self.weight_plot.add_subplot(111)
                axis.plot(range(len(self.weight_data_queue)), self.weight_data_queue, 'b.-')
                axis.set_xlabel('Time ->')
                axis.set_ylabel('Weight (g)')
                axis.set_title('Real-time Weight Data')
                axis.grid(True)
                self.weight_plot_canvas.draw()
        except Exception as e:
            error_message = f"Serial Exception: {str(e)}"
            self.log_error(error_message) 
            self.loadtk("Error updating weight plot:", e)

    def display_message(self, message):
        self.weight_label.config(text=message)
        
    def show_sample_weight(self):
        try:
            sample_weight_value = float(self.sample_weight.get())
            messagebox.showinfo("Sample Weight", f"Sample Weight: {sample_weight_value} grams")
        except ValueError as e:
            messagebox.showerror("Error", "Invalid sample weight value")
            error_message = f"Value Error: {str(e)}"
            self.log_error(error_message) 

    def on_closing(self):
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
            self.is_closed = True
            self.destroy()
        except Exception as e:
            self.log_error("Error on closing:", e)
              
    def on_tab_changed(self, event):
        current_tab = event.widget.tab(event.widget.select(), "text")
        if current_tab == "Setup":
            messagebox.showinfo("Important Message","Please read the Documentation before proceeding to set the Caliberation Factor (CLF ) to your Arduino/Node MCU Board for LoadCell Configuration.")  
             

if __name__ == "__main__":
    app = LoadCellApp()
    app.mainloop()
