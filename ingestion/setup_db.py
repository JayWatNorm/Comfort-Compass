"""One-off, idempotent setup script: creates the database (if missing),
creates the raw tables from db/init.sql, and runs dbt to build the mart.
"""
import os
import subprocess
import sys

import psycopg2
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
init_sql_path = os.path.join(script_dir, "..", "ingestion","db", "init.sql")
dbt_project_path = os.path.join(script_dir, "..", "dbt_project")

load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Step 1: connect to the default 'postgres' database to create ours if missing
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    dbname="postgres",
    user=db_user,
    password=db_password
)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
exists = cursor.fetchone()

if not exists:
    cursor.execute(f"CREATE DATABASE {db_name}")
    print(f"Created database {db_name}")
else:
    print(f"Database {db_name} already exists")

cursor.close()
conn.close()

# Step 2: connect to our actual database and run the init.sql schema
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_password
)
cursor = conn.cursor()

with open(init_sql_path, encoding="utf-8") as f:
    init_sql = f.read()

cursor.execute(init_sql)
conn.commit()

cursor.close()
conn.close()

print("Tables created (or already existed).")
try:
    subprocess.run(["dbt", "run"], cwd=dbt_project_path, check=True)
except subprocess.CalledProcessError:
    print("DBT run Failed")
    sys.exit(1)
else:
    print("DBT run completed successfully")
