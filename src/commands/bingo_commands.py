import discord
from discord import app_commands
import logging
import asyncio
from discord import Interaction, utils
from discord.ext.commands import Bot
import asyncio
from discord import Interaction
from src.hunt_stats.parsers.GDoc.GDocDataRetriever import GDocDataRetriever
from src.commands.BingoConfigParser import BingoConfigParser

logger = logging.getLogger(__name__)

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

async def send_bingo_verify_message(discord_bot, parser, interaction: Interaction, channels: bool) -> bool:
    """
    Sends an ephemeral verification message showing roles/channels from the parser.
    Lets the user react with ✅ to confirm or ❌ to cancel.
    """
    timeout = 120.0
    # Format the summary
    roles_str = "\n".join(f"- {r}" for r in parser.roles)
    text_channels_str = "\n".join(f"- {c}" for c in parser.text_channels)
    voice_channels_str = "\n".join(f"- {v}" for v in parser.voice_channels)
    user_roles_str = "\n".join(
        f"- {username} ({data['team_name']})" for username, data in parser.config.items()
    )

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

    # Send ephemeral message
    await interaction.response.send_message(
        f"```{summary_message}```\nReact with ✅ to confirm, ❌ to cancel.",
        ephemeral=True
    )

    msg = await interaction.original_message()
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    # Define reaction check
    def check(reaction, user):
        return (
            user == interaction.user
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == msg.id
        )

    try:
        reaction, user = await discord_bot.wait_for("reaction_add", timeout=timeout, check=check)

        if str(reaction.emoji) == "✅":
            await interaction.followup.send("✅ You confirmed the config!", ephemeral=True)
            return True
        elif str(reaction.emoji) == "❌":
            await interaction.followup.send("❌ Setup canceled by user.", ephemeral=True)
            return False

    except asyncio.TimeoutError:
        await interaction.followup.send("⏱ No reaction received in time. Setup canceled.", ephemeral=True)
        return False

async def check_user_roles(interaction: discord.Interaction, authorized_roles: list) -> bool:
    user_roles = [role.name.lower() for role in getattr(interaction.user, "roles", [])]
    authorized_roles = [role.lower() for role in authorized_roles]

    if any(role in user_roles for role in authorized_roles):
        return True
    else:
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
        return False

async def bingo_setup(interaction: discord.Interaction, discord_bot: Bot, sheet_id: str, channels: bool) -> None:
    '''
    - generate a list of the channels and roles / roles being assigned to which users being created, and ask user to verify it is correct by reacting with a checkmark?
    - if reacted with an X, then terminate the process
    - if reacted, then proceed to making them if they don't exist yet. 
    - Create role, voice channel, and text channel for team name in the set
        - set up the correct channel permissions so all staff, event host, and the corresponding role can see and use the channels
    - Assign roles to all participants using discord ID from dict
    - send success message

    '''
    guild = interaction.guild
    
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    authorized_roles = ["General", "Captain", "Lieutenant"]
    authorized = await check_user_roles(interaction=interaction, authorized_roles=authorized_roles)

    if not authorized:
        return
    
    # First checks if it can pull the GDoc data
    try:
        retriever = GDocDataRetriever(sheet_id=SHEET_ID)
        parser = BingoConfigParser(retriever)
        parser.load_bingo_config()
    except Exception as e:
        logger.error(f"[BingoCommands Setup] Error retrieving and parsing GDoc config", exc_info=e)
        interaction.followup.send(f"Unable to access the Google Sheet with sheet ID: {sheet_id}", ephemeral=True)

    if channels:
        # Generate and send verification message
        confirmed = await send_bingo_verify_message(discord_bot=discord_bot, parser=parser, interaction=interaction, channels=channels)
        
    if confirmed:
        # If verified, create channels and roles
        ...
    else:
        # abort
        ...

async def bingo_cleanup(interaction: discord.Interaction, discord_bot: Bot) -> None:
    '''
    - Generates a list of the bingo channels and roles that it will be deleting
    - Asks the user to verify
    - If yes, delete channels and roles
    - If No, terminate
    '''
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    authorized_roles = ["General", "Captain", "Lieutenant"]
    authorized = await check_user_roles(interaction=interaction, authorized_roles=authorized_roles)

    if not authorized:
        return

def register_bingo_commands(tree: app_commands.CommandTree, discord_bot: Bot) -> None:
    @tree.command(name="bingo_setup", description="Sets up roles, team channels, and permissions for the bingo event")
    @app_commands.describe(sheet_id="The GDoc sheet ID for the event configuration", channels="Flag for event text/voice channel creation. Defaults to False.")
    async def bingo_setup_cmd(interaction: discord.Interaction, sheet_id: str, channels: bool = False):
        logger.info("[Bingo Commands] /bingo_setup command called")
        await interaction.response.defer()
        await bingo_setup(interaction, discord_bot=discord_bot, sheet_id=sheet_id, channels=channels)
    
    @tree.command(name="bingo_cleanup", description="Removes bingo roles, and team channels from the server.")
    async def bingo_cleanup_cmd(interaction: discord.Interaction):
        logger.info("[Bingo Commands] /bingo_cleanup command called")
        await interaction.response.defer()
        await bingo_cleanup(interaction, discord_bot=discord_bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SHEET_ID = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
