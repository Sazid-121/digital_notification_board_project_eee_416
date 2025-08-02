import gspread
from datetime import datetime
import pytz
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from pprint import pprint

# Configuration
SERVICE_ACCOUNT_FILE = "service_account.json"
GOOGLE_SHEET_ID = "1w9C-oExk3cBsDNirHMABl1aJhoZZaNff6hUUJCnnUKw"
WORKSHEET_NAME = "Form Responses 1"

dhaka_tz = pytz.timezone("Asia/Dhaka")

# Correct field name mappings based on your actual sheet output
FIELD_MAP = {
    "topic": "Enter the seminar topic:",
    "speaker": "Enter speaker name here:",
    "photo_url": "Please upload a PHOTO of the speaker here:",
    "date": "Choose the DATE when the seminar will be held:",
    "start_time": "Seminar START time:",
    "end_time": "Seminar END time:",
}


def load_worksheet():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    return sh.worksheet(WORKSHEET_NAME)


def fetch_most_recent_valid_row():
    worksheet = load_worksheet()
    rows = worksheet.get_all_records()

    now = datetime.now(dhaka_tz)
    valid_entries = []

    for row in rows:
        try:
            date_str = row[FIELD_MAP["date"]].strip()
            start_time_str = row[FIELD_MAP["start_time"]].strip()
            end_time_str = row[FIELD_MAP["end_time"]].strip()

            start_dt = dhaka_tz.localize(datetime.strptime(f"{date_str} {start_time_str}", "%m/%d/%Y %I:%M:%S %p"))
            end_dt = dhaka_tz.localize(datetime.strptime(f"{date_str} {end_time_str}", "%m/%d/%Y %I:%M:%S %p"))

            if now < end_dt:
                row['__start_dt'] = start_dt
                row['__end_dt'] = end_dt
                valid_entries.append(row)

        except Exception as e:
            print(f"[Warning] Row skipped due to parsing error: {e}")

    if not valid_entries:
        print("No upcoming valid events found.")
        return None

    valid_entries.sort(key=lambda x: x['__start_dt'])
    return valid_entries[0]


def display_information_and_image(row):
    pprint(row)

    print("Seminar Topic:", row.get(FIELD_MAP["topic"], "N/A"))
    print("Speaker Name:", row.get(FIELD_MAP["speaker"], "N/A"))
    print("Seminar Date:", row['__start_dt'].strftime("%Y-%m-%d"))
    print("Start Time:", row['__start_dt'].strftime("%I:%M:%S %p"))
    print("End Time:", row['__end_dt'].strftime("%I:%M:%S %p"))

    image_url = row.get(FIELD_MAP["photo_url"], "").strip()

    if not image_url:
        print("[Error] No image URL provided.")
        return

    if "drive.google.com/open?id=" in image_url:
        image_url = image_url.replace("open?id=", "uc?id=")

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")

        # Plotting the info and image
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.imshow(img)
        ax.axis('off')
        plt.title(
            f"{row.get(FIELD_MAP['topic'], '')}\n"
            f"Speaker: {row.get(FIELD_MAP['speaker'], '')}\n"
            f"Date: {row['__start_dt'].strftime('%Y-%m-%d')} "
            f"{row['__start_dt'].strftime('%I:%M:%S %p')} - {row['__end_dt'].strftime('%I:%M:%S %p')}",
            fontsize=12
        )
        plt.show()

    except Exception as e:
        print(f"[Error] Failed to fetch or display image: {e}")


if __name__ == "__main__":
    row = fetch_most_recent_valid_row()
    if row:
        display_information_and_image(row)
