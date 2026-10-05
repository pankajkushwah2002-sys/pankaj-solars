import sqlite3
import pandas as pd

DB_NAME = "pankaj_solars.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_generation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            generation_kwh REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plant_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            plant_name TEXT DEFAULT 'Pankaj Solars',
            location TEXT DEFAULT 'Noida, Uttar Pradesh',
            capacity_kwp REAL DEFAULT 100.0,
            tariff_rate REAL DEFAULT 7.5
        )
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO plant_settings (id, plant_name, location, capacity_kwp, tariff_rate)
        VALUES (1, 'Pankaj Solars', 'Noida, Uttar Pradesh', 100.0, 7.5)
    ''')
    conn.commit()
    conn.close()

def save_daily_record(date_str, generation_kwh):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO daily_generation (date, generation_kwh)
        VALUES (?, ?)
        ON CONFLICT(date) DO UPDATE SET generation_kwh=excluded.generation_kwh
    ''', (date_str, generation_kwh))
    conn.commit()
    conn.close()

def bulk_insert_records(df):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO daily_generation (date, generation_kwh)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET generation_kwh=excluded.generation_kwh
        ''', (str(row['Date']), float(row['Generation_kWh'])))
    conn.commit()
    conn.close()

def get_all_generation_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT date as Date, generation_kwh as Generation_kWh FROM daily_generation ORDER BY date ASC", conn)
    conn.close()
    return df

def update_plant_settings(capacity, tariff):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE plant_settings SET capacity_kwp=?, tariff_rate=? WHERE id=1", (capacity, tariff))
    conn.commit()
    conn.close()

def get_plant_settings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT capacity_kwp, tariff_rate FROM plant_settings WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row if row else (100.0, 7.5)
