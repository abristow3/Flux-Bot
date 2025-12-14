import os
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GDoc:
    def __init__(self) -> None:
        self.service = None
        self.sheets = None
        self.sheet_id = ""
        self.creds_path = ""
        self.credentials = None
        self.on_startup()

    def on_startup(self) -> None:
        """Initialize the Google Sheets API client."""
        try:
            self.creds_path = "src/conf/google_auth.json"
            logger.info(f"GOOGLE CREDS PATH: {self.creds_path}")

            if not self.creds_path or not os.path.exists(self.creds_path):
                logger.error("Missing or invalid GOOGLE_CREDENTIALS_PATH")
                return

            self.credentials = service_account.Credentials.from_service_account_file(
                self.creds_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )

            self.service = build("sheets", "v4", credentials=self.credentials)
            self.sheets = self.service.spreadsheets()
            logger.info("Google Sheets API client initialized successfully.")

        except Exception as e:
            logger.error(f"Error during GDoc setup: {e}")

    def set_sheet_id(self, sheet_id: str) -> None:
        """Set the target Google Sheet ID."""
        self.sheet_id = sheet_id

    def get_data_from_sheet(self, sheet_name: str) -> np.ndarray:
        """Fetch data from a sheet and return as a NumPy array."""
        logger.info(f"Retrieving data from sheet '{sheet_name}'...")
        try:
            result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=sheet_name).execute()
            values = result.get("values", [])
            data_array = np.array(values, dtype=object)
            logger.info(f"Retrieved {data_array.shape[0]} rows from '{sheet_name}'.")
            return data_array
        except Exception as e:
            logger.error(f"Unable to fetch data from '{sheet_name}': {e}")
            return np.array([], dtype=object)
