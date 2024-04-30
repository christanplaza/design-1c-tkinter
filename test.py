from dotenv import load_dotenv
import os
import mysql.connector
load_dotenv()
admin_host = os.getenv("admin_host")
print(admin_host)

# FORMAT OF STRING FROM TKINTER
'Christan Plaza A, Dingdong Dantes A, John Vincent  De los Santos L, Christan Shane Plaza A'