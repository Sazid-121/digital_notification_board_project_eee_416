import requests

def fetch_remote_version():
    VERSION_URL = "https://raw.githubusercontent.com/Sazid-121/esp32-vga-notification-board/main/version.txt"
    try:
        response = requests.get(VERSION_URL, timeout=10)
        if response.status_code != 200:
            raise Exception("Failed to fetch version.txt")
        lines = response.text.strip().splitlines()
        if len(lines) < 2:
            raise Exception("Invalid version.txt format")

        version_num = int(lines[0].strip())

        return version_num
    except Exception as e:
        print(f"[WARN] Could not fetch remote version: {e}")
    return -1  # Default fallback if failed
