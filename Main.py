import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import os

# =========================
# ===== CONFIG ===========
# =========================
NAMES_TO_FIND = 300000
LENGTHS = [3, 4, 5]
WORKER_THREADS = 8
CHECK_SLEEP = 0.05

VALID_FILE = "valid.txt"
LOG_FILE = "scan_log.txt"

BIRTHDAY = "1999-04-20"
ROBLOX_VALIDATE_URL = "https://auth.roblox.com/v1/usernames/validate"

# Using your webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1438746345669398638/D04CCzQ689QlnZzrx2pUHeEoniyORaGmSqVkwlVp_dvQfKY7o-xm4JbYG1lKprxFyHtf"
WEBHOOK_NAME = None  # optional: leave None to use default webhook name

# =========================
# ===== GLOBALS ==========
# =========================
found_usernames = []
found_lock = threading.Lock()
checked_counter = 0
checked_lock = threading.Lock()
stop_event = threading.Event()
last_username = ""
last_status = ""

# =========================
# ===== LOGGING ==========
# =========================
def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a+", encoding="utf-8") as lf:
        lf.write(f"[{ts}] {msg}\n")
    print(msg)

# =========================
# ===== USERNAMES ========
# =========================
def make_username(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def check_username(username):
    params = {"request.username": username, "request.birthday": BIRTHDAY}
    try:
        r = requests.get(ROBLOX_VALIDATE_URL, params=params, timeout=5)
        r.raise_for_status()
        return r.json().get("code")
    except Exception as e:
        log(f"Network error for {username}: {e}")
        return None

# =========================
# ===== WEBHOOK ==========
# =========================
def send_message(message):
    """Send a plain Discord message through webhook."""
    payload = {"content": message}
    if WEBHOOK_NAME:
        payload["username"] = WEBHOOK_NAME
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        log("Failed to send webhook message: " + str(e))

# =========================
# ===== WORKER THREAD =====
# =========================
def worker_thread(thread_id, target_count):
    global checked_counter, last_username, last_status
    while not stop_event.is_set():
        with checked_lock:
            if len(found_usernames) >= target_count:
                break
            checked_counter += 1

        length = random.choice(LENGTHS)
        username = make_username(length)
        code = check_username(username)

        if code == 0:
            with found_lock:
                if username not in found_usernames:
                    found_usernames.append(username)
                    with open(VALID_FILE, "a+", encoding="utf-8") as vf:
                        vf.write(username + "\n")
            last_status = "available"
            last_username = username
            log(f"[FOUND] {username}")
            send_message(f"✅ Found Username: `{username}`")  # plain message
        elif code is None:
            last_status = "network-error"
            last_username = username
            log(f"[NET ERR] {username}")
        else:
            last_status = "taken"
            last_username = username
            log(f"[TAKEN] {username}")

        time.sleep(CHECK_SLEEP)

# =========================
# ===== START SCAN =======
# =========================
def start_scan():
    if stop_event.is_set():
        stop_event.clear()
    for f in [VALID_FILE, LOG_FILE]:
        if os.path.exists(f):
            os.remove(f)

    log("Scan starting...")
    send_message("🔍 Username Scanner Started!")  # opening message

    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        futures = [executor.submit(worker_thread, i, NAMES_TO_FIND) for i in range(WORKER_THREADS)]
        try:
            while not stop_event.is_set():
                with found_lock:
                    if len(found_usernames) >= NAMES_TO_FIND:
                        break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stop_event.set()
        stop_event.set()
        time.sleep(0.5)

    log("Scan finished.")
    send_message(f"✅ Scan Finished! Found {len(found_usernames)} usernames.")

# =========================
# ===== ENTRY POINT =======
# =========================
if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("ERROR: Please set WEBHOOK_URL before running.")
    else:
        start_scan()
