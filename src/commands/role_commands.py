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


async def clone_role(interaction: discord.Interaction, discord_bot: Bot, source_role_name: str,
                     new_role_name: str) -> None:
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

    # find the source role
    source_role = discord.utils.get(guild.roles, name=source_role_name)
    if not source_role:
        await interaction.followup.send(f"Role '{source_role_name}' not found.", ephemeral=True)
        return

    # create new role with base permissions
    new_role = await guild.create_role(
        name=new_role_name,
        permissions=source_role.permissions,
        color=source_role.color,
        hoist=source_role.hoist,
        mentionable=source_role.mentionable,
        reason=f"Cloned from {source_role.name}"
    )

    # copy channel and category overwrites
    for channel in guild.channels:
        overwrite = channel.overwrites_for(source_role)
        # Only copy if there is a real overwrite
        if overwrite.pair()[0] != discord.PermissionOverwrite():
            await channel.set_permissions(new_role, overwrite=overwrite)


def register_role_commands(tree: app_commands.CommandTree, discord_bot: Bot) -> None:
    @tree.command(name="clone_role", description="Clones sevrer permissions for a role into a new one.")
    @app_commands.describe(source_role_name="The name of the role that you want permissions cloned for.",
                           new_role_name="The name of the new role.")
    async def clone_cmd(interaction: discord.Interaction, source_role_name: str, new_role_name: str):
        logger.info("[Role Commands] /clone_role command called")
        await interaction.response.defer()
        await clone_role(interaction, discord_bot=discord_bot, source_role_name=source_role_name,
                         new_role_name=new_role_name)
        await interaction.followup.send(f"Role '{new_role_name}' cloned from '{source_role_name}'!")
