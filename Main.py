import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter

# Use a subset of 40 proxies
proxies_list = [
    "101.200.158.109:8808", "103.110.85.107:3128", "103.124.251.12:8081", "103.130.82.64:8080",
    "103.138.185.81:83", "103.139.253.56:8080", "103.141.105.74:55", "103.141.152.108:8989",
    "103.162.54.164:2233", "103.165.157.107:8080", "103.169.148.2:1111", "103.174.236.72:8080",
    "103.178.221.217:8080", "103.191.165.146:8090", "103.22.99.12:2020", "103.220.23.101:8080",
    "103.227.186.217:6080", "103.230.63.86:2626", "103.234.31.80:8080", "103.245.109.57:39355",
    "103.250.70.214:16464", "103.39.75.123:8080", "103.56.205.84:8080", "103.68.233.142:8097",
    "103.69.243.162:43826", "103.72.89.58:8097", "115.231.181.40:8128", "115.77.241.248:10001",
    "116.108.38.248:4002", "116.108.39.180:4002", "116.80.43.205:3172", "117.1.80.147:8080"
]

# Settings
THREADS = 20  # Number of threads
BATCH_SIZE = 50
stop_flag = False
start_flag = False
rate_limit_delay = 0.5  # Delay between requests to avoid rate limiting
discord_webhook_url = "YOUR_DISCORD_WEBHOOK_URL"

# Configure session with large connection pool
session = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount("https://", adapter)
session.mount("http://", adapter)

# ASCII Banner
def show_banner():
    print(r"""
 ####  ######   #######  ##    ## ######## 
 ##  ##    ## ##     ## ###   ##      ##  
 ##  ##       ##     ## ####  ##     ##   
 ##  ##       ##     ## ## ## ##    ##    
 ##  ##       ##     ## ##  ####   ##     
 ##  ##    ## ##     ## ##   ###  ##      
####  ######   #######  ##    ## ######## 
                                                                                                                                                 
iconZ Roblox Username Checker owner discord is @fj63
    """)

def generate_random_username():
    length = random.choice([3, 4])  # Only 3 or 4 characters
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_readable_username():
    words = ["ruinedbysin", "killedBysin", "drowninginsin", "murderedbytime"]
    return random.choice(words)

def generate_random_birthday():
    year = random.randint(2000, 2010)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"

def check_roblox_username(username):
    proxy = random.choice(proxies_list)
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    url = f"https://auth.roblox.com/v1/usernames/validate?request.username={username}&request.birthday={generate_random_birthday()}"
    try:
        response = session.get(url, proxies=proxies, timeout=3)
        if response.status_code == 200:
            return response.json().get('code') == 0
        elif response.status_code == 429:
            time.sleep(rate_limit_delay)  # Wait before retrying
            return check_roblox_username(username)  # Retry the request
    except requests.RequestException:
        return None  # Return None for network errors
    return False

def check_discord_username(username):
    proxy = random.choice(proxies_list)
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    url = f"https://discord.com/api/v9/users/{username}"
    try:
        response = session.get(url, proxies=proxies, timeout=3)
        if response.status_code == 200:
            return False  # Username is taken
        elif response.status_code == 404:
            return True  # Username is available
        elif response.status_code == 429:
            time.sleep(rate_limit_delay)  # Wait before retrying
            return check_discord_username(username)  # Retry the request
    except requests.RequestException:
        return None  # Return None for network errors
    return False

def check_tiktok_username(username):
    proxy = random.choice(proxies_list)
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    url = f"https://www.tiktok.com/@{username}"
    try:
        response = session.get(url, proxies=proxies, timeout=3)
        if response.status_code == 200:
            return False  # Username is taken
        elif response.status_code == 404:
            return True  # Username is available
        elif response.status_code == 429:
            time.sleep(rate_limit_delay)  # Wait before retrying
            return check_tiktok_username(username)  # Retry the request
    except requests.RequestException:
        return None  # Return None for network errors
    return False

def send_to_discord_webhook(message):
    payload = {"content": message}
    try:
        response = requests.post(discord_webhook_url, json=payload)
        if response.status_code != 204:
            print(f"Failed to send message to Discord webhook: {response.status_code} {response.text}")
    except requests.RequestException as e:
        print(f"Error sending message to Discord webhook: {e}")

def process_username(username, platform):
    if platform == "roblox":
        return check_roblox_username(username)
    elif platform == "discord":
        return check_discord_username(username)
    elif platform == "tiktok":
        return check_tiktok_username(username)
    return None

def listen_for_commands():
    global stop_flag, start_flag
    while True:
        cmd = input().strip().lower()
        if cmd == "start" and not start_flag:
            start_flag = True
            print("\n[✔] Start command received. Beginning checks...")
        elif cmd == "stop":
            stop_flag = True
            print("\n[!] Stop command received. Exiting gracefully...")
            break

def main():
    show_banner()

    mode = input("Select a mode: (username sniper/lookup/lookify): ").strip().lower()

    if mode == "username sniper":
        username_type = input("Do you want to generate readable words in addition to 3-4 character usernames? (yes/no): ").strip().lower()
        username_generators = [generate_random_username]
        if username_type == "yes":
            username_generators.append(generate_readable_username)

        check_discord = input("Do you want to check Discord usernames as well? (yes/no): ").strip().lower()
        check_tiktok = input("Do you want to check TikTok usernames as well? (yes/no): ").strip().lower()

        discord_webhook_url = input("Enter your Discord webhook URL: ").strip()

        input("Press Enter to start checking usernames: ")

        print("Type 'start' to begin checking usernames.")
        print("Type 'stop' anytime to exit gracefully.\n")

        threading.Thread(target=listen_for_commands, daemon=True).start()

        total_checked = 0
        available_count = 0

        try:
            with ThreadPoolExecutor(max_workers=THREADS) as executor:
                while not stop_flag:
                    if not start_flag:
                        time.sleep(1)
                        continue

                    usernames = [generate_random_username() for _ in range(BATCH_SIZE)]
                    futures = [executor.submit(process_username, username, "roblox") for username in usernames]
                    for future in futures:
                        try:
                            username = future.result()
                            if username:
                                available_count += 1
                                print(f"[+] Found Username: {username} | Total: {available_count}")
                                send_to_discord_webhook(f"[+] Found Username: {username} | Total: {available_count}")
                        except Exception as e:
                            # Handle any exceptions that occur during batch processing
                            continue

                    total_checked += BATCH_SIZE
                    print(f"[{time.strftime('%H:%M:%S')}] Checked: {total_checked} | Available: {available_count}")
                    time.sleep(2)  # Delay before next batch
        except KeyboardInterrupt:
            print("\n[!] Stopped by user.")
        finally:
            print(f"Total Checked: {total_checked}, Available Found: {available_count}")
            print("Exiting gracefully...")
    elif mode == "lookup":
        lookup_username = input("Enter the username to lookup: ").strip().lower()
        platforms = []
        if input("Do you want to check Discord? (yes/no): ").strip().lower() == "yes":
            platforms.append("discord")
        if input("Do you want to check TikTok? (yes/no): ").strip().lower() == "yes":
            platforms.append("tiktok")
        platforms.append("roblox")

        for platform in platforms:
            availability = process_username(lookup_username, platform)
            if availability is True:
                send_to_discord_webhook(f"The username '{lookup_username}' is available on {platform}.")
            elif availability is False:
                send_to_discord_webhook(f"The username '{lookup_username}' is taken on {platform}.")
            else:
                send_to_discord_webhook(f"Could not determine the availability of '{lookup_username}' on {platform}.")
    elif mode == "lookify":
        base_username = input("Enter the base username: ").strip().lower()
        variations = [
            base_username,
            base_username.replace('i', '1'),
            base_username.replace('o', '0'),
            base_username.replace('s', '5'),
            base_username.replace('a', '4'),
            base_username.replace('e', '3'),
            base_username.replace('t', '7'),
            base_username.replace('l', '1'),
            base_username.replace('b', '8'),
            base_username.replace('g', '6'),
            base_username.replace('p', '9'),
            base_username.replace('q', '9'),
            base_username.replace('z', '2'),
            base_username.replace('x', 'x'),
            base_username.replace('y', 'y'),
            base_username.replace('w', 'w'),
            base_username.replace('v', 'v'),
            base_username.replace('u', 'u'),
            base_username.replace('r', 'r'),
            base_username.replace('n', 'n'),
            base_username.replace('m', 'm'),
            base_username.replace('h', 'h'),
            base_username.replace('j', 'j'),
            base_username.replace('k', 'k'),
            base_username.replace('f', 'f'),
            base_username.replace('d', 'd'),
            base_username.replace('c', 'c'),
            base_username.replace('b', 'b'),
            base_username.replace('a', 'a'),
            base_username + '1',
            base_username + '2',
            base_username + '3',
            base_username + '4',
            base_username + '5',
            base_username + '6',
            base_username + '7',
            base_username + '8',
            base_username + '9',
            base_username + '0',
            base_username + '_',
            base_username + '-',
            base_username + '.',
            base_username + '!',
            base_username + '@',
            base_username + '#',
            base_username + '$',
            base_username + '%',
            base_username + '^',
            base_username + '&',
            base_username + '*',
            base_username + '(',
            base_username + ')',
            base_username + '_1',
            base_username + '_2',
            base_username + '_3',
            base_username + '_4',
            base_username + '_5',
            base_username + '_6',
            base_username + '_7',
            base_username + '_8',
            base_username + '_9',
            base_username + '_0',
        ]

        platforms = []
        if input("Do you want to check Discord? (yes/no): ").strip().lower() == "yes":
            platforms.append("discord")
        if input("Do you want to check TikTok? (yes/no): ").strip().lower() == "yes":
            platforms.append("tiktok")
        platforms.append("roblox")

        for platform in platforms:
            for variation in variations:
                availability = process_username(variation, platform)
                if availability is True:
                    send_to_discord_webhook(f"The username '{variation}' is available on {platform}.")
                elif availability is False:
                    send_to_discord_webhook(f"The username '{variation}' is taken on {platform}.")
                else:
                    send_to_discord_webhook(f"Could not determine the availability of '{variation}' on {platform}.")
    else:
        print("Invalid mode selected. Exiting...")

if __name__ == "__main__":
    main()
