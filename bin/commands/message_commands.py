import discord
from discord import app_commands
import logging
from discord.ext.commands import Bot

logger = logging.getLogger(__name__)


async def check_user_roles(interaction: discord.Interaction, authorized_roles: list) -> bool:
    user_roles = [role.name.lower() for role in getattr(interaction.user, "roles", [])]
    authorized_roles = [role.lower() for role in authorized_roles]

    if any(role in user_roles for role in authorized_roles):
        return True
    else:
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
        return False


async def send_message(interaction: discord.Interaction, discord_bot: Bot, message_content: str) -> None:
    """
    Clones all general, channel, and category level permissions in a server for a specific role into a new role.
    """
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    authorized_roles = ["General", "Captain", "Lieutenant"]
    authorized = await check_user_roles(interaction=interaction, authorized_roles=authorized_roles)

    if not authorized:
        return

    try:
        await interaction.channel.send(message_content)
        await interaction.followup.send("Message sent!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I cannot send messages in this channel.", ephemeral=True)


def register_message_commands(tree: app_commands.CommandTree, discord_bot: Bot) -> None:
    @tree.command(name="send_message", description="Sends your message as the Flux Bot")
    @app_commands.describe(message_content="The message you want to send.")
    async def send_msg_cmd(interaction: discord.Interaction, message_content: str):
        logger.info("[Message Commands] /send_message command called")
        await interaction.response.defer()
        await send_message(interaction, discord_bot=discord_bot, message_content=message_content)
