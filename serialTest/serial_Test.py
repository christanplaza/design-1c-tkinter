import serial
import time

serial_port = '/dev/ttyS0'  # or '/dev/ttyAMA0' for older Raspberry Pi models
baud_rate = 9600  # match this with the baud rate of your USB-TTL adapter

try:
  # Initialize serial connection
  ser = serial.Serial(serial_port, baud_rate)

  print("Waiting for incoming characters...")

  while True:
    char_array = ["2|Neil Patrick Sedeno|11:30|+639927126089/"]    
    for char in char_array:
      ser.write(char.encode())
      time.sleep(0.005)
      print("Sent: " + char)
    print("Characters sent successfully")
    time.sleep(100)

except KeyboardInterrupt:
  # Handle keyboard interrupt (Ctrl+C)
  print("Keyboard interrupt detected. Exiting...")

finally:
  # Close the serial connection
  ser.close()