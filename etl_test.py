import mysql.connector
import json
import os

# Load config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "db_config.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

db_conf = config["databases"]["sfmysql01"]

conn = mysql.connector.connect(
    host=db_conf["host"],
    user=db_conf["user"],
    password=db_conf["password"]
)

cursor = conn.cursor()

# 1️⃣ List all databases user can see
cursor.execute("SHOW DATABASES;")
databases = cursor.fetchall()
print("Databases visible to etl_user:")
for db in databases:
    print(" -", db[0])

# 2️⃣ List all tables in sfvispool
print("\nTables in sfvispool:")
cursor.execute("SHOW TABLES FROM sfvispool;")
tables = cursor.fetchall()
for t in tables:
    print(" -", t[0])

# 3️⃣ List all tables in sfOrinMonitoring
print("\nTables in sfOrinMonitoring:")
cursor.execute("SHOW TABLES FROM sfOrinMonitoring;")
tables = cursor.fetchall()
for t in tables:
    print(" -", t[0])

cursor.close()
conn.close()
