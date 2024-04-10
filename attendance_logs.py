import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import redis
from dotenv import load_dotenv
import os
import mysql.connector
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

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

current_class_session = None

class AttendanceApp:
    def __init__(self, root, class_session):
        self.root = root
        self.root.title("Live Attendance Tracker")

        self.class_session = class_session

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

        self.conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='root',
            password='',
            database='design-1c-class_management'
        )

        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS attendance_table (`id` INT NOT NULL AUTO_INCREMENT , `student_id` VARCHAR(16) NOT NULL , `student_name` VARCHAR(255) NOT NULL , `first_detected` DATETIME NOT NULL , `last_detected` DATETIME NOT NULL , PRIMARY KEY (`id`))''')
        self.conn.commit()

        # Setup the automatic refresh
        self.setup_automatic_refresh()

    def refresh_attendance(self):
        print("refreshing")

        # Clear existing items in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Send a GET request to the PHP script with the class_id
        url = 'http://localhost/design-1c-class_management/api/attendance_handler.php'
        params = {'class_id': self.class_session.class_id}

        response = requests.get(url, params=params)

        print("Request URL:", response.url)

        if response.status_code == 200:
            latest_log_entries = response.json()

            # Display the latest log entries in the treeview
            for log_entry in latest_log_entries:
                self.tree.insert('', 'end', values=(log_entry['student_number'], log_entry['first_name'], log_entry['last_name'], log_entry['first_seen'], log_entry['last_seen']))
        else:
            print(response)
            print("Failed to retrieve attendance logs from the server")

    def finalize_attendance(self):
        print("Finalizing attendance")

        # Send a GET request to the PHP script with the class_id
        response = requests.get('http://localhost/design-1c-class_management/api/finalize_attendance.php', params={'class_id': self.class_session.class_id})
        
        # response = requests.get('http://localhost/design-1c-class_management/api/finalize_attendance.php', params={'class_id': 3})

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

    
    def setup_automatic_refresh(self):
        # Refresh every 60 seconds (60000 milliseconds)
        self.refresh_attendance()  # Perform initial refresh
        self.root.after(60000, self.setup_automatic_refresh)

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

        # Connect to the MySQL database
        self.conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='root',
            password='',
            database='design-1c-class_management'
        )
        self.cursor = self.conn.cursor()
        
        # Fetch ongoing classes
        self.ongoing_classes = self.get_ongoing_classes()
        
        # Display ongoing classes
        self.display_ongoing_classes()

    def get_ongoing_classes(self):
        current_time = datetime.now()
        current_day_of_week = current_time.strftime('%A').lower()  # Convert to lowercase to match the database format
        current_time_str = current_time.strftime('%H:%M:%S')
        
        # Fetch ongoing classes from MySQL database based on current day and time
        query = ("SELECT c.title, c.course, s.location, s.start_time, s.end_time, t.name AS teacher_name, c.id "
                 "FROM classes c "
                 "JOIN teachers t ON c.teacher_id = t.id "
                 "JOIN schedules s ON c.id = s.class_id "
                 "WHERE s.day_of_week = %s "
                 "AND s.start_time <= %s "
                 "AND s.end_time >= %s")
        self.cursor.execute(query, (current_day_of_week, current_time_str, current_time_str))
        ongoing_classes = self.cursor.fetchall()
        return ongoing_classes
    
    def display_ongoing_classes(self):
        # Create a frame to contain the card grid layout
        card_frame = ttk.Frame(self.root)
        card_frame.pack(fill=tk.BOTH, expand=True)

        # Sort the ongoing classes alphabetically by title
        sorted_classes = sorted(self.ongoing_classes, key=lambda x: x[0])

        # Iterate over ongoing classes and create a card for each
        for class_info in sorted_classes:
            # Create a frame for the card
            card = ttk.Frame(card_frame, borderwidth=2, relief="solid", padding=(10, 5))
            card.grid(row=len(card_frame.grid_slaves()), column=0, padx=10, pady=10, sticky="nsew")
            
            # Display information about the ongoing class
            title_label = tk.Label(card, text=f"Title: {class_info[0]}", font=("Helvetica", 14, "bold"))
            title_label.grid(row=0, column=0, sticky="w")

            teacher_label = tk.Label(card, text=f"Teacher: {class_info[5]}", font=("Helvetica", 14, "bold"))
            teacher_label.grid(row=1, column=0, sticky="w")

            course_label = tk.Label(card, text=f"Course: {class_info[1]}")
            course_label.grid(row=2, column=0, sticky="w")

            location_label = tk.Label(card, text=f"Location: {class_info[2]}")
            location_label.grid(row=3, column=0, sticky="w")

            time_label = tk.Label(card, text=f"Time: {class_info[3]} - {class_info[4]}")
            time_label.grid(row=4, column=0, sticky="w")
            
            # Create a button to start the class
            start_class_button = tk.Button(card, text="Start Class", command=lambda: self.start_class(class_info[0], class_info[6]))
            start_class_button.grid(row=5, column=0, pady=(10, 0), sticky="w")
        

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
        attendance_app = AttendanceApp(tk.Toplevel(self.root), current_class_session)
        
        # Start the AttendanceApp
        attendance_app.setup_automatic_refresh()  # Start automatic refresh
        attendance_app.root.mainloop()  # Start the main event loop


if __name__ == "__main__":
    # root = tk.Tk()
    # app = AttendanceApp(root)
    # root.mainloop()
    # Create and display the initial window
    root = tk.Tk()
    initial_window = InitialWindow(root)
    root.mainloop()
