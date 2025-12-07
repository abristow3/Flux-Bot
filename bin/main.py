#!/usr/bin/env python3
import asyncio
import discord
from discord.ext import commands, tasks
import logging
import os

from commands.role_commands import register_role_commands
from commands.message_commands import register_message_commands

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Capture all logs

# Common formatter
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler (prints to terminal)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Change to DEBUG if you want more verbose logs
console_handler.setFormatter(formatter)

# Add console handler to the root logger
logger.addHandler(console_handler)

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.error("[Main Task Loop] No Discord API token found.")
    exit()

logger.info("[Main Task Loop] Discord API token found successfully.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


async def sync_commands(test: bool = False):
    try:
        # Optional: force sync for a specific guild
        if test:
            guild = discord.Object(id=414435426007384075)
            await bot.tree.sync(guild=guild)
            logger.info("[Main Task Loop] Slash commands have been synced to guild.")

        # Also sync globally (optional but safe to include)
        await bot.tree.sync()
        logger.info("[Main Task Loop] Global slash commands have been successfully refreshed!")
    except Exception as e:
        logger.error(f"[Main Task Loop] Error refreshing commands: {e}")


async def list_commands():
    # List all global commands
    logger.info("[Main Task Loop] Listing all registered commands:")
    for command in bot.tree.get_commands():
        logger.info(f"[Main Task Loop] Command Name: {command.name}, Description: {command.description}")


@bot.event
async def on_ready():
    logger.info("[Main Task Loop] Loading Assets...")
    with open("assets/avatar.png", "rb") as avatar_file:
        # Update the bot's avatar
        image = avatar_file.read()
        await bot.user.edit(avatar=image)

    logger.info("[Main Task Loop] Assets Loaded")

    register_role_commands(tree=bot.tree, discord_bot=bot)
    register_message_commands(tree=bot.tree, discord_bot=bot)

    # Sync and List all commands
    await sync_commands(test=True)
    await list_commands()


async def main():
    await bot.start(TOKEN)


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
