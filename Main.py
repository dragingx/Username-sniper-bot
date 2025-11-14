import requests
import random
import string
import time
import threading
import math
import os
from concurrent.futures import ThreadPoolExecutor

# =========================
# ====== CONFIG ==========
# =========================
NAMES_TO_FIND = 300000       # total usernames to find
LENGTHS = [3, 4, 5]          # only 3–5 letter usernames
WORKER_THREADS = 8           # adjust for your hosting environment
CHECK_SLEEP = 0.05           # delay per thread

VALID_FILE = "valid.txt"
LOG_FILE = "scan_log.txt"

BIRTHDAY = "1999-04-20"
ROBLOX_VALIDATE_URL = "https://auth.roblox.com/v1/usernames/validate"

WEBHOOK_URL = "https://discord.com/api/webhooks/1438742305904398376/pIIR53lJZXDUCnhxVnjyQZtYPkvHMs4joBmZW6AltyZ053A_l0j3IozUCWgena6MZOdi"  # <-- Replace with your webhook
WEBHOOK_NAME = "Username Scanner"
WEBHOOK_AVATAR = None

PAGE_SIZE = 18
MAX_EMBED_DESC = 1900

# =========================
# ====== GLOBALS =========
# =========================
found_usernames = []
found_lock = threading.Lock()
checked_counter = 0
checked_lock = threading.Lock()
stop_event = threading.Event()
last_username = ""
last_status = ""
current_page_index = 0

# =========================
# ====== LOGGING =========
# =========================
def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a+", encoding="utf-8") as lf:
        lf.write(f"[{ts}] {msg}\n")
    print(msg)

# =========================
# ====== USERNAMES =======
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
# ====== PROGRESS BAR =====
# =========================
def make_progress_bar(current, total, size=20):
    if total <= 0:
        return "`[{}] 0%`".format("░" * size)
    progress = min(1.0, float(current) / total)
    filled = int(round(size * progress))
    bar = "█" * filled + "░" * (size - filled)
    percent = int(progress * 100)
    return f"`[{bar}] {percent}%`"

# =========================
# ====== WEBHOOK =========
# =========================
def send_embed(found_count, checked_count, last_user, status, page_idx=0):
    """Sends a new Discord embed with current scan status."""
    bar = make_progress_bar(found_count, NAMES_TO_FIND, size=20)
    with found_lock:
        total_found = len(found_usernames)
        pages = max(1, math.ceil(total_found / PAGE_SIZE))
        page_idx = page_idx % pages
        start = page_idx * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = found_usernames[start:end]
        desc = "\n".join(f"`{u}`" for u in page_items) if page_items else "None yet."
        if len(desc) > MAX_EMBED_DESC:
            desc = desc[:MAX_EMBED_DESC-4] + "..."

    embeds = [
        {"title": "🔍 Username Scanner — Live Status",
         "color": 0x2ecc71 if status == "available" else (0xe74c3c if status=="taken" else 0xf1c40f),
         "fields":[
             {"name":"Found","value":str(found_count),"inline":True},
             {"name":"Goal","value":str(NAMES_TO_FIND),"inline":True},
             {"name":"Checked","value":str(checked_count),"inline":True},
             {"name":"Progress","value":bar,"inline":False},
             {"name":"Last Username","value":f"`{last_user}`","inline":False},
             {"name":"Status","value":status,"inline":False}],
         "footer":{"text":f"Page {page_idx+1}/{pages}"}},
        {"title":f"📜 Found Usernames — Page {page_idx+1}/{pages}",
         "description": desc,
         "color": 0x2ecc71}
    ]
    payload = {"embeds": embeds}
    if WEBHOOK_NAME:
        payload["username"] = WEBHOOK_NAME
    if WEBHOOK_AVATAR:
        payload["avatar_url"] = WEBHOOK_AVATAR
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        log("Error sending embed: " + str(e))

# =========================
# ====== WORKER THREAD ====
# =========================
def worker_thread(thread_id):
    global checked_counter, last_username, last_status, current_page_index
    while not stop_event.is_set():
        with checked_lock:
            if len(found_usernames) >= NAMES_TO_FIND:
                break
            checked_counter += 1
            checked_now = checked_counter

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
            log(f"[FOUND] {username}")

            # SEND NEW EMBED IMMEDIATELY
            with found_lock:
                fcount = len(found_usernames)
            with checked_lock:
                ccount = checked_counter
            send_embed(fcount, ccount, username, "available", page_idx=current_page_index)

        elif code is None:
            last_status = "network-error"
            log(f"[NET ERR] {username}")
        else:
            last_status = "taken"
            log(f"[TAKEN] {username}")

        last_username = username
        time.sleep(CHECK_SLEEP)

# =========================
# ====== DASHBOARD =======
# =========================
def dashboard_loop():
    global current_page_index
    last_edit_time = 0
    while not stop_event.is_set():
        with found_lock:
            total_found = len(found_usernames)
            pages = max(1, math.ceil(total_found/PAGE_SIZE))
        current_page_index = (current_page_index + 1) % pages if pages>0 else 0
        now = time.time()
        if now - last_edit_time >= 5:  # send a page rotation embed every 5 sec
            with found_lock: fcount = len(found_usernames)
            with checked_lock: ccount = checked_counter
            send_embed(fcount, ccount, last_username if last_username else "-", last_status if last_status else "starting", page_idx=current_page_index)
            last_edit_time = now
        time.sleep(1)

# =========================
# ====== START SCAN ======
# =========================
def start_scan():
    if stop_event.is_set():
        stop_event.clear()
    for f in [VALID_FILE, LOG_FILE]:
        if os.path.exists(f): os.remove(f)
    log("Scan starting.")

    threading.Thread(target=dashboard_loop, daemon=True).start()
    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        futures = [executor.submit(worker_thread, i) for i in range(WORKER_THREADS)]
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

    # final embed
    send_embed(len(found_usernames), checked_counter, last_username if last_username else "-", "complete", page_idx=0)
    upload_logs()
    log("Scan finished.")

# =========================
# ====== LOG UPLOAD =======
# =========================
def upload_logs():
    files_payload = {}
    if os.path.exists(VALID_FILE):
        files_payload["valid.txt"] = open(VALID_FILE,"rb")
    if os.path.exists(LOG_FILE):
        files_payload["scan_log.txt"] = open(LOG_FILE,"rb")
    if not files_payload:
        return
    post_kwargs = {"files": files_payload,"data":{"content":"📁 Scan finished — logs attached."}}
    if WEBHOOK_NAME:
        post_kwargs["data"]["username"] = WEBHOOK_NAME
    if WEBHOOK_AVATAR:
        post_kwargs["data"]["avatar_url"] = WEBHOOK_AVATAR
    try:
        requests.post(WEBHOOK_URL, **post_kwargs)
        log("Logs uploaded.")
    except Exception as e:
        log("Failed to upload logs: "+str(e))
    finally:
        for f in list(files_payload.values()):
            try: f.close()
            except: pass

# =========================
# ====== ENTRY POINT ======
# =========================
if __name__=="__main__":
    if not WEBHOOK_URL or "YOUR_WEBHOOK_HERE" in WEBHOOK_URL:
        print("ERROR: Please set WEBHOOK_URL before running.")
    else:
