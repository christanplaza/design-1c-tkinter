try:
    import serial
except ImportError:
    print("The 'serial' module could not be imported. Please install it using 'pip install pyserial'")
    exit(1)
else:
    print("The 'serial' module was imported successfully.")