from src.services.bingo.BingoConfigParser import BingoConfigParser
from src.services.GDoc.GDoc import GDoc
from typing import Optional
import logging

from discord.ext import tasks, commands

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

class BingoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheet_name = "Bot Config"
        self.config_parser = BingoConfigParser(sheet_name=self.sheet_name)
        self.gdoc = GDoc()
        self.sheet_id = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
        self.bingo_discord_category_id = 1063433446321565796

    def load_config(self) -> None:
        """Load all configuration and participant data."""
        try:
            self.gdoc.set_sheet_id(self.sheet_id)
            sheet_data = self.gdoc.get_data_from_sheet(self.config_parser.sheet_name)

            self.config_parser.set_sheet_data(sheet_data)
            self.config_parser.config_table_data = self.config_parser.pull_table_data(self.config_parser.config_table_name)
            self.config_parser.build_table_map()

            # Load configuration table
            self.config_parser.load_config_table(self.config_parser.config_table_data)
            logger.info("Bingo configuration loaded successfully!")

            # Load participants table
            self.config_parser.participants_table_data = self.config_parser.pull_table_data(self.config_parser.participants_table_name)
            self.config_parser.load_participants_table(self.config_parser.participants_table_data)
            logger.info("Participants data loaded successfully!")
        except Exception as e:
            logger.error(f"[Bingo Cog] Error when loading bingo configuration and participant data.", exc_info=e)

    async def cog_load(self) -> None:
        """Runs when the cog is loaded and bot is ready."""
        logger.info("[Score Cog] Loading Score Cog.")

        try:
            self.get_bingo_channel()
            self.configured = True
        except Exception as e:
            logger.error(f"[Score Cog] Failed configuration: {e}")
            return

    async def cog_unload(self) -> None:
        """Cleans up background tasks on cog unload."""
        logger.info("[Score Cog] Unloading Score Cog.")
        if self.start_scores.is_running():
            self.start_scores.stop()
        if self.watch_scores.is_running():
            self.watch_scores.stop()
    
    @tasks.loop(seconds=10)
    async def start_bingo(self) -> None:
        if not self.configured:
            logger.warning("[Score Cog] Cog not properly configured. Skipping score update.")
            return

        try:
            channel = self.discord_bot.get_channel(self.score_channel_id)
            if not channel:
                logger.warning("Score channel not found.")
                return
        except Exception as e:
            ...