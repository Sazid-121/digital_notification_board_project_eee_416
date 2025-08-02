import gspread
from datetime import datetime
import pytz

# Constants
SERVICE_ACCOUNT_FILE = "service_account.json"
GOOGLE_SHEET_ID = "1w9C-oExk3cBsDNirHMABl1aJhoZZaNff6hUUJCnnUKw"
WORKSHEET_NAME = "Form Responses 1"

# Timezone
dhaka_tz = pytz.timezone("Asia/Dhaka")

# Column mapping
FIELD_MAP = {
    "date": "Choose the DATE when the seminar will be held:",
    "start_time": "Seminar START time:",
    "end_time": "Seminar END time:",
}

def load_worksheet():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    return sh.worksheet(WORKSHEET_NAME)

def fetch_latest_valid_meetings():
    worksheet = load_worksheet()

    try:
        rows = worksheet.get_all_records()
    except Exception as e:
        return [], None

    now = datetime.now(dhaka_tz)
    valid_entries = []
    rows_to_delete = []
    last_deleted_end_time = None  # ← Track the most recent deleted meeting's end time

    for idx, row in enumerate(rows):
        try:
            date_str = row[FIELD_MAP["date"]].strip()
            start_time_str = row[FIELD_MAP["start_time"]].strip()
            end_time_str = row[FIELD_MAP["end_time"]].strip()

            # Parse datetime
            start_dt = dhaka_tz.localize(datetime.strptime(f"{date_str} {start_time_str}", "%m/%d/%Y %I:%M:%S %p"))
            end_dt = dhaka_tz.localize(datetime.strptime(f"{date_str} {end_time_str}", "%m/%d/%Y %I:%M:%S %p"))

            # Delete if:
            # - Already ended
            # - Will end within the next 5 minutes
            if now >= end_dt or (end_dt - now).total_seconds() < 5 * 60:
                rows_to_delete.append(idx + 2)  # +2 for 1-based indexing & header
                if last_deleted_end_time is None or end_dt > last_deleted_end_time:
                    last_deleted_end_time = end_dt
                continue

            row['__start_dt'] = start_dt
            row['__end_dt'] = end_dt
            valid_entries.append(row)

        except Exception as e:
            print(f"[Warning] Row {idx+2} skipped due to parsing error: {e}")

    # Delete rows from bottom up
    for row_idx in reversed(rows_to_delete):
        worksheet.delete_rows(row_idx)
        print(f"[Info] Deleted invalid/past row {row_idx}")

    # Sort valid entries
    valid_entries.sort(key=lambda row: row['__start_dt'])

    return valid_entries, last_deleted_end_time  # ← Updated return value
