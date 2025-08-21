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
    os.makedirs(LOG_DIR, exist_ok=True)
    # Pastikan header CSV sesuai format baru: timestamp,kamera,nama,skor
    if not os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "kamera", "nama", "skor"])
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

def log_detection(kamera: str, nama: str, skor: float):
    """
    Tulis log hanya untuk orang yang cocok, format:
    2025-08-19 00:16:43 [INFO] DETECTION | kamera=IP Kamera Dalam nama=Laufie skor=69.00
    (skor ditulis dalam persen, 2 desimal)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # tulis CSV (timestamp,kamera,nama,skor_percent)
    try:
        with _csv_lock:
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, kamera, nama, f"{float(skor)*100.0:.2f}"])
    except Exception:
        logging.exception("Failed to write detection to CSV.")

    logging.info(f"DETECTION | kamera={kamera} nama={nama} skor={float(skor)*100.0:.2f}")
