#!/usr/bin/env python3
import json
import logging
import mysql.connector
from mysql.connector import Error

# --- CONFIG ---
CONFIG_FILE = "db_config.json"
SOURCE_DB_KEY = "sfmysql01"
DEST_DB_KEY = "sfmysql04"
SOURCE_SCHEMA = "sfOrinMonitoring"
DEST_SCHEMA = "sfOrinAggregate"
TABLES = [f"sfvis{i:02}" for i in range(1,16)]
HISTORY_LIMIT = 30

# Columns that are safe to copy (ignore problematic ones)
SAFE_COLUMNS = [
    'uptime','CPU1','CPU2','CPU3','CPU4','CPU5','CPU6','RAM','SWAP','EMC',
    'GPU','APE','NVDEC','NVJPG','NVJPG1','OFA','SE','VIC','disk_available_gb',
    'hostname','ip_address','model','jetpack','l4t','nv_power_mode','serial_number',
    'p_number','module','distribution','cuda','cudnn','tensorrt','vpi','vulkan','opencv'
]

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# --- HELPER FUNCTIONS ---
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)["databases"]

def get_connection(cfg, database=None):
    params = {k:v for k,v in cfg.items() if k in ['host','user','password']}
    if database:
        params['database'] = database
    return mysql.connector.connect(**params)

def ensure_database(conn, db_name):
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    conn.commit()

def get_source_columns(cursor, schema, table):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {schema}.{table}")
        return [row[0] for row in cursor.fetchall()]
    except Error as e:
        logging.warning(f"Skipping {schema}.{table}: {e}")
        return []

def get_safe_source_columns(src_cols):
    return [c for c in src_cols if c in SAFE_COLUMNS]

def fetch_last_row(cursor, schema, table, columns):
    if not columns:
        return None
    cols_str = ', '.join(columns)
    cursor.execute(f"SELECT {cols_str} FROM {schema}.{table} ORDER BY id DESC LIMIT 1")
    return cursor.fetchone()

def ensure_table(conn, table_name, columns):
    if not columns:
        return
    cursor = conn.cursor()
    cols_def = ', '.join([f"{c} TEXT" for c in columns])
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        {cols_def}
    ) ENGINE=InnoDB
    """
    cursor.execute(sql)
    conn.commit()

def insert_row(cursor, table_name, columns, row):
    if not row:
        return
    cols_str = ', '.join(columns)
    # Escape each value properly as a string literal
    vals_escaped = []
    for v in row:
        if v is None:
            vals_escaped.append("NULL")
        else:
            vals_escaped.append(f"'{str(v).replace('\'','\\\'')}'")
    vals_str = ', '.join(vals_escaped)
    sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})"
    cursor.execute(sql)


def trim_history(cursor, table_name, limit=HISTORY_LIMIT):
    cursor.execute(f"""
        DELETE FROM {table_name}
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT id FROM {table_name} ORDER BY id DESC LIMIT {limit}
            ) t
        )
    """)

# --- MAIN ETL ---
def main():
    dbs = load_config()
    src_conn = get_connection(dbs[SOURCE_DB_KEY], SOURCE_SCHEMA)
    dest_conn = get_connection(dbs[DEST_DB_KEY])
    ensure_database(dest_conn, DEST_SCHEMA)
    dest_conn.database = DEST_SCHEMA

    src_cursor = src_conn.cursor()
    dest_cursor = dest_conn.cursor()

for table in tables:
    logging.info(f"=== Processing {table} ===")
    try:
        # Load rows from source
        rows = fetch_rows(src_cursor, table, SAFE_COLUMNS)
        if not rows:
            logging.info(f"No rows to copy for {table}")
            continue

        # Insert rows into destination
        for row in rows:
            try:
                insert_row(dest_cursor, table, SAFE_COLUMNS, row)
            except Exception as e:
                logging.warning(f"ETL error for row in {table}: {e}")
        
        logging.info(f"Inserted last row from {table}")

    except mysql.connector.Error as e:
        logging.warning(f"Skipping {table}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for {table}: {e}")


    src_cursor.close()
    dest_cursor.close()
    src_conn.close()
    dest_conn.close()
    logging.info("ETL run completed")

if __name__ == "__main__":
    main()
