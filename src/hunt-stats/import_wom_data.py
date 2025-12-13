'''
Calculate totals for entire hunt
- total raids completed
- total cox, toa, tob
- total xp gained
- total boss kills loop over [participations][player_id], then query player endpoint and look loops over [data][bosses][<boss_name>][kills][gained] and sum
- total participants (can be retrieved from event object)

[data][bosses][<boss_name>][kills][gained]
'''

import requests
import json
import os
import time
import math
import shutil

'''
Features:
- Rate limiting (20 req/min)
- Progress bar with estimated time remaining
- Saves competition + player gain data
'''

# -----------------------------
# Rate limit configuration
# -----------------------------
RATE_LIMIT = 20
WINDOW = 60
DELAY = WINDOW / RATE_LIMIT  # 3 seconds/request

last_request_time = 0.0


def rate_limited_request(url):
    global last_request_time

    now = time.time()
    elapsed = now - last_request_time

    if elapsed < DELAY:
        sleep_time = DELAY - elapsed
        time.sleep(sleep_time)

    response = requests.get(url)
    last_request_time = time.time()

    response.raise_for_status()
    return response


def save_pretty_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -----------------------------
# Progress bar helper
# -----------------------------
def print_progress(current, total, start_time):
    elapsed = time.time() - start_time
    avg_time = elapsed / current if current > 0 else 0
    remaining = avg_time * (total - current)

    # Format time
    def format_time(t):
        if t < 60:
            return f"{t:.1f}s"
        return f"{int(t//60)}m {int(t%60)}s"

    term_width = shutil.get_terminal_size((80, 20)).columns
    bar_width = min(40, term_width - 40)

    filled = int((current / total) * bar_width)
    bar = "[" + "#" * filled + "-" * (bar_width - filled) + "]"

    percent = (current / total) * 100

    print(
        f"\r{bar} {percent:5.1f}% | "
        f"{current}/{total} | "
        f"ETR: {format_time(remaining)}",
        end="",
        flush=True
    )


# -----------------------------
# Main execution
# -----------------------------
if __name__ == '__main__':
    comp_id = "100262"
    hunt_name = "Hunt-14"

    BASE_DIR = os.path.join("Hunts", hunt_name)
    PLAYERS_DIR = os.path.join(BASE_DIR, "players")

    os.makedirs(PLAYERS_DIR, exist_ok=True)

    print("\nFetching competition data...\n")

    # -----------------------------
    # 1. Fetch competition data
    # -----------------------------
    comp_url = f"https://api.wiseoldman.net/v2/competitions/{comp_id}"

    try:
        comp_res = rate_limited_request(comp_url)
        comp_data = comp_res.json()

        save_pretty_json(os.path.join(BASE_DIR, "competition.json"), comp_data)

        start_time = comp_data.get("startsAt")
        end_time = comp_data.get("endsAt")

        if not start_time or not end_time:
            raise ValueError("Competition response missing timestamps.")

    except Exception as e:
        print(f"Failed to fetch competition data: {e}")
        exit(1)

    # -----------------------------
    # 2. Extract usernames
    # -----------------------------
    participants = comp_data.get("participations", [])
    usernames = [
        p["player"]["displayName"]
        for p in participants
        if p.get("player") and p["player"].get("displayName")
    ]

    total = len(usernames)
    print(f"Found {total} participants.\n")
    print("Fetching player gains...")

    # -----------------------------
    # 3. Fetch gains for each player w/ progress bar
    # -----------------------------
    start_time_global = time.time()

    for i, username in enumerate(usernames, start=1):

        gains_url = (
            f"https://api.wiseoldman.net/v2/players/{username}/gained"
            f"?startDate={start_time}&endDate={end_time}"
        )

        try:
            gains_res = rate_limited_request(gains_url)
            gains_data = gains_res.json()

            safe_name = username.replace("/", "_")
            file_path = os.path.join(PLAYERS_DIR, f"{safe_name}.json")

            save_pretty_json(file_path, gains_data)

        except Exception:
            pass  # Keep going even if one user fails

        print_progress(i, total, start_time_global)

    print("\n\nDone! All player data saved.\n")

