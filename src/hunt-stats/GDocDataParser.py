import json
import pandas as pd
from GDoc import GDoc


class GDocDataParser:
    def __init__(self, gdoc: GDoc):
        self.gdoc = gdoc

        # Canonical data store
        self.team_players = {
            "Team Red": {
                "players": {},
                "team_totals": {
                    "total_drops": 0,
                    "total_points": 0.0,
                    "total_coins": 0.0
                }
            },
            "Team Gold": {
                "players": {},
                "team_totals": {
                    "total_drops": 0,
                    "total_points": 0.0,
                    "total_coins": 0.0
                }
            }
        }

    # ---------------------------------------------------------
    # Sheet parsing
    # ---------------------------------------------------------
    def get_team_dataframes(self, sheet_name: str):
        """Fetch Team Red (A-F) and Team Gold (J-O) as DataFrames."""
        raw_data = self.gdoc.get_data_from_sheet(sheet_name)

        if raw_data is None or raw_data.shape[0] < 3:
            return pd.DataFrame(), pd.DataFrame()

        rows = raw_data.tolist()[2:]  # skip team label + header

        # Team Red (A-F → keep A,B,C,E,F)
        red_rows = []
        for r in rows:
            r += [""] * (6 - len(r))
            red_rows.append([r[0], r[1], r[2], r[4], r[5]])

        df_red = pd.DataFrame(
            red_rows,
            columns=["Content", "Item", "Player", "Coins", "Points"]
        )

        # Team Gold (J-O → keep J,K,L,N,O)
        gold_rows = []
        for r in rows:
            r += [""] * (15 - len(r))
            gold_rows.append([r[9], r[10], r[11], r[13], r[14]])

        df_gold = pd.DataFrame(
            gold_rows,
            columns=["Content", "Item", "Player", "Coins", "Points"]
        )

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
                "most_expensive_drop": {
                    "item": None,
                    "value": 0.0
                },
                "most_points_item": {
                    "item": None,
                    "points": 0.0
                }
            }


    # ---------------------------------------------------------
    # Core ingestion logic (single pass per team)
    # ---------------------------------------------------------
    def ingest_team_dataframe(self, df_team: pd.DataFrame, team_name: str):
        if df_team.empty:
            return

        df = df_team.copy()

        # Clean columns
        for col in ["Player", "Item", "Coins", "Points"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "").str.strip()

        df["Coins"] = pd.to_numeric(df.get("Coins", 0), errors="coerce").fillna(0)
        df["Points"] = pd.to_numeric(df.get("Points", 0), errors="coerce").fillna(0)

        df_valid = df[(df["Player"] != "") & (df["Item"] != "")]

        mega_rares = [
            "scythe of vitur",
            "twisted bow",
            "elder maul",
            "kodai insignia",
            "tumeken's shadow"
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

            # Points & Coins
            pdata["total_points"] += points
            pdata["total_coins"] += coins
            totals["total_points"] += points
            totals["total_coins"] += coins

            # Most points item
            if points > pdata["most_points_item"]["points"]:
                pdata["most_points_item"] = {
                    "item": item,
                    "points": points
                }

            # Boss pets
            if "pet" in item.lower():
                pdata["boss_pets"] += 1

            # Jars
            if item.lower() == "jar":
                pdata["jars"] += 1

            # Mega-rares
            if any(mr in item.lower() for mr in mega_rares):
                pdata["mega_rares"] += 1

            # Most expensive drop
            if coins > pdata["most_expensive_drop"]["value"]:
                pdata["most_expensive_drop"] = {
                    "item": item,
                    "value": coins
                }

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------
    def write_metrics_to_file(self, path: str):
        output = {}

        for team, data in self.team_players.items():
            output[team] = {
                "team_totals": {
                    "total_drops": data["team_totals"]["total_drops"],
                    "total_points": f'{data["team_totals"]["total_points"]:,.1f}',
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

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    SHEET_ID = "1uQYTIZz6szfp4yyHkVPlPzCcEK042Kb-lFUx2gmCOlg"
    SHEET_NAME = "Inputs"
    OUTPUT_FILE = "hunt_metrics.json"

    # Initialize GDoc
    gdoc = GDoc()
    gdoc.set_sheet_id(SHEET_ID)

    # Initialize parser
    parser = GDocDataParser(gdoc)

    # Fetch team data
    df_team_red, df_team_gold = parser.get_team_dataframes(SHEET_NAME)

    print("=== Top 5 Rows: Team Red ===")
    print(df_team_red.head(), "\n")

    print("=== Top 5 Rows: Team Gold ===")
    print(df_team_gold.head(), "\n")

    # Ingest metrics
    parser.ingest_team_dataframe(df_team_red, "Team Red")
    parser.ingest_team_dataframe(df_team_gold, "Team Gold")

    # Write metrics to file
    parser.write_metrics_to_file(OUTPUT_FILE)

    # -----------------------------
    # Sanity-check output
    # -----------------------------
    for team, data in parser.team_players.items():
        print(f"\n=== {team} Summary ===")

        totals = data["team_totals"]
        players = data["players"]

        print(f"Total Drops : {totals['total_drops']}")
        print(f"Total Points: {totals['total_points']:,.1f}")
        print(f"Total Coins : {totals['total_coins']:,.0f}")

        if not players:
            print("No player data.")
            continue

        # ---- Top by drops ----
        top_drops = max(players.items(), key=lambda x: x[1]["total_drops"])
        print(
            f"Top Drops Player: {top_drops[0]} "
            f"({top_drops[1]['total_drops']} drops)"
        )

        # ---- Top by points ----
        top_points = max(players.items(), key=lambda x: x[1]["total_points"])
        mpi = top_points[1]["most_points_item"]
        print(
            f"Top Points Player: {top_points[0]} "
            f"({top_points[1]['total_points']:,.1f} pts)"
        )
        if mpi["item"]:
            print(
                f"  ↳ Highest Points Item: {mpi['item']} "
                f"({mpi['points']:,.1f} pts)"
            )

        # ---- Top by coins ----
        top_coins = max(players.items(), key=lambda x: x[1]["total_coins"])
        print(
            f"Top Coins Player: {top_coins[0]} "
            f"({top_coins[1]['total_coins']:,.0f} coins)"
        )

        # ---- Most expensive single drop ----
        expensive = max(
            players.items(),
            key=lambda x: x[1]["most_expensive_drop"]["value"]
        )
        ed = expensive[1]["most_expensive_drop"]
        if ed["item"]:
            print(
                f"Most Expensive Drop: {expensive[0]} "
                f"({ed['item']} @ {ed['value']:,.0f})"
            )

        # ---- Boss pets ----
        top_pets = max(players.items(), key=lambda x: x[1]["boss_pets"])
        if top_pets[1]["boss_pets"] > 0:
            print(
                f"Most Boss Pets: {top_pets[0]} "
                f"({top_pets[1]['boss_pets']})"
            )

        # ---- Jars ----
        top_jars = max(players.items(), key=lambda x: x[1]["jars"])
        if top_jars[1]["jars"] > 0:
            print(
                f"Most Jars: {top_jars[0]} "
                f"({top_jars[1]['jars']})"
            )

        # ---- Mega-rares ----
        top_mega = max(players.items(), key=lambda x: x[1]["mega_rares"])
        if top_mega[1]["mega_rares"] > 0:
            print(
                f"Most Mega-Rares: {top_mega[0]} "
                f"({top_mega[1]['mega_rares']})"
            )


    print(f"\nMetrics written to: {OUTPUT_FILE}")
