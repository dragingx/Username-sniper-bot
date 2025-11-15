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
THREADS = 100
SLEEP = 0

VALID_FILE = "valid.txt"
LOG_FILE = "log.txt"

BIRTHDAY = "1999-04-20"
ROBLOX_URL = "https://auth.roblox.com/v1/usernames/validate"

WEBHOOK_URL = "https://discord.com/api/webhooks/1438748098145947809/dFFPhpnH2CMW3I43K6gjiyaFeA9Qa9v8xnZZ6kgp_NFEFPbzNsfk7_L_g_t3Ex4JUIE4"

# =========================
# == GLOBAL VARIABLES =====
# =========================
found = []
checked = 0
found_lock = threading.Lock()
checked_lock = threading.Lock()
stop_event = threading.Event()

message_id = None   # webhook message we will update


# =========================
# ====== UTILITIES ========
# =========================

def log(msg):
    with open(LOG_FILE, "a+", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def make_username(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def check_username(username):
    params = {
        "request.username": username,
        "request.birthday": BIRTHDAY
    }
    try:
        r = requests.get(ROBLOX_URL, params=params, timeout=5)
        r.raise_for_status()
        return r.json().get("code")
    except:
        return None


# =========================
# === WEBHOOK FUNCTIONS ===
# =========================

def send_initial_embed():
    global message_id

    payload = {
        "content": "",
        "embeds": [
            {
                "title": "🔍 Username Scanner",
                "description": "Starting scan...",
                "color": 0x3498db
            }
        ]
    }

    r = requests.post(WEBHOOK_URL, json=payload)
    r.raise_for_status()
    message_id = r.json()["id"]   # store message id


def update_embed():
    """Updates ONE webhook message forever."""
    if message_id is None:
        return

    update_url = WEBHOOK_URL + f"/messages/{message_id}"

    with checked_lock:
        checked_now = checked
    with found_lock:
        found_now = list(found)

    usernames_text = "\n".join(found_now) if found_now else "None yet."
    stats = f"**Found:** {len(found_now)}\n**Checked:** {checked_now}\n"

    payload = {
        "content": "",
        "embeds": [
            {
                "title": "🔍 Live Username Scanner",
                "description": stats + "\n**Usernames:**\n```\n" +
                               usernames_text[:1500] + "\n```",
                "color": 0x2ecc71
            }
        ]
    }

    try:
        requests.patch(update_url, json=payload)
    except:
        pass



# =========================
# === THREAD WORKER =======
# =========================

def worker():
    global checked

    while not stop_event.is_set():

        # Count checked
        with checked_lock:
            checked += 1
            if len(found) >= NAMES_TO_FIND:
                return

        # Generate username
        username = make_username(random.choice(LENGTHS))
        code = check_username(username)

        # Found
        if code == 0:
            with found_lock:
                if username not in found:
                    found.append(username)

                    # update valid.txt (append at bottom)
                    with open(VALID_FILE, "a+", encoding="utf-8") as f:
                        f.write(username + "\n")

            log(f"[FOUND] {username}")

        time.sleep(SLEEP)



# =========================
# ===== MAIN LOGIC ========
# =========================

def start():
    global message_id

    if os.path.exists(VALID_FILE):
        os.remove(VALID_FILE)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    open(VALID_FILE, "w").close()

    send_initial_embed()

    # Update embed loop
    def embed_loop():
        while not stop_event.is_set():
            update_embed()
            time.sleep(1)

    threading.Thread(target=embed_loop, daemon=True).start()

    # Scan threads
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(worker)

    stop_event.set()
    update_embed()


# =========================
# ===== ENTRY POINT =======
# =========================
if __name__ == "__main__":
    start()
