from datetime import datetime, timedelta
import pytz

dhaka_tz = pytz.timezone("Asia/Dhaka")


def determine_state(valid_meetings):
    """
    Determine current state (A, B, or C) based on the most recent meeting.

    Returns:
        - state: "A", "B", or "C"
        - selected_meeting: dict (or None if A)
    """
    now = datetime.now(dhaka_tz)

    if not valid_meetings:
        return "A", None

    # Ensure sorted by start time
    valid_meetings.sort(key=lambda row: row['__start_dt'])
    meeting = valid_meetings[0]

    start_dt = meeting['__start_dt']
    end_dt = meeting['__end_dt']

    state_b_window = start_dt - timedelta(minutes=5)
    state_c_end = end_dt - timedelta(minutes=5)

    if now < state_b_window:
        return "B", meeting  # Upcoming meeting
    elif state_b_window <= now < state_c_end:
        return "C", meeting  # Ongoing meeting
    else:
        return "A", None  # Past or ending soon
