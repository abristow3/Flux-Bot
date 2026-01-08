from src.services.bingo.BingoConfigParser import BingoConfigParser
from src.services.GDoc.GDoc import GDoc
from typing import Optional
import logging


'''
DESIGN OVERVIEW:

in the bingo commands, when setup is run, at the end we want it to start the bingo cog

MAYBE MOVE ALL thiS LOGIC INTO THE BINGOCOG and HAVE JUST 1 SUPERCLASS

Create the object
Set the sheet id via Bingo.config_parser.set_sheet_id
load the config
load the participants

'''
logger = logging.getLogger(__name__)

class Bingo:
    def __init__(self):
        self.sheet_name = "Bot Config"
        self.config_parser = BingoConfigParser(sheet_name=self.sheet_name)
        self.gdoc = GDoc()
        self.sheet_id = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
        self.bingo_discord_category_id = 1063433446321565796
        
    def startup(self) -> None:
        self.gdoc.set_sheet_id(self.sheet_id)
        sheet_data = self.gdoc.get_data_from_sheet(self.config_parser.sheet_name)

        self.config_parser.set_sheet_data(sheet_data)
        self.config_parser.config_table_data = self.config_parser.pull_table_data(self.config_parser.config_table_name)
        self.config_parser.build_table_map()

        # Load configuration table
        self.config_parser.load_config_table(self.config_parser.config_table_data)
        logger.info("Bingo configuration loaded successfully!\n")
        
        # Load participants table
        self.config_parser.participants_table_data = self.config_parser.pull_table_data(self.config_parser.participants_table_name)
        self.config_parser.load_participants_table(self.config_parser.participants_table_data)
        logger.info("Participants data loaded successfully!\n")
        print(self.config_parser.participants_dict)
        print(f"TEAM NAMES: {self.config_parser.team_names}\n")
        print(f"TCS: {self.config_parser.text_channels}\n")
        print(f"VCS: {self.config_parser.voice_channels}\n")
        print(f"ROLES: {self.config_parser.roles}\n")