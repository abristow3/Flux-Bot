import asyncio
import colorsys
import logging
from typing import Optional
import discord
from discord import app_commands, Interaction
from src.main import BotClient
from src.cogs.BingoCog import BingoCog

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


def generate_distinct_colors(n: int, saturation: float = 0.8, value: float = 0.9):
    """
    Generate n visually distinct colors as discord.Color objects.

    :param n: Number of colors to generate
    :param saturation: Saturation for the colors (0-1)
    :param value: Brightness for the colors (0-1)
    :return: List of discord.Color
    """
    colors = []
    for i in range(n):
        # distribute evenly around the color wheel
        hue = i / n
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        colors.append(discord.Color.from_rgb(r, g, b))
    return colors


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


async def bingo_setup(interaction: discord.Interaction, discord_bot: BotClient, sheet_id: str, channels: bool) -> None:
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
    authorized = discord_bot.utils.check_user_roles(user=interaction.user, authorized_roles=authorized_roles)
    if not authorized:
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
        return

    # Attempt to get the BingoCog
    bingo_cog: Optional[BingoCog] = discord_bot.get_cog("BingoCog")

    # If cog is not loaded, dynamically load it
    if bingo_cog is None:
        try:
            bingo_cog = BingoCog(discord_bot)
            await discord_bot.add_cog(bingo_cog)
            await interaction.followup.send("BingoCog was not loaded, but has now been initialized.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to load BingoCog: {e}", ephemeral=True)
            return

    bingo_cog.load_config()
    await interaction.followup.send("Bingo setup loaded successfully.", ephemeral=True)

    # TODO wrap this an in 'if verified == True:' block
    # Create the bingo roles
    colors = generate_distinct_colors(len(bingo_cog.config_parser.roles))
    for role_name, color in zip(bingo_cog.config_parser.roles, colors):
        await discord_bot.utils.create_role(role_name=role_name, color=color, mentionable=True)

    # if command was invoked with channels=True, create voice and text channels
    # TODO setup channel permissions to match the roles? maybe need a role to channel map
    # if channels:
    #     for text_channel in bingo_cog.config_parser.text_channels:
    #         await discord_bot.utils.create_text_channel(channel_name=text_channel,
    #                                                     category_id=bingo_cog.bingo_discord_category_id)
    #
    #     for voice_channel in bingo_cog.config_parser.voice_channels:
    #         await discord_bot.utils.create_voice_channel(channel_name=voice_channel,
    #                                                      category_id=bingo_cog.bingo_discord_category_id)

    # Assign users their roles
    participant_list = bingo_cog.config_parser.participants_dict.get("Participants", [])
    for player in participant_list:
        member = discord_bot.utils.get_guild_member_by_id(user_id=player.get("Discord ID", None))
        event_role_set = await discord_bot.utils.assign_user_role(user=member, role_name="Bingo!")
        team_role_set = await discord_bot.utils.assign_user_role(user=member, role_name=player.get("Team Name", None))

        if not event_role_set or not team_role_set:
            await interaction.followup.send("Error when assigning user roles for bingo.", ephemeral=True)
            return


async def bingo_cleanup(interaction: discord.Interaction, discord_bot: BotClient) -> None:
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
    authorized = discord_bot.utils.check_user_roles(user=interaction.user, authorized_roles=authorized_roles)
    if not authorized:
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
        return


def register_bingo_commands(tree: app_commands.CommandTree, discord_bot: BotClient) -> None:
    @tree.command(name="bingo_setup", description="Sets up roles, team channels, and permissions for the bingo event")
    @app_commands.describe(sheet_id="The GDoc sheet ID for the event configuration",
                           channels="Flag for event text/voice channel creation. Defaults to False.")
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
