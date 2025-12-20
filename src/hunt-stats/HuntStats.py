from parsers.WOM.WOMDataParser import WOMDataParser
from parsers.WOM.WOMDataRetriever import WOMDataRetriever
from parsers.GDoc.GDocDataParser import GDocDataParser
from parsers.GDoc.GDocDataRetriever import GDocDataRetriever
import json
import os
from pathlib import Path

def load_json_data(filepath) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

class HuntStats:
    def __init__(self, hunt_edition: str, gdoc_sheet_id: str, wom_comp_id: str):
        self.hunt_edition: str = hunt_edition
        self.gdoc_sheet_id: str = gdoc_sheet_id
        self.wom_comp_id: str = wom_comp_id
        # Match the directory structure used by GDocDataParser
        self.json_path = Path(os.path.join("src", "hunt-stats", "data", f"Hunt-{self.hunt_edition}", "hunt_metrics.json"))
        self.data = {}

    def run(self) -> None:
        # Fetch GDoc Data
        # gdoc_data = GDocDataRetriever(sheet_id=self.gdoc_sheet_id)
        # gdoc_parser = GDocDataParser(gdoc=gdoc_data, hunt_edition=self.hunt_edition)
        # gdoc_parser.run()

        # Fetch WoM Data
        # wom_data = WOMDataRetriever(comp_id=self.wom_comp_id, hunt_edition=self.hunt_edition)
        # wom_data.run()  # Uncomment if fetching from API

        # Lowercase all filename
        self.lowercase_filenames("src/hunt-stats/data/Hunt-14/players")

        wom_parser = WOMDataParser(hunt_edition=self.hunt_edition)
        wom_parser.run()

        # Load JSON data
        self.load_json()

        # Lowercase all player names
        self.lowercase_player_names()

        # Calculate totals
        self.calculate_team_totals()

        # Calculate points & coin per EHB
        self.calculate_player_points_per_ehb()
        self.calculate_player_coins_per_ehb()
        self.calculate_player_drops_per_ehb()

        # Calc team best point per EHB
        self.calculate_team_best_avg_points_per_ehb()
        self.calculate_team_best_avg_coins_per_ehb()
        self.calculate_team_best_drops_per_ehb()

        # Calc most killed boss for each team
        self.calculate_team_most_killed_boss(wom_parser.players_dir)

        # Count entries missing WoM data
        self.count_players_missing_wom()

        # Save JSON back
        self.save_json()

    def load_json(self):
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            raise FileNotFoundError(f"{self.json_path} does not exist.")

    def save_json(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def calculate_team_totals(self) -> None:
        for team_name, team_data in self.data.items():
            totals = {
                "total_drops": 0,
                "total_points": 0.0,
                "total_coins": 0,
                "total_pets": 0,
                "total_jars": 0,
                "total_mega_rares": 0,
                "total_cox": 0,
                "total_tob": 0,
                "total_toa": 0,
                "total_raids": 0,
                "total_ehb": 0.0,
                "total_clues": 0,
                "clues_breakdown": {
                    "beginner": 0,
                    "easy": 0,
                    "medium": 0,
                    "hard": 0,
                    "elite": 0,
                    "master": 0
                },
                "total_xp": 0
            }

            players = team_data.get("players", {})
            for player, pdata in players.items():
                totals["total_drops"] += pdata.get("total_drops", 0)
                totals["total_coins"] += int(pdata.get("total_coins", "0").replace(",", ""))
                totals["total_pets"] += pdata.get("boss_pets", 0)
                totals["total_jars"] += pdata.get("jars", 0)
                totals["total_mega_rares"] += pdata.get("mega_rares", 0)

                wom = pdata.get("wom", {})
                totals["total_cox"] += wom.get("cox", 0)
                totals["total_tob"] += wom.get("tob", 0)
                totals["total_toa"] += wom.get("toa", 0)
                totals["total_raids"] += wom.get("raids", 0)
                totals["total_ehb"] += wom.get("ehb", 0.0)
                totals["total_xp"] += wom.get("xp_gained", 0)

                clues = wom.get("clues", {})
                totals["total_clues"] += clues.get("total", 0)
                for key in totals["clues_breakdown"]:
                    totals["clues_breakdown"][key] += clues.get(key, 0)

            # Format totals for JSON like your example
            team_data["team_totals"] = {
                "total_drops": totals["total_drops"],
                "total_points": f"{totals['total_points']:,}",
                "total_coins": f"{totals['total_coins']:,}",
                "total_pets": totals["total_pets"],
                "total_jars": totals["total_jars"],
                "total_mega_rares": totals["total_mega_rares"],
                "total_cox": totals["total_cox"],
                "total_tob": totals["total_tob"],
                "total_toa": totals["total_toa"],
                "total_raids": totals["total_raids"],
                "total_ehb": round(totals["total_ehb"], 4),
                "total_clues": totals["total_clues"],
                "clues_breakdown": totals["clues_breakdown"],
                "total_xp": totals["total_xp"]
            }

    def calculate_player_points_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            for player_data in players.values():
                # Get total points (string -> float)
                points_str = player_data.get("total_points", "0")
                total_points = float(points_str.replace(",", ""))

                # Get EHB
                ehb = player_data.get("wom", {}).get("ehb", 0)

                # Calculate average points per EHB
                if ehb > 0:
                    points_per_ehb = total_points / ehb
                else:
                    points_per_ehb = 0.0

                # Store result (rounded if you want)
                player_data["points_per_ehb"] = round(points_per_ehb, 2)

    def calculate_team_best_avg_points_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            best_player = None
            best_value = -1

            for player_name, player_data in players.items():
                value = player_data.get("points_per_ehb")

                if value is None:
                    continue

                if value > best_value:
                    best_value = value
                    best_player = player_name

            if best_player is not None:
                team_data.setdefault("team_totals", {})
                team_data["team_totals"]["best_points_per_ehb"] = (
                    f"{best_player} ({best_value})"
                )

    def calculate_player_coins_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            for player_data in players.values():
                # Get total coins (string with commas -> float)
                coins_str = player_data.get("total_coins", "0")
                total_coins = float(coins_str.replace(",", ""))

                # Get EHB
                ehb = player_data.get("wom", {}).get("ehb", 0)

                # Calculate coins per EHB
                if ehb > 0:
                    coins_per_ehb = total_coins / ehb
                else:
                    coins_per_ehb = 0.0

                # Store result (rounded for readability)
                player_data["coins_per_ehb"] = round(coins_per_ehb, 2)

    def calculate_team_best_avg_coins_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            best_player = None
            best_value = -1

            for player_name, player_data in players.items():
                value = player_data.get("coins_per_ehb")

                if value is None:
                    continue

                if value > best_value:
                    best_value = value
                    best_player = player_name

            if best_player is not None:
                team_data.setdefault("team_totals", {})
                # Format the number with commas
                formatted_value = f"{best_value:,.2f}"
                team_data["team_totals"]["best_coins_per_ehb"] = (
                    f"{best_player} ({formatted_value})"
                )

    def count_players_missing_wom(self) -> None:
        for team_name, team_data in self.data.items():
            players = team_data.get("players", {})

            missing_names = []

            for player_name, player_data in players.items():
                if "wom" not in player_data:
                    missing_names.append(player_name)

            print(f"{team_name}: {len(missing_names)} players missing wom data")

            if missing_names:
                print("  Players:", ", ".join(missing_names))

    def lowercase_filenames(self, directory: str) -> None:
        for filename in os.listdir(directory):
            old_path = os.path.join(directory, filename)

            # Skip subdirectories
            if not os.path.isfile(old_path):
                continue

            new_filename = filename.lower()
            new_path = os.path.join(directory, new_filename)

            # Avoid unnecessary rename
            if old_path == new_path:
                continue

            os.rename(old_path, new_path)

    def lowercase_player_names(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            new_players = {}

            for player_name, player_data in players.items():
                lower_name = player_name.lower()

                # If a collision happens, keep the first one found
                if lower_name not in new_players:
                    new_players[lower_name] = player_data
                else:
                    # Optional: handle collisions explicitly if you want
                    pass

            team_data["players"] = new_players

    def calculate_team_most_killed_boss(self, players_dir) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})
            team_totals = team_data.setdefault("team_totals", {})

            boss_kill_totals = {}

            for player_name in players.keys():
                player_file = os.path.join(players_dir, f"{player_name}.json")

                if not os.path.exists(player_file):
                    continue

                player_data = load_json_data(player_file)
                bosses = player_data.get("data", {}).get("bosses", {})

                for boss_name, boss_info in bosses.items():
                    kills = boss_info.get("kills", {}).get("gained", 0)

                    if kills <= 0:
                        continue

                    boss_kill_totals[boss_name] = (
                        boss_kill_totals.get(boss_name, 0) + kills
                    )

            if not boss_kill_totals:
                continue

            most_killed_boss, total_kills = max(
                boss_kill_totals.items(),
                key=lambda item: item[1]
            )

            team_totals["most_killed_boss"] = {
                "boss": most_killed_boss,
                "kills": total_kills
            }

    def calculate_player_drops_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            for player_data in players.values():
                # Get total drops (integer)
                total_drops = player_data.get("total_drops", 0)

                # Get EHB
                ehb = player_data.get("wom", {}).get("ehb", 0)

                # Calculate drops per EHB
                if ehb > 0:
                    drops_per_ehb = total_drops / ehb
                else:
                    drops_per_ehb = 0.0

                # Store result (rounded for readability)
                player_data["drops_per_ehb"] = round(drops_per_ehb, 2)

    def calculate_team_best_drops_per_ehb(self) -> None:
        for team_data in self.data.values():
            players = team_data.get("players", {})

            best_player = None
            best_value = -1

            for player_name, player_data in players.items():
                value = player_data.get("drops_per_ehb")

                if value is None:
                    continue

                if value > best_value:
                    best_value = value
                    best_player = player_name

            if best_player is not None:
                team_data.setdefault("team_totals", {})
                # Format with commas
                formatted_value = f"{best_value:,.2f}"
                team_data["team_totals"]["best_drops_per_ehb"] = (
                    f"{best_player} ({formatted_value})"
                )

if __name__ == "__main__":
    gdoc_sheet_id = "1uQYTIZz6szfp4yyHkVPlPzCcEK042Kb-lFUx2gmCOlg"
    wom_comp_id = "100262"
    hunt_edition = "14"
    hunt_stats = HuntStats(hunt_edition=hunt_edition, gdoc_sheet_id=gdoc_sheet_id, wom_comp_id=wom_comp_id)
    hunt_stats.run()
