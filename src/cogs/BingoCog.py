from src.services.bingo.BingoConfigParser import BingoConfigParser
from src.services.GDoc.GDoc import GDoc
from typing import Optional
import logging
from datetime import datetime, timedelta, timezone
from discord.ext import tasks, commands
from src.main import BotClient

logger = logging.getLogger(__name__)

class BingoCog(commands.Cog):
    def __init__(self, bot: BotClient):
        self.bot = bot
        self.sheet_name = "Bot Config"
        self.config_parser = BingoConfigParser(sheet_name=self.sheet_name)
        self.gdoc = GDoc()
        self.sheet_id = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
        self.events_channel_id = ""
        self.configured = False

        # Announcements variables
        self.signup_reminder_sent = False
        self.start_reminder_sent = False
        self.start_sent = False
        self.end_reminder_sent = False
        self.end_sent = False

        self.signup_datetime = None
        self.start_reminder_datetime = None
        self.start_datetime = None
        self.end_reminder_datetime = None
        self.end_datetime = None

    def _load_config(self) -> None:
        """Load all configuration and participant data."""
        try:
            # Set, retrieve, and parse GDoc sheet
            self.gdoc.set_sheet_id(self.sheet_id)
            sheet_data = self.gdoc.get_data_from_sheet(self.config_parser.sheet_name)
            self.config_parser.set_sheet_data(sheet_data)
            self.config_parser.config_table_data = self.config_parser.pull_table_data(self.config_parser.config_table_name)
            self.config_parser.build_table_map()

            # Load configuration table
            self.config_parser.load_config_table(self.config_parser.config_table_data)
            self.configured = True
            logger.info("Bingo configuration loaded successfully!")

        except Exception as e:
            logger.error(f"[Bingo Cog] Error when loading bingo configuration and participant data.", exc_info=e)

    async def cog_load(self) -> None:
        try:
            self._load_config()
            self._get_events_channel_id()
            self._create_announcement_datetimes()
            self.start_bingo.start()
        except Exception as e:
            logger.error(f"[Bingo Cog] Failed to load Bingo Cog: {e}")
            return

    async def cog_unload(self) -> None:
        if self.start_bingo.is_running():
            self.start_bingo.stop()

    def _get_events_channel_id(self) -> None:
        self.events_channel_id = int(self.config_parser.config_dict('EVENTS_CHANNEL_ID', "0"))
        if self.events_channel_id == 0:
            logger.error("[Bingo Cog] EVENTS_CHANNEL_ID not found")
            raise KeyError
        
    def now_gmt(self) -> datetime:
        """Return the current datetime in GMT/UTC (timezone-aware)."""
        return datetime.now(timezone.utc)
    
    def parse_datetime(self, date_str: str, time_str: str) -> datetime | None:
        if not date_str or not time_str:
            return None

        # Combine date and time into one string
        dt_str = f"{date_str} {time_str}"

        # Parse into datetime (DD/MM/YYYY HH:MM)
        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")

        # Make timezone-aware (GMT / UTC)
        return dt.replace(tzinfo=timezone.utc)

    def _create_announcement_datetimes(self) -> None:
        signup_end_date = self.config_parser.config_dict("SIGNUP_END_DATE", "")
        signup_end_time_gmt = self.config_parser.config_dict("SIGNUP_END_TIME_GMT", "")
   
        start_date = self.config_parser.config_dict("BINGO_START_DATE", "")
        start_time_gmt = self.config_parser.config_dict("BINGO_START_TIME_GMT", "")

        end_date = self.config_parser.config_dict("BINGO_END_DATE", "")
        end_time_gmt = self.config_parser.config_dict("BINGO_END_TIME_GMT", "")

        signup_datetime = self.parse_datetime(signup_end_date, signup_end_time_gmt)
        self.signup_datetime = signup_datetime - timedelta(hours=24)

        self.start_datetime = self.parse_datetime(start_date, start_time_gmt)
        self.start_reminder_datetime = self.start_datetime - timedelta(hours=24)
        
        self.end_datetime = self.parse_datetime(end_date, end_time_gmt)
        self.end_reminder_datetime = self.end_datetime - timedelta(hours=24)

    async def _send_message(self, config_key: str) -> None:
        message = self.config_parser.config_dict.get(config_key, "")
        if not message:
            logger.error(f"[Bingo Cog] Missing message for {config_key}")
            return

        channel = self.bot.get_channel(self.events_channel_id) or \
                await self.bot.fetch_channel(self.events_channel_id)

        await channel.send(message)

    async def _send_signup_reminder_24hr(self) -> None:
        await self._send_message("REMINDER_SIGNUP_24HR")

    async def _send_start_reminder_24hr(self) -> None:
        await self._send_message("REMINDER_START_24HR")

    async def _send_start_msg(self) -> None:
        await self._send_message("START_MESSAGE")

    async def _send_end_reminder_24hr(self) -> None:
        await self._send_message("REMINDER_END_24HR")

    async def _send_end_msg(self) -> None:
        await self._send_message("END_MESSAGE")

    @tasks.loop(seconds=1)
    async def start_bingo(self) -> None:
        if not self.configured:
            logger.warning("[Bingo Cog] Cog not properly configured.")
            return
        
        ctime = self.now_gmt()

        if self.end_sent:
            self.start_bingo.stop()

        if not self.signup_reminder_sent:
            # Signup reminder not sent yet, check if need to post it
            if ctime > self.signup_datetime:
                await self._send_signup_reminder_24hr()
                self.signup_reminder_sent = True
        
        if not self.start_reminder_sent:
            # Start reminder not sent yet, check if need to post it
            if ctime > self.start_reminder_datetime:
                await self._send_start_reminder_24hr()
                self.start_reminder_sent = True

        if not self.start_sent:
            if ctime > self.start_datetime:
                await self._send_start_msg()
                self.start_sent = True

        if not self.end_reminder_sent:
            # End reminder not sent yet, check if need to post it
            if ctime > self.end_reminder_datetime:
                await self._send_end_reminder_24hr()
                self.end_reminder_sent = True
        
        if not self.end_sent:
            if ctime > self.end_datetime:
                await self._send_end_msg()
                self.end_sent = True
        
        