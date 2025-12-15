from parsers.WOM.WOMDataParser import WOMDataParser
from parsers.WOM.WOMDataRetriever import WOMDataRetriever
from parsers.GDoc.GDocDataParser import GDocDataParser
from parsers.GDoc.GDocDataRetriever import GDocDataRetriever
import json
import os
from pathlib import Path

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
        gdoc_data = GDocDataRetriever(sheet_id=self.gdoc_sheet_id)
        gdoc_parser = GDocDataParser(gdoc=gdoc_data, hunt_edition=self.hunt_edition)
        gdoc_parser.run()

        # Fetch WoM Data
        wom_data = WOMDataRetriever(comp_id=self.wom_comp_id, hunt_edition=self.hunt_edition)
        # wom_data.run()  # Uncomment if fetching from API

        wom_parser = WOMDataParser(hunt_edition=self.hunt_edition)
        wom_parser.run()

        # Load JSON data
        self.load_json()
        # Calculate totals
        self.calculate_team_totals()
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

if __name__ == "__main__":
    gdoc_sheet_id = "1uQYTIZz6szfp4yyHkVPlPzCcEK042Kb-lFUx2gmCOlg"
    wom_comp_id = "100262"
    hunt_edition = "14"
    hunt_stats = HuntStats(hunt_edition=hunt_edition, gdoc_sheet_id=gdoc_sheet_id, wom_comp_id=wom_comp_id)
    hunt_stats.run()
