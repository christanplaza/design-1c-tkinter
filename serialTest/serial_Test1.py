import serial

serial_port = '/dev/ttyS0'  # or '/dev/ttyAMA0' for older Raspberry Pi models
baud_rate = 9600  # match this with the baud rate of your USB-TTL adapter

try:
    # Initialize serial connection
    ser = serial.Serial(serial_port, baud_rate)
    
    print("Waiting for incoming characters...")
    
    while True:
        if ser.in_waiting > 0:
            # Read a character from the serial port
            incoming_char = ser.read().decode('utf-8')
            
            print("Received:", incoming_char)
            ser.write(incoming_char.encode())
            
except KeyboardInterrupt:
    # Handle keyboard interrupt (Ctrl+C)
    print("Keyboard interrupt detected. Exiting...")

finally:
    # Close the serial connection
    ser.close()