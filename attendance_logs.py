import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import redis
from dotenv import load_dotenv
import os
from datetime import date
import requests
import csv
import serial
import time


# Load environment variables from .env file
load_dotenv()

# Read Redis connection details from environment variables
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_password = os.getenv("REDIS_PASSWORD")
admin_host = os.getenv("admin_host")

admin_host = os.getenv("admin_host")

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

current_class_session = None

class AttendanceApp:
    def __init__(self, root, class_session, initial_window):
        self.root = root
        self.class_session = class_session
        self.initial_window = initial_window
        self.root.title("Live Attendance Tracker")

        self.tree = ttk.Treeview(self.root, columns=('Student Number', 'First Name', 'Last Name', 'First Seen', 'Last Seen'))
        self.tree.heading('#0', text='ID')  # Provide a heading for the first column
        self.tree.heading('#1', text='Student Number')
        self.tree.heading('#2', text='First Name')
        self.tree.heading('#3', text='Last Name')
        self.tree.heading('#4', text='First Seen')
        self.tree.heading('#5', text='Last Seen')
        self.tree.pack(padx=10, pady=10)

        self.refresh_button = tk.Button(self.root, text='Finalize Attendance', command=self.finalize_attendance)
        self.refresh_button.pack(pady=10)

        ## Close AttendanceApp and open InitialWindow Again
        self.root.protocol("WM_DELETE_WINDOW", self.on_close) 

        # Setup the automatic refresh
        self.setup_automatic_refresh()

    def refresh_attendance(self):
        print("refreshing")

        # Clear existing items in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Send a GET request to the PHP script with the class_id
        url = f'http://{admin_host}/design-1c-cms/api/attendance_handler.php'
        params = {'class_id': self.class_session.class_id}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            latest_log_entries = response.json()

            # Display the latest log entries in the treeview
            for log_entry in latest_log_entries:
                self.tree.insert('', 'end', values=(log_entry['student_number'], log_entry['first_name'], log_entry['last_name'], log_entry['first_seen'], log_entry['last_seen']))
        else:
            print("Failed to retrieve attendance logs from the server")

    def finalize_attendance(self):
        print("Finalizing attendance")
        self.refresh_attendance()

        # Send a GET request to the PHP script with the class_id
        url = f'http://{admin_host}/design-1c-cms/api/finalize_attendance.php'
        params = {'class_id': self.class_session.class_id}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            attendance_data = response.json()

            # Clear existing items in the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Display the attendance data in the treeview
            for student in attendance_data:
                self.tree.insert('', 'end', values=(student['student_number'], student['first_name'], student['last_name'], student['status']))

            # Convert the attendance data to CSV string
            csv_data = self.convert_to_state2_csv(attendance_data)

            # Send the CSV data to PIC via UART
            self.send_to_pic_state2(csv_data)
        else:
            print("Failed to retrieve attendance data from the server")

    def convert_to_state2_csv(self, data):
        csv_data = []
        for student in data:
            full_name = f"{student['first_name']} {student['last_name']}"
            first_seen = student['first_seen']
            phone_number = student['phone_number']
            csv_data.append(f"{full_name}|{first_seen}|{phone_number}")  # Name|timestamp|phone_number

        # return ", ".join(csv_data)
        return csv_data

    def convert_to_csv(self, data):
        csv_data = []
        for student in data:
            full_name = f"{student['first_name']} {student['last_name']}"
            status = student['status'][0]  # Get the first letter of the status (P/L/A)
            csv_data.append(f"{full_name} {status}") #Name P/L/A

        return ", ".join(csv_data)

    def send_to_pic_state2(self, csv_data):
        # Configure the serial connection (replace 'COM3' with the appropriate port)
        ser = serial.Serial('COM4', 9600)  # Adjust the baud rate if needed
        # print(csv_data.encode()) # State 1
        for data in csv_data:
            ser.write(data.encode())
            print('Sent')
            time.sleep(5)
            
        # # Send the CSV data to PIC

        # # Close the serial connection
        # ser.close()

    
    def on_close(self):
        self.root.destroy()  # Destroy the AttendanceApp window
        self.initial_window.show_initial_window()  # Show the InitialWindow again

    
    def setup_automatic_refresh(self):
        # Refresh every 60 seconds (60000 milliseconds)
        self.refresh_attendance()  # Perform initial refresh
        self.root.after(15000, self.setup_automatic_refresh)  # Change time to

class ClassSession:
    def __init__(self, class_id):
        self.class_id = class_id
        self.start_time = datetime.now()

class InitialWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Initial Window")
        
        # # Get the screen width and height
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set the size of the window to fill the entire screen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        # Create a refresh button
        refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_ongoing_classes)
        refresh_button.pack(pady=10)
        
        # Fetch ongoing classes
        self.ongoing_classes = self.get_ongoing_classes()
        
        # Display ongoing classes
        self.display_ongoing_classes()

    def get_ongoing_classes(self):
        # Send a GET request to the PHP API endpoint
        response = requests.get(f'http://{admin_host}/design-1c-class_management/api/get_current_class.php')

        if response.status_code == 200:
            # Parse the JSON response
            ongoing_classes_data = response.json()

            # Format the ongoing classes data
            ongoing_classes = []
            for class_data in ongoing_classes_data:
                title = class_data['title']
                course = class_data['course']
                location = class_data['location']
                start_time = datetime.strptime(class_data['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(class_data['end_time'], '%H:%M:%S').time()
                teacher_name = class_data['teacher_name']
                class_id = class_data['id']

                # Calculate the duration as timedelta
                duration = datetime.combine(datetime.min, end_time) - datetime.combine(datetime.min, start_time)

                # Create a tuple with the formatted data
                class_tuple = (title, course, location, start_time, end_time, teacher_name, class_id)
                ongoing_classes.append(class_tuple)

            return ongoing_classes
        else:
            # Handle the error case
            print(f"Error: {response.status_code}")
            return []
    
    def display_ongoing_classes(self):
        # Create a frame to contain the card grid layout
        self.card_frame = ttk.Frame(self.root)
        self.card_frame.pack(fill=tk.BOTH, expand=True)

        # Create a canvas to hold the card frame
        canvas = tk.Canvas(self.card_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a scrollbar for the canvas
        scrollbar = ttk.Scrollbar(self.card_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas to work with the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create a frame inside the canvas to hold the cards
        card_container = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=card_container, anchor="nw")

        # Sort the ongoing classes alphabetically by title
        sorted_classes = sorted(self.ongoing_classes, key=lambda x: x[0])

        # Iterate over ongoing classes and create a card for each
        for i, class_info in enumerate(sorted_classes):
            # Create a frame for the card
            card = ttk.Frame(card_container, borderwidth=2, relief="solid", padding=(10, 5))
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

            # Display information about the ongoing class
            title_label = tk.Label(card, text=f"Title: {class_info[0]}", font=("Helvetica", 14, "bold"))
            title_label.grid(row=0, column=0, sticky="w")

            teacher_label = tk.Label(card, text=f"Teacher: {class_info[5]}", font=("Helvetica", 14, "bold"))
            teacher_label.grid(row=1, column=0, sticky="w")

            course_label = tk.Label(card, text=f"Course: {class_info[1]}")
            course_label.grid(row=2, column=0, sticky="w")

            location_label = tk.Label(card, text=f"Location: {class_info[2]}")
            location_label.grid(row=3, column=0, sticky="w")

            time_label = tk.Label(card, text=f"Time: {class_info[3].strftime('%I:%M:%S %p')} - {class_info[4].strftime('%I:%M:%S %p')}")
            time_label.grid(row=4, column=0, sticky="w")

            # Create a button to start the class
            start_class_button = tk.Button(card, text="Start Class", command=lambda title=class_info[0], class_id=class_info[6]: self.start_class(title, class_id))
            start_class_button.grid(row=5, column=0, pady=(10, 0), sticky="w")

        # Configure the card container to expand to fit the canvas
        card_container.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        

    def start_class(self, class_title, class_id):
        global current_class_session
        current_class_session = ClassSession(class_id)
        # Implement the logic to start the class (e.g., open a new window, perform necessary actions, etc.)
        print(f"Starting class: {class_title} with class id: {class_id}")

        self.open_attendance_app()

    def open_attendance_app(self):
        # Hide the current window
        self.root.withdraw()
        
        # Create a new instance of the AttendanceApp class
        attendance_app = AttendanceApp(tk.Toplevel(self.root), current_class_session, self)
        
        # Start the AttendanceApp
        attendance_app.setup_automatic_refresh()  # Start automatic refresh
        attendance_app.root.mainloop()  # Start the main event loop

    def refresh_ongoing_classes(self):
        # Clear the existing ongoing classes
        self.ongoing_classes = []
        
        # Fetch the updated ongoing classes from the API
        self.ongoing_classes = self.get_ongoing_classes()
        
        # Destroy the existing card frame
        if hasattr(self, 'card_frame'):
            self.card_frame.destroy()
        
        # Redisplay the updated ongoing classes
        self.display_ongoing_classes()

    def show_initial_window(self):
        self.root.deiconify()
        self.refresh_ongoing_classes()


if __name__ == "__main__":
    # root = tk.Tk()
    # app = AttendanceApp(root)
    # root.mainloop()
    # Create and display the initial window
    root = tk.Tk()
    initial_window = InitialWindow(root)
    root.mainloop()