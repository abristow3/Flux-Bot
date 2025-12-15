from parsers.WOM.WOMDataParser import WOMDataParser
from parsers.WOM.WOMDataRetriever import WOMDataRetriever
from parsers.GDoc.GDocDataParser import GDocDataParser
from parsers.GDoc.GDocDataRetriever import GDocDataRetriever

class HuntStats:
    def __init__(self, hunt_edition: str, gdoc_sheet_id: str, wom_comp_id: str):
        self.hunt_edition: str = hunt_edition
        self.gdoc_sheet_id: str = gdoc_sheet_id
        self.wom_comp_id: str = wom_comp_id
    
    def run(self) -> None:
        # Fethc GDoc Data
        gdoc_data = GDocDataRetriever(sheet_id=self.gdoc_sheet_id)
        gdoc_parser = GDocDataParser(gdoc=gdoc_data, hunt_edition=self.hunt_edition)
        gdoc_parser.run()

        # Fetch WoM Data
        wom_data = WOMDataRetriever(comp_id=self.wom_comp_id, hunt_edition=self.hunt_edition)
        # uncomment to fetch data from API
        # wom_data.run()

        wom_parser = WOMDataParser(hunt_edition=self.hunt_edition)
        wom_parser.run()

if __name__ == "__main__":
    gdoc_sheet_id = "1uQYTIZz6szfp4yyHkVPlPzCcEK042Kb-lFUx2gmCOlg"
    wom_comp_id = "100262"
    hunt_edition = "14"
    hunt_stats = HuntStats(hunt_edition=hunt_edition, gdoc_sheet_id=gdoc_sheet_id, wom_comp_id=wom_comp_id)
    hunt_stats.run()
