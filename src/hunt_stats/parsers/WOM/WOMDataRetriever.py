import requests
import json
import os
import time
import shutil

# Rate limit configuration (WOM is 20 req/min)
RATE_LIMIT = 20
WINDOW = 60
DELAY = WINDOW / RATE_LIMIT  # 3 seconds/request

last_request_time = 0.0


class WOMDataRetriever:
    def __init__(self, comp_id: str, hunt_edition: str):
        self.comp_id = comp_id
        self.hunt_edition = hunt_edition

        self.base_dir = os.path.join("Hunts", f"Hunt-{self.hunt_edition}")
        self.players_dir = os.path.join(self.base_dir, "players")

        os.makedirs(self.players_dir, exist_ok=True)

    # -------------------------
    # Rate-limited requests
    # -------------------------
    @staticmethod
    def rate_limited_request(url: str):
        global last_request_time

        now = time.time()
        elapsed = now - last_request_time

        if elapsed < DELAY:
            time.sleep(DELAY - elapsed)

        response = requests.get(url)
        last_request_time = time.time()

        response.raise_for_status()
        return response

    # -------------------------
    # Save JSON helper
    # -------------------------
    @staticmethod
    def save_pretty_json(filepath: str, data: dict):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # -------------------------
    # Progress bar
    # -------------------------
    @staticmethod
    def print_progress(current: int, total: int, start_time: float):
        elapsed = time.time() - start_time
        avg_time = elapsed / current if current > 0 else 0
        remaining = avg_time * (total - current)

        def format_time(t):
            if t < 60:
                return f"{t:.1f}s"
            return f"{int(t // 60)}m {int(t % 60)}s"

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
            flush=True,
        )

    # -------------------------
    # Main runner
    # -------------------------
    def run(self):
        print("\nFetching competition data...\n")

        comp_url = f"https://api.wiseoldman.net/v2/competitions/{self.comp_id}"

        try:
            comp_res = self.rate_limited_request(comp_url)
            comp_data = comp_res.json()

            self.save_pretty_json(os.path.join(self.base_dir, "competition.json"), comp_data)

            start_time = comp_data.get("startsAt")
            end_time = comp_data.get("endsAt")

            if not start_time or not end_time:
                raise ValueError("Competition response missing timestamps.")

        except Exception as e:
            print(f"Failed to fetch competition data: {e}")
            return

        # extract usernames
        participants = comp_data.get("participations", [])
        usernames = [
            p["player"]["displayName"]
            for p in participants
            if p.get("player") and p["player"].get("displayName")
        ]

        total = len(usernames)
        print(f"Found {total} participants.\n")
        print("Fetching player gains...")

        start_time_global = time.time()

        # get stats for each player
        for i, username in enumerate(usernames, start=1):
            gains_url = (
                f"https://api.wiseoldman.net/v2/players/{username}/gained"
                f"?startDate={start_time}&endDate={end_time}"
            )

            try:
                gains_res = self.rate_limited_request(gains_url)
                gains_data = gains_res.json()

                safe_name = username.replace("/", "_")
                file_path = os.path.join(self.players_dir, f"{safe_name}.json")

                self.save_pretty_json(file_path, gains_data)

            except Exception:
                pass

            self.print_progress(i, total, start_time_global)

        print("\n\nDone! All player data saved.\n")


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    retriever = WOMDataRetriever(comp_id="100262", hunt_edition="14")
    retriever.run()
