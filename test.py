from dotenv import load_dotenv
import os
import mysql.connector
load_dotenv()
admin_host = os.getenv("admin_host")
print(admin_host)
