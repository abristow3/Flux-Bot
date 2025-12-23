import logging
import discord
import pandas as pd
from typing import Dict
import logging
from discord.ext.commands import Bot
from src.hunt_stats.parsers.GDoc.GDocDataRetriever import GDocDataRetriever
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BingoConfigParser:
    def __init__(self, discord_bot: Bot, gdoc_retriever: GDocDataRetriever) -> None:
        self.discord_bot = discord_bot
        self.gdoc = gdoc_retriever
        self.config: Dict[str, dict] = {}
        self.team_names: set[str] = set()
        self.text_channels: list[str] = []
        self.voice_channels: list[str] = []
        self.roles: list[str] = ["Bingo"]
        self.team_name_prefix = "team"

    def load_bingo_config(self) -> None:
        """
        Reads the 'Bot Config' sheet and returns a nested dictionary:

        {
            username: {
                "discord_id": <disc_id>,
                "team_name": <team_name>,
                "color": <hex_color>,
                "role_name": f"{self.team_name_prefix}-{team_name}"
            }
        }
        """
        try:
            raw_data = self.gdoc.get_data_from_sheet("Bot Config")

            if raw_data.size == 0:
                logger.warning("Bot Config sheet is empty or missing.")
                return {}

            headers = raw_data[0]
            rows = raw_data[1:]

            df = pd.DataFrame(rows, columns=headers)

            for _, row in df.iterrows():
                username = str(row["Participant"]).strip()
                if not username:
                    continue

                team_name = row["Team Name"].strip()
                # Add color field and role_name alongside discord_id and team_name
                self.config[username] = {
                    "discord_id": row["Discord ID"],
                    "team_name": team_name,
                    "color": row.get("Color", "#000000"),  # default black if missing
                    "role_name": f"{self.team_name_prefix}-{team_name}"
                }

            logger.info(f"Loaded {len(self.config)} bingo config entries.")
            self.save_config_as_json(fp="src/conf/bingo_config.json")
        except Exception as e:
            logger.error("Error parsing Bingo Config Sheet", exc_info=e)

    def parse_team_names(self) -> None:
        # iterate over config
        logger.info(f"[BingoConfigParser] Parsing team names")
        for username, data in self.config.items():
            team_name = data["team_name"]
            self.team_names.add(team_name)

        logger.info(f"[BingoConfigParser] Team name parsing completed")
    
    def generate_channel_and_role_names(self) -> None:
        # iterate over each unique team name
        for name in self.team_names:
            # Create channel and role name for the team
            self.text_channels.append(f"{self.team_name_prefix}-{name}-chat")
            self.voice_channels.append(f"{self.team_name_prefix}-{name}-voice")
            self.roles.append(f"{self.team_name_prefix}-{name}")

    async def create_text_channel(self, channel_name: str) -> None:
        # Create the text channel
        guild = self.discord_bot.guilds[0]
        channel_name = f"{self.team_name_prefix}-{channel_name}"
        await guild.create_text_channel(name=channel_name)

    async def create_voice_channel(self, channel_name: str) -> None:
        guild = self.discord_bot.guilds[0]
        channel_name = f"{self.team_name_prefix}-{channel_name}"
        await guild.create_voice_channel(name=channel_name)
    
    async def create_role_with_color(self, team_name: str, hex_color: str):
        guild = self.discord_bot.guilds[0]

        # Convert hex string to discord.Color
        try:
            # Remove # if present
            hex_color = hex_color.lstrip("#")
            color_int = int(hex_color, 16)
            color = discord.Color(color_int)
        except ValueError:
            logger.info(f"Invalid hex color: {hex_color}. Using default color.")
            color = discord.Color.default()
        
        # Create the role
        role_name = f"{self.team_name_prefix}-{team_name}"
        role = await guild.create_role(name=role_name,color=color,mentionable=True)
        logger.info(f"Created role: {role.name} with color {hex_color}")

    async def assign_participant_roles(self) -> None:
        """
        Assigns the corresponding team role to each participant
        based on the nested config dict. Stores the assigned Role
        object under each participant's entry.
        """
        guild = self.discord_bot.guilds[0]

        for username, data in self.config.items():
            discord_id = data.get("discord_id")
            role_name = data.get("role_name")

            if not discord_id or not role_name:
                logger.warning(f"Skipping {username}: missing discord_id or role_name")
                continue

            # Fetch the role object by name
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                logger.warning(f"Role '{role_name}' not found in guild to assign to {username}")
                continue

            # Fetch the member object by Discord ID
            member = guild.get_member(int(discord_id))
            if not member:
                logger.warning(f"Member with ID {discord_id} not found in guild for {username}")
                continue

            try:
                await member.add_roles(role, reason="Assigning Bingo Team role")
                # Store the role object under participant entry for later reference
                self.config[username]["role_obj"] = role
                logger.info(f"Assigned role '{role_name}' to {username}")
            except Exception as e:
                logger.error(f"Failed to assign role '{role_name}' to {username}: {e}", exc_info=e)

    def save_config_as_json(self, fp: str) -> None:
        """
        Saves self.config as a JSON file.
        If no file path is provided, saves to 'bingo_config.json' in the current directory.
        """
        path = Path(fp)

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            print(f"Config successfully saved to {path.resolve()}")
        except Exception as e:
            print(f"Failed to save config to {path}: {e}")


DISCORD_SETUP_SUMMARY_TEMPLATE = """\
Discord Setup Summary
=====================

Roles to be Created:
{roles}

Text Channels to be Created:
{text_channels}

Voice Channels to be Created:
{voice_channels}

User Role Assignments:
{user_roles}
"""

if __name__ == "__main__":
    import logging
    from src.hunt_stats.parsers.GDoc.GDocDataRetriever import GDocDataRetriever

    logging.basicConfig(level=logging.INFO)

    SHEET_ID = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"

    # Initialize the Google Sheet retriever
    retriever = GDocDataRetriever(sheet_id=SHEET_ID)

    # Initialize the parser (discord_bot=None for testing config only)
    parser = BingoConfigParser(discord_bot=None, gdoc_retriever=retriever)

    # Load the bingo config
    parser.load_bingo_config()

    # Parse unique team names
    parser.parse_team_names()

    # Generate all channel and role names in memory
    parser.generate_channel_and_role_names()

    # Generate user-role assignments (username (role_name))
    user_roles_str = "\n".join(f"{username} ({data['role_name']})" for username, data in parser.config.items())

    roles_str = "\n".join(f"- {r}" for r in parser.roles)
    text_channels_str = "\n".join(f"- {c}" for c in parser.text_channels)
    voice_channels_str = "\n".join(f"- {v}" for v in parser.voice_channels)
    user_roles_str = "\n".join(
        f"- {username} ({data['role_name']})" for username, data in parser.config.items()
    )

    channels = True
    # if command called with channels flag as False, don't display them
    if not channels:
        text_channels_str = "None"
        voice_channels_str = "None"

    summary_message = DISCORD_SETUP_SUMMARY_TEMPLATE.format(
        roles=roles_str,
        text_channels=text_channels_str,
        voice_channels=voice_channels_str,
        user_roles=user_roles_str
    )

    # Print the filled template
    print(summary_message)




    



