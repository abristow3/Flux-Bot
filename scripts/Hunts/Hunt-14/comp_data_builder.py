import json

def load_event_data(filepath) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)  # JSON objects → dict
    return data
class HuntData:
    def __init__(self):
        self.competition_data = load_event_data("competition.json")
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
        self.player_most_bosses_killed = {} # player name and total
        self.player_most_raids_completed = {} # player name and total
        self.player_most_cox_completed = {}  # player name and total
        self.player_most_tob_completed = {}  # player name and total
        self.player_most_toa_completed = {}  # player name and total
        self.most_clues_completed = {} # player name and total

    def calculate_total_event_ehb(self) -> None:
        participants: list = self.competition_data['participations']
        for player in participants:
            self.total_hunt_ehb += player['progress']['gained']

        print(f"Total Hunt 14 EHB: {self.total_hunt_ehb}")


if __name__ == "__main__":
    details = HuntData()
    details.calculate_total_event_ehb()

