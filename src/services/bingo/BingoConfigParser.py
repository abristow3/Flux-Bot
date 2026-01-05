import pandas as pd
import logging
from typing import List, Dict, Set
from src.services.GDoc.GDoc import GDoc
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class InvalidConfig(Exception):
    def __init__(self, message="Error reading configuration file"):
        # Call the base class constructor
        super().__init__(message)


class BingoConfigParser:
    def __init__(self, gdoc_retriever):
        self.gdoc = gdoc_retriever
        self.config_table_name = "Config"
        self.participants_table_name = "Participants"
        self.config_fp = "src/conf/bingo_config.json"
        self.participants_fp = "src/conf/bingo_participants.json"
        self.participants_dict = {}
        self.config_dict = {}

        # Raw sheet data
        self.sheet_data: pd.DataFrame = pd.DataFrame()

        # Maps table_name -> {start_col, end_col}
        self.table_map: Dict[str, Dict[str, int]] = {}

        # Extracted tables
        self.participants_table_data: pd.DataFrame = pd.DataFrame()
        self.config_table_data: pd.DataFrame = pd.DataFrame()

        # Channels and roles to create
        self.team_names: Set[str] = set()
        self.text_channels: Set[str] = set()
        self.voice_channels: Set[str] = set()
        self.roles: Set[str] = set({"Bingo!"})

        # Define required config keys
        self.required_config_keys = [
            "REMINDER_START_24HR",
            "REMINDER_SIGNUP_24HR",
            "REMINDER_END_24HR",
            "BINGO_START_TIME_GMT",
            "BINGO_START_DATE",
            "BINGO_END_DATE",
            "BINGO_END_TIME",
            "START_MESSAGE",
            "END_MESSAGE",
            "SIGNUP_END_DATE",
            "SIGNUP_END_TIME",
            "EVENT_PASSWORD"
        ]

    def set_sheet_name(self, sheet_name: str) -> None:
        self.sheet_name = sheet_name

    def set_sheet_data(self, data) -> None:
        try:
            df = pd.DataFrame(data)
            df.iloc[0] = df.iloc[0].replace({"": None})
            self.sheet_data = df
        except Exception as e:
            logger.error(e)
            logger.error("Error creating Dataframe")
            self.sheet_data = pd.DataFrame()

    def build_table_map(self) -> None:
        logger.info("Building table map...")
        start_col = None
        end_col = None
        name = ""

        try:
            # Dynamically find the cells that fall under the merged cell table name
            for col in range(len(self.sheet_data.columns)):
                header_value = self.sheet_data.iloc[0, col]

                if header_value is not None:
                    name = header_value
                    start_col = col

                    self.table_map[name] = {"start_col": start_col}

                if header_value is None:
                    end_col = col
                    self.table_map.setdefault(name, {})['end_col'] = end_col
        except Exception as e:
            logger.error(e)
            logger.error("Error building table map")
            self.table_map = {}

    def pull_table_data(self, table_name: str) -> None:
        logger.info("Pulling Table Data...")
        table_metadata = self.table_map.get(table_name, {})
        if not table_metadata:
            return []

        logger.info(f"Data located between columns {table_metadata['start_col']} and {table_metadata['end_col']}")

        # Get the data between columns
        df = self.sheet_data.iloc[:, table_metadata['start_col']:table_metadata['end_col'] + 1].copy()

        # Drop the header row (merged cell label)
        df = df.drop(index=0).reset_index(drop=True)

        # Replace empty strings with pd.NA
        df = df.replace("", pd.NA)

        # Drop completely empty columns
        df = df.dropna(axis=1, how='all')

        # Drop completely empty rows
        df = df.dropna(how='all')

        # Set the second row (index 0 now) as column headers
        df.columns = df.iloc[0]
        df = df.drop(index=0).reset_index(drop=True)

        return df

    def load_config_table(self, df: pd.DataFrame) -> None:
        try:
            # Convert DF into dict
            self.config_dict = dict(zip(df["Key"], df["Value"]))
            logger.debug(f"Raw config_dict loaded: {self.config_dict}")
        except Exception as e:
            logger.exception("Failed to parse configuration dataframe.")
            raise InvalidConfig("Failed to parse configuration dataframe.")

        if not self.config_dict:
            raise InvalidConfig("Configuration map is empty.")

        # Check for missing fields in the config dict
        missing_fields = []
        for key in self.required_config_keys:
            value = self.config_dict.get(key, "").strip() if self.config_dict.get(key) else ""
            if not value:
                missing_fields.append(key)

        if missing_fields:
            logger.error(f"Missing or empty configuration fields: {', '.join(missing_fields)}")
            raise InvalidConfig(f"Missing or empty configuration fields: {', '.join(missing_fields)}")

        # Combine Bingo start date/time into a datetime object
        start_datetime_str = f"{self.config_dict.get('BINGO_START_DATE', '')} {self.config_dict.get('BINGO_START_TIME_GMT', '')}"
        try:
            self.start_datetime = datetime.strptime(start_datetime_str, "%d/%m/%Y %H:%M")
            self.start_datetime = pytz.timezone("Europe/London").localize(self.start_datetime)
            self.end_datetime = self.start_datetime + timedelta(days=3)
        except ValueError:
            logger.exception(f"Invalid Bingo start date/time format: {start_datetime_str}")
            raise InvalidConfig("Invalid date/time format. Expected format: DD/MM/YYYY HH:MM")

        self.configured = True
        self._save_dict_as_json(fp=self.config_fp, data=self.config_dict)
        logger.info("Bingo configuration loaded successfully.")

    def load_participants_table(self, df: pd.DataFrame) -> None:
        """
        Load participants from the 'Participants' table dataframe.
        Expects a table with columns: 'Participant', 'Discord ID', 'Team Name', and 'Color'.
        Converts the DataFrame into a dictionary and stores it in the class attribute.
        """
        # Define required participants table columns
        required_columns = ['Participant', 'Discord ID', 'Team Name', 'Color']
        
        try:
            # Check for missing required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Participants table missing required columns: {', '.join(missing_columns)}")
                raise InvalidConfig(f"Participants table missing required columns: {', '.join(missing_columns)}")
            
            # Clean and convert the DataFrame into a list of dictionaries
            participants_data = df[['Participant', 'Discord ID', 'Team Name', 'Color']].dropna()
            participants_list = participants_data.to_dict(orient="records")
            
            # Store participants data as a dictionary
            self.participants_dict = {"Participants": participants_list}
            
            logger.debug(f"Participants data converted to dict: {self.participants_dict}")

            # Extract unique team names and log them
            logger.info(f"Teams found: {', '.join(self.team_names)}")
            self._build_team_names()
            self._build_text_channel_names()
            self._build_voice_channel_names()
            self._build_role_names()
            self._save_dict_as_json(fp=self.participants_fp, data=self.participants_dict)
        except Exception as e:
            logger.exception("Failed to load participants table.")
            raise InvalidConfig("Failed to load participants table.")

    def _save_dict_as_json(self, fp: str, data: dict) -> None:
        path = Path(fp)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            print(f"Data successfully saved to {path.resolve()}")
        except Exception as e:
            print(f"Failed to save data to {path}: {e}")

    def _build_team_names(self) -> None:
        # Iterates over the list of participants and extracts the team name
        for participant in self.participants_dict["Participants"]:
            team_name = participant.get("Team Name", "")
            self.team_names.add(team_name)
    
    def _build_text_channel_names(self) -> None:
        # Create a text channel name for each unique team name
        for name in self.team_names:
            channel_name = f"{name}-text"
            self.text_channels.add(channel_name)

    def _build_voice_channel_names(self) -> None:
        # Create a voice channel name for each unique team name
        for name in self.team_names:
            channel_name = f"{name}-voice"
            self.voice_channels.add(channel_name)

    def _build_role_names(self) -> None:
        # Create a role name for each unique team name
        for name in self.team_names:
            self.roles.add(name)


# ==== TEST SCRIPT ====
if __name__ == "__main__":
    # Initialize mock bot and GDoc retriever
    gdoc = GDoc()
    gdoc.set_sheet_id("1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk")

    # Initialize BingoConfigParser
    parser = BingoConfigParser(gdoc_retriever=gdoc)
    parser.set_sheet_name("Bot Config")

    # Retrieve and set sheet data
    sheet_data = gdoc.get_data_from_sheet(parser.sheet_name)
    parser.set_sheet_data(sheet_data)

    # Build table map and pull table data
    parser.build_table_map()
    parser.config_table_data = parser.pull_table_data(parser.config_table_name)
    
    # Load configuration table
    parser.load_config_table(parser.config_table_data)
    logger.info("Bingo configuration loaded successfully!\n")
    print(parser.config_dict)

    # Load participants table
    parser.participants_table_data = parser.pull_table_data(parser.participants_table_name)
    parser.load_participants_table(parser.participants_table_data)
    logger.info("Participants data loaded successfully!\n")
    print(parser.participants_dict)
    print(f"TEAM NAMES: {parser.team_names}\n")
    print(f"TCS: {parser.text_channels}\n")
    print(f"VCS: {parser.voice_channels}\n")
    print(f"ROLES: {parser.roles}\n")


