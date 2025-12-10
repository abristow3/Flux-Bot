import json
import os


def load_json_data(filepath) -> dict:
    with open(filepath, 'r') as f:
        data = json.load(f)  # JSON objects → dict
    return data


class WOMDataParser:
    def __init__(self):
        self.competition_data = load_json_data("../data/Hunt-14/competition.json")
        self.total_hunt_ehb = 0.0
        self.total_participants = 0
        self.most_ehb = 0.0
        self.total_bosses_killed = 0
        self.total_raids_completed = 0
        self.total_cox_completed = 0
        self.total_tob_completed = 0
        self.total_toa_completed = 0
        self.total_barrows_looted = 0
        self.total_clues_completed = 0
        self.total_beginner_clues = 0
        self.total_easy_clues = 0
        self.total_medium_clues = 0
        self.total_hard_clues = 0
        self.total_elite_clues = 0
        self.total_master_clues = 0
        self.total_xp_gained = 0
        self.player_most_bosses_killed = {}  # player name and total
        self.player_most_raids_completed = {}  # player name and total
        self.player_most_cox_completed = {}  # player name and total
        self.player_most_tob_completed = {}  # player name and total
        self.player_most_toa_completed = {}  # player name and total
        self.player_most_barrows_completed = {"Name": "", "Total": 0}
        self.player_most_clues_completed = {}  # player name and total
        self.player_most_xp_gained = {"Name": "", "Total": 0}

    def calculate_total_event_ehb(self) -> None:
        participants: list = self.competition_data['participations']
        for player in participants:
            self.total_hunt_ehb += player['progress']['gained']

        print(f"Total EHB: {self.total_hunt_ehb:,}")

    def calculate_total_participants(self) -> None:
        self.total_participants = self.competition_data["participantCount"]
        print(f"Total Participants: {self.total_participants}")

    def calculate_most_ehb(self) -> None:
        most_ehb: float = 0.0
        player_name = ""
        participants: list = self.competition_data['participations']

        for player in participants:
            ehb = player['progress']['gained']

            if ehb > most_ehb:
                player_name = player['player']['displayName']
                most_ehb = ehb

        print(f"Most EHB: {player_name} - {most_ehb} EHB")

    def calculate_total_bosses_killed(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")

            for boss_name, boss_info in player_data['data']['bosses'].items():
                self.total_bosses_killed += boss_info.get('kills', {}).get('gained', 0)

        print(f"Total Boss Kills: {self.total_bosses_killed:,}")

    def calculate_total_raids_killed(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")

            for boss_name, boss_info in player_data['data']['bosses'].items():
                kills = boss_info.get('kills', {}).get('gained', 0)

                if 'chambers_of_xeric' in boss_name:
                    self.total_cox_completed += kills
                    self.total_raids_completed += kills
                elif 'theatre_of_blood' in boss_name:
                    self.total_tob_completed += kills
                    self.total_raids_completed += kills
                elif 'tombs_of_amascut' in boss_name:
                    self.total_toa_completed += kills
                    self.total_raids_completed += kills

        print(f"Total Raids Completed: {self.total_raids_completed:,}")
        print(f"Total CoX Completed: {self.total_cox_completed:,}")
        print(f"Total ToB Completed: {self.total_tob_completed:,}")
        print(f"Total ToA Completed: {self.total_toa_completed:,}")

    def calculate_total_barrows_killed(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")

            for boss_name, boss_info in player_data['data']['bosses'].items():
                kills = boss_info.get('kills', {}).get('gained', 0)

                if 'barrows_chests' in boss_name:
                    self.total_barrows_looted += kills

        print(f"Total Barrows Chests Looted: {self.total_barrows_looted:,}")

    def calculate_total_clues_completed(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")

            for activity_name, activity_info in player_data['data']['activities'].items():
                clues_completed = activity_info.get('score', {}).get('gained', 0)

                if 'clue_scrolls_all' in activity_name:
                    self.total_clues_completed += clues_completed
                elif 'clue_scrolls_beginner' in activity_name:
                    self.total_beginner_clues += clues_completed
                elif 'clue_scrolls_easy' in activity_name:
                    self.total_easy_clues += clues_completed
                elif 'clue_scrolls_medium' in activity_name:
                    self.total_medium_clues += clues_completed
                elif 'clue_scrolls_hard' in activity_name:
                    self.total_hard_clues += clues_completed
                elif 'clue_scrolls_elite' in activity_name:
                    self.total_elite_clues += clues_completed
                elif 'clue_scrolls_master' in activity_name:
                    self.total_master_clues += clues_completed

        print(f"Total Clue Scrolls Completed: {self.total_clues_completed}")
        print(f"Total Beginner Clue Scrolls Completed: {self.total_beginner_clues}")
        print(f"Total Easy Clue Scrolls Completed: {self.total_easy_clues}")
        print(f"Total Medium Clue Scrolls Completed: {self.total_medium_clues}")
        print(f"Total Hard Clue Scrolls Completed: {self.total_hard_clues}")
        print(f"Total Elite Clue Scrolls Completed: {self.total_elite_clues}")
        print(f"Total Master Clue Scrolls Completed: {self.total_master_clues}")

    def calculate_total_xp(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            self.total_xp_gained += player_data['data']['skills']['overall']['experience']['gained']

        print(f"Total Experience Gained: {self.total_xp_gained:,}")

    def calculate_player_most_total_kills(self) -> None:
        most_kills_total = 0
        most_kills_name = ""
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            total_kills = 0
            player_name = file.split(".")[0]

            for boss_name, boss_info in player_data['data']['bosses'].items():
                total_kills += boss_info.get('kills', {}).get('gained', 0)

            if total_kills > most_kills_total:
                most_kills_total = total_kills
                most_kills_name = player_name

        self.player_most_bosses_killed = {most_kills_name: most_kills_total}
        print(f"Most Bosses Killed: {most_kills_name} - {most_kills_total:,}")

    def calculate_player_most_raids_completed(self) -> None:
        most_kills_total = 0
        most_kills_name = ""
        most_cox_kills_total = 0
        most_cox_kills_name = ""
        most_tob_kills_total = 0
        most_tob_kills_name = ""
        most_toa_kills_total = 0
        most_toa_kills_name = ""

        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            player_name = file.split(".")[0]
            raid_total = 0

            for boss_name, boss_info in player_data['data']['bosses'].items():
                kills = boss_info.get('kills', {}).get('gained', 0)

                if 'chambers_of_xeric' in boss_name:
                    if kills > most_cox_kills_total:
                        most_cox_kills_total = kills
                        raid_total += kills
                        most_cox_kills_name = player_name
                elif 'theatre_of_blood' in boss_name:
                    if kills > most_tob_kills_total:
                        most_tob_kills_total = kills
                        raid_total += kills
                        most_tob_kills_name = player_name
                elif 'tombs_of_amascut' in boss_name:
                    if kills > most_toa_kills_total:
                        most_toa_kills_total = kills
                        raid_total += kills
                        most_toa_kills_name = player_name

            if raid_total > most_kills_total:
                most_kills_total = raid_total
                most_kills_name = player_name

        print(f"Most Raids Completed: {most_kills_name} - {most_kills_total:,}")
        print(f"Most CoX Completed: {most_cox_kills_name} - {most_cox_kills_total:,}")
        print(f"Most ToB Completed: {most_tob_kills_name} - {most_tob_kills_total:,}")
        print(f"Most ToA Completed: {most_toa_kills_name} - {most_toa_kills_total:,}")

    def calculate_player_most_clues(self) -> None:
        most_clues_total = 0
        most_clues_name = ""
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            player_name = file.split(".")[0]

            for activity_name, activity_info in player_data['data']['activities'].items():
                clues_completed = activity_info.get('score', {}).get('gained', 0)

                if 'clue_scrolls_all' in activity_name:
                    if clues_completed > most_clues_total:
                        most_clues_name = player_name
                        most_clues_total = clues_completed

        print(f"Most Clue Scrolls Completed: {most_clues_name} - {most_clues_total:,}")

    def calculate_player_most_xp_gained(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            player_name = file.split(".")[0]
            xp_gained = player_data['data']['skills']['overall']['experience']['gained']

            if xp_gained > self.player_most_xp_gained['Total']:
                self.player_most_xp_gained['Name'] = player_name
                self.player_most_xp_gained['Total'] = xp_gained

        print(f"Most Experience Gained: {self.player_most_xp_gained['Name']} - {self.player_most_xp_gained['Total']:,}")

    def calculate_player_most_barrows(self) -> None:
        for file in os.listdir("../data/Hunt-14/players"):
            player_data: dict = load_json_data(f"../data/Hunt-14/players/{file}")
            player_name = file.split(".")[0]

            for boss_name, boss_info in player_data['data']['bosses'].items():
                kills = boss_info.get('kills', {}).get('gained', 0)

                if 'barrows_chests' in boss_name:
                    if kills > self.player_most_barrows_completed['Total']:
                        self.player_most_barrows_completed['Total'] = kills
                        self.player_most_barrows_completed['Name'] = player_name

        print(f"Most Barrows Chests Looted: {self.player_most_barrows_completed['Name']} - "
              f"{self.player_most_barrows_completed['Total']:,}")


if __name__ == "__main__":
    details = WOMDataParser()
    details.calculate_total_event_ehb()
    details.calculate_total_participants()
    details.calculate_most_ehb()
    details.calculate_total_bosses_killed()
    details.calculate_total_raids_killed()
    details.calculate_total_barrows_killed()
    details.calculate_total_clues_completed()
    details.calculate_total_xp()
    details.calculate_player_most_total_kills()
    details.calculate_player_most_raids_completed()
    details.calculate_player_most_clues()
    details.calculate_player_most_xp_gained()
    details.calculate_player_most_barrows()
