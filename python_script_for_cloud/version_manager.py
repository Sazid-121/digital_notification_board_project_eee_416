from datetime import datetime

VERSION_FILE = "version.txt"

def write_version(version, trigger_time=None):
    """
    Writes version.txt with:
    - version (0–9)
    - 'now' OR an ISO timestamp string like '2025-07-19T13:59:00'

    Params:
    - version: int
    - trigger_time: datetime object (or None to use 'now')
    """
    version_num = version % 10
    render_time_str = "now" if trigger_time is None else trigger_time.isoformat()

    with open(VERSION_FILE, "w") as f:
        f.write(f"{version_num}\n{render_time_str}\n")

    print(f"[Info] Updated version.txt → version: {version_num}, render_time: {render_time_str}")


def read_version():
    """
    Reads version.txt and returns (version_number, render_time_str)
    """
    try:
        with open(VERSION_FILE, "r") as f:
            lines = f.readlines()
            version = int(lines[0].strip())
            render_time_str = lines[1].strip()
            return version, render_time_str
    except Exception as e:
        print(f"[Warning] Could not read version.txt: {e}")
        return None, None
