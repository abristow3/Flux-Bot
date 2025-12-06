#!/usr/bin/env python3
import asyncio
import discord
from discord.ext import commands, tasks
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Capture all logs

# Common formatter
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Debug handler (everything goes here)
debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)

# Info handler (INFO and up)
info_handler = logging.FileHandler('app.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# Add handlers to root logger
logger.addHandler(debug_handler)
logger.addHandler(info_handler)

# Optional: Get logger for current module
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    logger.error("[Main Task Loop] No Discord API token found.")
    exit()

logger.info("[Main Task Loop] Discord API token found successfully.")

intents = discord.Intents.default()
intents.message_content = True
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
    with open("assets/Clay_golem_chathead.png", "rb") as avatar_file:
        # Update the bot's avatar
        image = avatar_file.read()
        await bot.user.edit(avatar=image)

    logger.info("[Main Task Loop] Assets Loaded")

    # register_main_commands(bot.tree, gdoc, hunt_bot, state, bot)
    # Sync and List all commands
    await sync_commands(test=True)
    await list_commands()

    logger.info(f"[Main Task Loop] Logged in as {bot.user}")

async def main():
    await bot.start(TOKEN)

def run():
    asyncio.run(main())