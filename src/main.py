#!/usr/bin/env python3
import asyncio
import discord
from discord.ext import commands, tasks
import logging
import os

from src.commands.role_commands import register_role_commands
from src.commands.message_commands import register_message_commands
from src.commands.bingo_commands import register_bingo_commands
from src.services.discord.DiscordUtils import DiscordUtils

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class BotClient(commands.Bot):
    def __init__(self, token: str, guild_id: int):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents)

        self.token = token
        self.guild_id = guild_id
        self.utils = DiscordUtils(bot=self, guild_id=guild_id)

    async def setup_hook(self):
        """
        Called when the bot is starting. Use it to register cogs, commands, etc.
        """
        logger.info("[BotClient] Registering slash commands...")
        register_role_commands(tree=self.tree, discord_bot=self)
        register_message_commands(tree=self.tree, discord_bot=self)
        register_bingo_commands(tree=self.tree, discord_bot=self)

        await self.sync_commands(test=True)
        await self.list_commands()

    async def on_ready(self):
        logger.info(f"[BotClient] Logged in as {self.user} (ID: {self.user.id})")
        logger.info("[BotClient] Loading assets...")

        # Load avatar
        try:
            with open("assets/avatar.png", "rb") as avatar_file:
                image = avatar_file.read()
                await self.user.edit(avatar=image)
            logger.info("[BotClient] Assets loaded successfully")
        except Exception as e:
            logger.error(f"[BotClient] Failed to load avatar: {e}")

    async def sync_commands(self, test: bool = False):
        """Sync slash commands either to a test guild or globally."""
        try:
            if test:
                guild = discord.Object(id=self.guild_id)
                await self.tree.sync(guild=guild)
                logger.info("[BotClient] Slash commands synced to test guild")
            await self.tree.sync()
            logger.info("[BotClient] Global slash commands synced")
        except Exception as e:
            logger.error(f"[BotClient] Error syncing commands: {e}")

    async def list_commands(self):
        logger.info("[BotClient] Listing all registered slash commands:")
        for command in self.tree.get_commands():
            logger.info(f"Command: {command.name}, Description: {command.description}")

    async def start_bot(self):
        """Wrapper to start the bot."""
        await self.start(self.token)


# -------------------
# Entry Point
# -------------------
def run():
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        logger.error("No Discord API token found in environment")
        exit()

    GUILD_ID = 414435426007384075
    bot = BotClient(token=TOKEN, guild_id=GUILD_ID)

    asyncio.run(bot.start_bot())


if __name__ == "__main__":
    run()
