import json
import os


def load_json_data(filepath) -> dict:
    with open(filepath, 'r') as f:
        data = json.load(f)  # JSON objects → dict
    return data


class HuntData:
    def __init__(self):
        self.competition_data = load_json_data("competition.json")
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
        self.most_clues_completed = {}  # player name and total

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
        for file in os.listdir("players"):
            player_data: dict = load_json_data(f"players/{file}")

            for boss_name, boss_info in player_data['data']['bosses'].items():
                self.total_bosses_killed += boss_info.get('kills', {}).get('gained', 0)

        print(f"Total Boss Kills: {self.total_bosses_killed:,}")

    def calculate_total_raids_killed(self) -> None:
        for file in os.listdir("players"):
            player_data: dict = load_json_data(f"players/{file}")

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
        for file in os.listdir("players"):
            player_data: dict = load_json_data(f"players/{file}")

            for boss_name, boss_info in player_data['data']['bosses'].items():
                kills = boss_info.get('kills', {}).get('gained', 0)

                if 'barrows_chests' in boss_name:
                    self.total_barrows_looted += kills

        print(f"Total Barrows Chests Looted: {self.total_barrows_looted:,}")

    def calculate_total_clues_completed(self) -> None:
        for file in os.listdir("players"):
            player_data: dict = load_json_data(f"players/{file}")

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
        for file in os.listdir("players"):
            player_data: dict = load_json_data(f"players/{file}")
            self.total_xp_gained += player_data['data']['skills']['overall']['experience']['gained']

        print(f"Total Experience Gained: {self.total_xp_gained:,}")

if __name__ == "__main__":
    details = HuntData()
    details.calculate_total_event_ehb()
    details.calculate_total_participants()
    details.calculate_most_ehb()
    details.calculate_total_bosses_killed()
    details.calculate_total_raids_killed()
    details.calculate_total_barrows_killed()
    details.calculate_total_clues_completed()
    details.calculate_total_xp()
