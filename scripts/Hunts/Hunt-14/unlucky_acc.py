import json

def load_player_data(filepath) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)  # JSON objects → dict
    return data


if __name__ == '__main__':
    filepaths = ["players/Jimmb0.json"]

    for path in filepaths:
        player_data: dict = load_player_data(path)

        # Get player name from filepath
        player_name = path.split("players/")[1].split(".")[0]

        # Initialize totals
        cox_total = 0
        toa_total = 0
        tob_total = 0
        doom_total = 0
        vard_total = 0
        leviathan_total = 0
        duke_total = 0
        whisper_total = 0

        # Sum kills for each relevant boss
        for boss_name, boss_info in player_data['data']['bosses'].items():
            kills = boss_info.get('kills', {}).get('gained', 0)

            if boss_name == 'chambers_of_xeric':
                cox_total += kills
            elif boss_name == 'theatre_of_blood':
                tob_total += kills
            elif boss_name == 'tombs_of_amascut':
                toa_total += kills
            elif boss_name == 'doom_of_mokhaiotl':
                doom_total += kills
            elif boss_name == 'vardorvis':
                vard_total += kills
            elif boss_name == 'leviathan':
                leviathan_total += kills
            elif boss_name == 'duke_sucellus':
                duke_total += kills
            elif boss_name == 'whisperer':
                whisper_total += kills

        total_raids = cox_total + toa_total + tob_total
        print(f"====== {player_name} ======")
        print(f"COX: {cox_total}\nTOB: {tob_total}\nTOA: {toa_total}\nTOTAL RAIDS: {total_raids}")
        print(f"DOOM: {doom_total}\nVARD: {vard_total}\nLEVIATHAN: {leviathan_total}\nDUKE: {duke_total}\nWHISPER: {whisper_total}")
