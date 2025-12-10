'''
Total GP
Total Drops
total pets
total jars
total mega-rares

Most Expensive Drop
Team 1 Score / Name / points
Team 2 Score / Name / points
most points from gdoc

Player with most drops
Player earned most GP
Player most points per EHB
player most GP per EHB
players most drops per EHB
player most pets
player most jars

===== from both data sources ====
avg gp per boss kill
player with most gp per boss kill
player with least gp per boss kill

'''


class GDocDataParser:
    def __init__(self, sheet_id: str) -> None:
        self.sheet_id: str = sheet_id
        self.gdoc_data = None

    def retrieve_hunt_sheet_data(self) -> None:
        ...
