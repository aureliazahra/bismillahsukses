# logger.py
import os
import csv
import logging
from datetime import datetime
from threading import Lock

LOG_DIR = "logs"
CSV_FILE = os.path.join(LOG_DIR, "log.csv")
APP_LOG = os.path.join(LOG_DIR, "app.log")

_csv_lock = Lock()

def init_logger(level=logging.INFO):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "kamera", "nama", "hasil", "skor"])
        except Exception as e:
            print(f"Gagal membuat {CSV_FILE}: {e}")

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(APP_LOG, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def log_detection(kamera, nama, hasil, skor):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, kamera, nama, hasil, f"{skor:.2f}"]
    try:
        with _csv_lock:
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
    except Exception:
        logging.exception("Failed to write detection to CSV.")

    logging.info(f"DETECTION | kamera={kamera} nama={nama} hasil={hasil} skor={skor:.2f}")
