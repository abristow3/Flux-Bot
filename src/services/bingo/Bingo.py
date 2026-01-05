from src.services.bingo.BingoConfigParser import BingoConfigParser
from typing import Optional


'''
Create the object
Set the sheet idea via Bingo.config_parser.set_sheet_id
load the config



'''
class Bingo:
    def __init__(self):
        self.config_parser: Optional[BingoConfigParser] = None
