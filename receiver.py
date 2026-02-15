#!/usr/bin/env python3
"""
receiver_db.py
--------------
Main receiver script for Raspberry Pi. Decodes BLE packets, maps MAC addresses
to locations, and saves timestamped data to a SQLite database.
"""

import asyncio
import struct
import sqlite3
import time
from datetime import datetime
from dataclasses import dataclass
from bleak import BleakScanner

# --- CONFIGURATION ---
DB_FILENAME = "/mnt/data/weather_data.db"  # changed to use SD card on BBBrevC
TARGET_COMPANY_ID = 0x0822
TARGET_PRODUCT_ID = 0xABCD
STRUCT_FORMAT = "<HhHhH"

# Minimum seconds between database writes per sensor (to prevent spamming)
LOG_INTERVAL = 60 

# The "Phonebook": Map MAC to Location
KNOWN_SENSORS = {
    "E1:BD:F2:F7:60:45": "store_room",
    "C3:1A:08:56:82:67": "garden",
    # Add more MACs here as you find them
}

@dataclass
class SensorReading:
    mac: str
    location: str
    temp_bmp: float
    pressure: int
    temp_sht: float
    humidity: int
    rssi: int

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            mac_address TEXT,
            location TEXT,
            temp_bmp REAL,
            pressure INTEGER,
            temp_sht REAL,
            humidity INTEGER,
            rssi INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_to_db(r: SensorReading):
    try:
        conn = sqlite3.connect(DB_FILENAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO readings 
            (mac_address, location, temp_bmp, pressure, temp_sht, humidity, rssi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (r.mac, r.location, r.temp_bmp, r.pressure, r.temp_sht, r.humidity, r.rssi))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

# --- GLOBAL STATE ---
last_logged = {}

def decode_payload(payload: bytes):
    expected_size = struct.calcsize(STRUCT_FORMAT)
    # Strip the extra 0x0A length byte if present
    if len(payload) == expected_size + 1:
        payload = payload[1:]
    
    if len(payload) != expected_size:
        return None
    try:
        return struct.unpack(STRUCT_FORMAT, payload)
    except struct.error:
        return None

def detection_callback(device, advertisement_data):
    if TARGET_COMPANY_ID not in advertisement_data.manufacturer_data:
        return

    payload = advertisement_data.manufacturer_data[TARGET_COMPANY_ID]
    decoded = decode_payload(payload)
    if not decoded:
        return

    key, t_bmp_raw, p_bmp, t_sht_raw, h_sht = decoded
    if key != TARGET_PRODUCT_ID:
        return

    # Throttling
    mac = device.address
    now = time.time()
    if mac in last_logged and (now - last_logged[mac]) < LOG_INTERVAL:
        return

    # Data Processing
    reading = SensorReading(
        mac=mac,
        location=KNOWN_SENSORS.get(mac, f"Unknown ({mac})"),
        temp_bmp=t_bmp_raw / 10.0,
        pressure=p_bmp,
        temp_sht=t_sht_raw / 10.0,
        humidity=h_sht,
        rssi=advertisement_data.rssi
    )

    last_logged[mac] = now
    log_to_db(reading)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved: {reading.location} | {reading.temp_bmp}°C")

async def main():
    init_db()
    print(f"Starting Receiver. Logging to {DB_FILENAME} every {LOG_INTERVAL}s")
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    try:
        await asyncio.get_running_loop().create_future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())
