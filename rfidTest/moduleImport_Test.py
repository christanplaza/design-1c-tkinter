try:
    import mfrc522
    print("module imported successfully")
except ImportError:
    print("module not found")