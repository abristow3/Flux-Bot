import pandas as pd
import logging
from typing import Dict, Set
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
    def __init__(self, sheet_name: str = "Bot Config"):
        self.sheet_name = sheet_name
        self.config_table_name = "Config"
        self.config_fp = "src/conf/bingo/bingo_config.json"
        self.config_dict = {}

        # Raw sheet data
        self.sheet_data: pd.DataFrame = pd.DataFrame()
        self.table_map: Dict[str, Dict[str, int]] = {}

        # Extracted tables
        self.config_table_data: pd.DataFrame = pd.DataFrame()

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
            "MASTER_PASSWORD"
        ]

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

    def pull_table_data(self, table_name: str):
        logger.info("Pulling Table Data...")
        table_metadata = self.table_map.get(table_name, {})
        if not table_metadata:
            return pd.DataFrame()

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
        if not isinstance(df, pd.DataFrame):
            raise InvalidConfig(
                f"Expected DataFrame for config table, got {type(df).__name__}"
            )

        if df.empty:
            raise InvalidConfig("Configuration table is empty.")

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

        self._save_dict_as_json(fp=self.config_fp, data=self.config_dict)
        logger.info("Bingo configuration loaded successfully.")

    @staticmethod
    def _save_dict_as_json(fp: str, data: dict) -> None:
        path = Path(fp)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            print(f"Data successfully saved to {path.resolve()}")
        except Exception as e:
            print(f"Failed to save data to {path}: {e}")
