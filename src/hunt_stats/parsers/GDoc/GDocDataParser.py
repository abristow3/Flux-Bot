import json
import pandas as pd
from parsers.GDoc.GDocDataRetriever import GDocDataRetriever
import os

class GDocDataParser:
    def __init__(self, gdoc: GDocDataRetriever, hunt_edition: str, sheet_name: str = "Inputs"):
        self.gdoc = gdoc
        self.sheet_name = sheet_name
        self.hunt_edition = hunt_edition

        # Output directory and file
        self.base_dir = os.path.join("src", "hunt-stats", "data", f"Hunt-{self.hunt_edition}")
        os.makedirs(self.base_dir, exist_ok=True)
        self.output_file = os.path.join(self.base_dir, "hunt_metrics.json")

        # Canonical data store
        self.team_players = {
            "Team Red": {
                "players": {},
                "team_totals": {
                    "total_drops": 0,
                    "total_points": 0.0,  # Leave as 0 for now
                    "total_coins": 0.0
                }
            },
            "Team Gold": {
                "players": {},
                "team_totals": {
                    "total_drops": 0,
                    "total_points": 0.0,  # Leave as 0 for now
                    "total_coins": 0.0
                }
            }
        }

    def run(self):
        """Main method to fetch, parse, and write metrics."""
        df_red, df_gold = self.get_team_dataframes(self.sheet_name)

        df_red_clean = self.clean_team_dataframe(df_red)
        df_gold_clean = self.clean_team_dataframe(df_gold)

        self.ingest_team_dataframe(df_red_clean, "Team Red")
        self.ingest_team_dataframe(df_gold_clean, "Team Gold")

        self.write_metrics_to_file(self.output_file)
        print("GDOC PARSING COMPLETED")

    # ---------------------------------------------------------
    # Sheet parsing
    # ---------------------------------------------------------
    def get_team_dataframes(self, sheet_name: str):
        raw_data = self.gdoc.get_data_from_sheet(sheet_name)
        if raw_data is None or raw_data.shape[0] < 3:
            return pd.DataFrame(), pd.DataFrame()

        rows = raw_data.tolist()[2:]  # skip team label + header

        # Team Red (A-F → keep A,B,C,E,F)
        red_rows = []
        for r in rows:
            r += [""] * (6 - len(r))
            red_rows.append([r[0], r[1], r[2], r[4], r[5]])
        df_red = pd.DataFrame(red_rows, columns=["Content", "Item", "Player", "Coins", "Points"])

        # Team Gold (J-O → keep J,K,L,N,O)
        gold_rows = []
        for r in rows:
            r += [""] * (15 - len(r))
            gold_rows.append([r[9], r[10], r[11], r[13], r[14]])
        df_gold = pd.DataFrame(gold_rows, columns=["Content", "Item", "Player", "Coins", "Points"])

        return df_red, df_gold

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _ensure_player(self, team_name: str, player: str):
        players = self.team_players[team_name]["players"]
        if player not in players:
            players[player] = {
                "total_drops": 0,
                "total_points": 0.0,
                "total_coins": 0.0,
                "boss_pets": 0,
                "jars": 0,
                "mega_rares": 0,
                "most_expensive_drop": {"item": None, "value": 0.0},
                "most_points_item": {"item": None, "points": 0.0}
            }

    # ---------------------------------------------------------
    # Core ingestion logic
    # ---------------------------------------------------------
    def ingest_team_dataframe(self, df_team: pd.DataFrame, team_name: str):
        if df_team.empty:
            return

        df = df_team.copy()
        for col in ["Player", "Item", "Coins", "Points"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "").str.strip()

        df["Coins"] = pd.to_numeric(df.get("Coins", 0), errors="coerce").fillna(0)
        df["Points"] = pd.to_numeric(df.get("Points", 0), errors="coerce").fillna(0)

        df_valid = df[(df["Player"] != "") & (df["Item"] != "")]

        mega_rares = [
            "scythe of vitur", "twisted bow", "elder maul",
            "kodai insignia", "tumeken's shadow"
        ]

        for _, row in df_valid.iterrows():
            player = row["Player"]
            item = row["Item"]
            coins = float(row["Coins"])
            points = float(row["Points"])

            self._ensure_player(team_name, player)
            pdata = self.team_players[team_name]["players"][player]
            totals = self.team_players[team_name]["team_totals"]

            # Drops (exclude bounty/challenge)
            if not any(x in item.lower() for x in ["bounty daily", "challenge"]):
                pdata["total_drops"] += 1
                totals["total_drops"] += 1

            pdata["total_points"] += points
            pdata["total_coins"] += coins
            totals["total_coins"] += coins

            if points > pdata["most_points_item"]["points"]:
                pdata["most_points_item"] = {"item": item, "points": points}

            if "pet" in item.lower():
                pdata["boss_pets"] += 1

            if item.lower() == "jar":
                pdata["jars"] += 1

            if any(mr in item.lower() for mr in mega_rares):
                pdata["mega_rares"] += 1

            if coins > pdata["most_expensive_drop"]["value"]:
                pdata["most_expensive_drop"] = {"item": item, "value": coins}

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------
    def write_metrics_to_file(self, path: str):
        output = {}
        for team, data in self.team_players.items():
            output[team] = {
                "team_totals": {
                    "total_drops": data["team_totals"]["total_drops"],
                    "total_points": f'{data["team_totals"]["total_points"]:,.1f}',  # still 0 for now
                    "total_coins": f'{data["team_totals"]["total_coins"]:,.0f}'
                },
                "players": {}
            }

            for player, pdata in data["players"].items():
                output[team]["players"][player] = {
                    "total_drops": pdata["total_drops"],
                    "total_points": f'{pdata["total_points"]:,.1f}',
                    "total_coins": f'{pdata["total_coins"]:,.0f}',
                    "boss_pets": pdata["boss_pets"],
                    "jars": pdata["jars"],
                    "mega_rares": pdata["mega_rares"],
                    "most_expensive_drop": {
                        "item": pdata["most_expensive_drop"]["item"],
                        "value": f'{pdata["most_expensive_drop"]["value"]:,.0f}'
                    },
                    "most_points_item": {
                        "item": pdata["most_points_item"]["item"],
                        "points": f'{pdata["most_points_item"]["points"]:,.1f}'
                    }
                }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

    # ---------------------------------------------------------
    # Data cleaning
    # ---------------------------------------------------------
    def clean_team_dataframe(self, df_team: pd.DataFrame) -> pd.DataFrame:
        """Normalize and clean a team dataframe."""
        if df_team is None or df_team.empty:
            return pd.DataFrame()

        df = df_team.copy()

        # Normalize string columns
        for col in ["Content", "Item", "Player"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Normalize Coins
        if "Coins" in df.columns:
            df["Coins"] = (
                df["Coins"]
                .fillna(0)
                .astype(str)
                .str.replace(",", "")
                .str.strip()
                .replace(["", "NULL", "None"], "0")
            )
            df["Coins"] = pd.to_numeric(df["Coins"], errors="coerce").fillna(0).astype(int)
        else:
            df["Coins"] = 0

        # Normalize Points
        if "Points" in df.columns:
            df["Points"] = (
                df["Points"]
                .fillna(0)
                .astype(str)
                .str.replace(",", "")
                .str.strip()
                .replace(["", "NULL", "None"], "0")
            )
            df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0).astype(float)
        else:
            df["Points"] = 0.0

        # Drop rows where all columns except 'Points' are empty/NaN
        cols_except_points = [col for col in df.columns if col != "Points"]
        df = df.loc[~df[cols_except_points].apply(lambda x: all([v in [None, "", "nan"] for v in x]), axis=1)]

        return df
