import time
import numpy as np
import matplotlib.pyplot as plt
import requests
import random
from datetime import datetime
import pytz

# === GitHub Raw URLs ===
VERSION_URL = "https://raw.githubusercontent.com/Sazid-121/esp32-vga-notification-board/main/version.txt"
BIN_URL = "https://raw.githubusercontent.com/Sazid-121/esp32-vga-notification-board/main/display_image_rgb565.bin"

# === Display Settings ===
WIDTH, HEIGHT = 640, 480
current_version = None
dhaka_tz = pytz.timezone("Asia/Dhaka")

def rgb565_to_rgb888(pixel):
    r = ((pixel >> 11) & 0x1F) << 3
    g = ((pixel >> 5) & 0x3F) << 2
    b = (pixel & 0x1F) << 3
    return r, g, b

def download_version():
    response = requests.get(VERSION_URL)
    if response.status_code != 200:
        raise Exception("Failed to fetch version.txt")

    lines = response.text.strip().splitlines()
    if len(lines) < 2:
        raise Exception("Invalid version.txt format")

    version_num = int(lines[0].strip())
    render_time_str = lines[1].strip()

    return version_num, render_time_str

def download_bin():
    response = requests.get(f"{BIN_URL}?nocache={random.randint(1000,9999)}")
    if response.status_code != 200:
        raise Exception(".bin download failed")
    return response.content

def parse_image_from_bin(data):
    expected_size = WIDTH * HEIGHT * 2
    if len(data) != expected_size:
        raise ValueError(f"Expected {expected_size} bytes, got {len(data)} bytes")

    image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    for i in range(WIDTH * HEIGHT):
        offset = i * 2
        pixel_565 = data[offset] | (data[offset + 1] << 8)
        r, g, b = rgb565_to_rgb888(pixel_565)
        y = i // WIDTH
        x = i % WIDTH
        image[y, x] = [r, g, b]
    return image

def wait_until(render_time_str):
    try:
        render_time = datetime.fromisoformat(render_time_str).replace(tzinfo=dhaka_tz)
    except Exception:
        print("[WARN] Invalid render time. Rendering immediately.")
        return

    while datetime.now(dhaka_tz) < render_time:
        remaining = (render_time - datetime.now(dhaka_tz)).total_seconds()
        print(f"[WAIT] Waiting {int(remaining)}s until render time...")
        time.sleep(min(5, remaining))

# === Main Loop ===
print("[INFO] ESP32 Display Emulator Running. Press Ctrl+C to stop.")

try:
    while True:
        print(f"\n[INFO] Checking at {datetime.now(dhaka_tz).strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            version, render_time_str = download_version()

            if version != current_version:
                print(f"[UPDATE] Version changed: {current_version} → {version}")
                bin_data = download_bin()

                if render_time_str == "now":
                    print("[ACTION] Rendering immediately.")
                else:
                    print(f"[SCHEDULED] Render time: {render_time_str}")
                    wait_until(render_time_str)

                # Render image
                img = parse_image_from_bin(bin_data)
                plt.close('all')
                plt.figure(figsize=(10, 6))
                plt.imshow(img)
                plt.title(f"Rendered (Version {version})")
                plt.axis("off")
                plt.tight_layout()
                plt.show(block=False)
                plt.pause(5)

                current_version = version
            else:
                print(f"[INFO] No update. Current version: {current_version}")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(30)

except KeyboardInterrupt:
    print("\n[EXIT] Emulator stopped.")
