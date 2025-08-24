
import os, csv, logging, asyncio
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "log.csv")
APP_LOG = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(APP_LOG, encoding="utf-8"), logging.StreamHandler()],
)
app_logger = logging.getLogger("face-backend")

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp","camera","name","score"])

_events_queue: "asyncio.Queue[str]" = asyncio.Queue()

def log_match(camera: str, name: str, score: float):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([ts, camera, name, f"{score:.4f}"])
    app_logger.info("DETECTION | camera=%s name=%s score=%.2f", camera, name, score*100.0)
    try:
        _events_queue.put_nowait(f'event: detection\ndata: {{"ts":"{ts}","camera":"{camera}","name":"{name}","score":{score:.4f}}}\n\n')
    except Exception:
        pass

async def sse_stream():
    yield "event: hello\ndata: {}\n\n"
    while True:
        msg = await _events_queue.get()
        yield msg
