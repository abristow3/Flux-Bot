import json
import os


def load_json_data(filepath) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_data(filepath: str, data: dict) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class WOMDataParser:
    def __init__(self, hunt_edition: str):
        self.hunt_edition = hunt_edition

        self.players_dir = os.path.join("src", "hunt-stats", "data", f"Hunt-{hunt_edition}", "players")
        self.competition_fp = os.path.join("src", "hunt-stats", "data", f"Hunt-{hunt_edition}", "competition.json")
        self.hunt_metrics_fp = os.path.join("src", "hunt-stats", "data", f"Hunt-{hunt_edition}", "hunt_metrics.json")

        self.competition_data = load_json_data(self.competition_fp)
        self.hunt_metrics_data = load_json_data(self.hunt_metrics_fp)

        # Build player index (player name -> player object)
        self.player_index = self._build_player_index()

        # Build EHB lookup (player name -> EHB)
        self.ehb_by_player = {
            p["player"]["displayName"]: p["progress"]["gained"]
            for p in self.competition_data.get("participations", [])
            if p.get("player") and p["player"].get("displayName")
        }

    # -------------------------
    # Helpers
    # -------------------------
    def _build_player_index(self) -> dict:
        index = {}
        for team_data in self.hunt_metrics_data.values():
            for player_name, player_obj in team_data.get("players", {}).items():
                index[player_name] = player_obj
        return index

    def _get_player_obj(self, player_name: str) -> dict | None:
        return self.player_index.get(player_name)

    def _ensure_wom_bucket(self, player_obj: dict) -> dict:
        if "wom" not in player_obj:
            player_obj["wom"] = {}
        return player_obj["wom"]

    # -------------------------
    # Calculations
    # -------------------------
    def calculate_player_ehb(self) -> None:
        for player_name, ehb in self.ehb_by_player.items():
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            wom["ehb"] = ehb

    def calculate_total_bosses_killed(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue
            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            wom["boss_kills"] = 0
            player_data = load_json_data(os.path.join(self.players_dir, file))
            for boss_info in player_data["data"]["bosses"].values():
                wom["boss_kills"] += boss_info.get("kills", {}).get("gained", 0)

    def calculate_total_raids_killed(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue
            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            wom.update({"raids": 0, "cox": 0, "tob": 0, "toa": 0})
            player_data = load_json_data(os.path.join(self.players_dir, file))
            for boss_name, boss_info in player_data["data"]["bosses"].items():
                kills = boss_info.get("kills", {}).get("gained", 0)
                if "chambers_of_xeric" in boss_name:
                    wom["cox"] += kills
                    wom["raids"] += kills
                elif "theatre_of_blood" in boss_name:
                    wom["tob"] += kills
                    wom["raids"] += kills
                elif "tombs_of_amascut" in boss_name:
                    wom["toa"] += kills
                    wom["raids"] += kills

    def calculate_total_barrows_killed(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue
            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            wom["barrows"] = 0
            player_data = load_json_data(os.path.join(self.players_dir, file))
            for boss_name, boss_info in player_data["data"]["bosses"].items():
                if "barrows_chests" in boss_name:
                    wom["barrows"] += boss_info.get("kills", {}).get("gained", 0)

    def calculate_total_clues_completed(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue
            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            wom["clues"] = {"total": 0, "beginner": 0, "easy": 0, "medium": 0, "hard": 0, "elite": 0, "master": 0}
            player_data = load_json_data(os.path.join(self.players_dir, file))
            for activity_name, activity_info in player_data["data"]["activities"].items():
                gained = activity_info.get("score", {}).get("gained", 0)
                if "clue_scrolls_all" in activity_name:
                    wom["clues"]["total"] += gained
                elif "clue_scrolls_beginner" in activity_name:
                    wom["clues"]["beginner"] += gained
                elif "clue_scrolls_easy" in activity_name:
                    wom["clues"]["easy"] += gained
                elif "clue_scrolls_medium" in activity_name:
                    wom["clues"]["medium"] += gained
                elif "clue_scrolls_hard" in activity_name:
                    wom["clues"]["hard"] += gained
                elif "clue_scrolls_elite" in activity_name:
                    wom["clues"]["elite"] += gained
                elif "clue_scrolls_master" in activity_name:
                    wom["clues"]["master"] += gained

    def calculate_total_xp(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue
            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue
            wom = self._ensure_wom_bucket(player_obj)
            player_data = load_json_data(os.path.join(self.players_dir, file))
            wom["xp_gained"] = player_data["data"]["skills"]["overall"]["experience"]["gained"]

    def calculate_most_killed_boss(self) -> None:
        for file in os.listdir(self.players_dir):
            if not file.endswith(".json"):
                continue

            player_name = file.replace(".json", "")
            player_obj = self._get_player_obj(player_name)
            if not player_obj:
                continue

            wom = self._ensure_wom_bucket(player_obj)

            player_data = load_json_data(os.path.join(self.players_dir, file))
            bosses = player_data.get("data", {}).get("bosses", {})

            most_killed_boss = None
            most_kills = 0

            for boss_name, boss_info in bosses.items():
                kills = boss_info.get("kills", {}).get("gained", 0)

                if kills > most_kills:
                    most_kills = kills
                    most_killed_boss = boss_name

            # Store result in WOM bucket
            if most_killed_boss is not None:
                wom["most_killed_boss"] = {
                    "boss": most_killed_boss,
                    "kills": most_kills
                }


    # -------------------------
    # Save
    # -------------------------
    def save(self) -> None:
        save_json_data(self.hunt_metrics_fp, self.hunt_metrics_data)

    # -------------------------
    # Run all calculations
    # -------------------------
    def run(self) -> None:
        self.calculate_player_ehb()
        self.calculate_total_bosses_killed()
        self.calculate_total_raids_killed()
        self.calculate_total_barrows_killed()
        self.calculate_total_clues_completed()
        self.calculate_total_xp()
        self.calculate_most_killed_boss()
        self.save()
        print("WOM PARSING COMPLETED")
