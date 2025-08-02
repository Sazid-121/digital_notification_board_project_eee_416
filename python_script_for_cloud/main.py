import time
from datetime import datetime, timedelta
import pytz

from fetch_sheet import fetch_latest_valid_meetings
from determine_state import determine_state
from render_state_a import render_state_a
from render_state_b import render_state_b
from render_state_c import render_state_c
from convert_to_bin import save_image_as_bin
from version_manager import write_version
from state_summary import get_summary_for_state
from content_hasher import generate_content_hash
from upload_to_github import upload_files_to_github
from remote_version import fetch_remote_version

# === GitHub Config ===
GITHUB_TOKEN = "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"
REPO_NAME = "Sazid-121/esp32-vga-notification-board"
BRANCH = "main"

# === Initial Setup ===
version = fetch_remote_version()
print(f"[INFO] Initialized version from server: {version}")

previous_state = None
previous_data = {}

dhaka_tz = pytz.timezone("Asia/Dhaka")

# === Main Loop ===
while True:
    now = datetime.now(dhaka_tz)
    if now.second == 0:
        print(f"\n[INFO] Checking at {now.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

        try:
            valid_meetings, deleted_end_time = fetch_latest_valid_meetings()  # ⬅️ updated
        except Exception as e:
            print(f"[ERROR] Failed to fetch meetings: {e}", flush=True)
            time.sleep(10)
            continue

        if not valid_meetings:
            print("[INFO] No upcoming meetings found. Staying in state A.", flush=True)
            current_state, meeting = "A", None
        else:
            current_state, meeting = determine_state(valid_meetings)

        current_summary = get_summary_for_state(current_state, meeting)
        current_hash = generate_content_hash(meeting, current_state)
        previous_summary = previous_data.get("summary")
        previous_hash = previous_data.get("hash")

        should_update = (
            current_state != previous_state or
            current_summary != previous_summary or
            current_hash != previous_hash
        )

        if should_update:
            print(f"[INFO] State or content changed: {previous_state} → {current_state}", flush=True)

            # Increment version
            version = (version + 1) % 10

            # === Determine when to render the image ===
            render_time = None
            if previous_state == "C" and current_state in ["A", "B"]:
                if deleted_end_time:
                    render_time = deleted_end_time - timedelta(minutes=1)
            elif current_state == "C" and previous_state == "B":
                render_time = meeting['__start_dt'] - timedelta(minutes=1)

            # === Render image
            if current_state == "A":
                img = render_state_a()
            elif current_state == "B":
                topic = meeting.get("Enter the seminar topic:", "Unknown Topic")
                speaker = meeting.get("Enter speaker name here:", "Unknown Speaker")
                date = meeting.get("Choose the DATE when the seminar will be held:", "")
                time_ = meeting.get("Seminar START time:", "")
                datetime_str = f"{date}, {time_}"
                img = render_state_b(topic, datetime_str, speaker)
            elif current_state == "C":
                topic = meeting.get("Enter the seminar topic:", "Unknown Topic")
                speaker = meeting.get("Enter speaker name here:", "Unknown Speaker")
                image_url = meeting.get("Please upload a PHOTO of the speaker here:", "")
                abstract = meeting.get("Enter the abstract of the seminar: (in 150 words)", "No abstract provided")
                img = render_state_c(topic, speaker, image_url, abstract)
            else:
                print("[ERROR] Unknown state. Skipping render.", flush=True)
                time.sleep(1)
                continue

            # === Save framebuffer
            save_image_as_bin(img, "display_image_rgb565.bin")

            # === Write version file with trigger time
            write_version(version, render_time)

            # === Upload to GitHub
            upload_files_to_github(
                token=GITHUB_TOKEN,
                repo_name=REPO_NAME,
                branch=BRANCH
            )

            # Wait for GitHub cache
            time.sleep(10)

            # === Track current info
            previous_state = current_state
            previous_data["summary"] = current_summary
            previous_data["hash"] = current_hash

        else:
            print(f"[INFO] No update needed. Still in state {current_state}.", flush=True)

        time.sleep(1)
    else:
        time.sleep(0.2)




