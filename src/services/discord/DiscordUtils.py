from __future__ import annotations
import logging
from typing import TypeVar, Optional
import discord
from discord import Color
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=commands.Cog)


class DiscordUtils:
    def __init__(self, bot: commands.Bot, guild_id: int):
        """
        Initializes the DiscordUtils instance.

        :param bot: The instance of the bot.
        :param guild_id: The ID of the guild (server) where operations will be performed.
        """
        self.bot = bot
        self.guild = bot.get_guild(guild_id)

        if not self.guild:
            logger.warning(f"Guild {guild_id} not found at startup!")

    # ---------- CHANNELS ----------
    async def create_text_channel(self, channel_name: str, category_id: int = None) -> bool:
        """
        Creates a text channel in the guild if no duplicate exists.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        existing_channel = self._get_text_channel_by_name(channel_name, category_id)
        if existing_channel:
            logger.info(f"Channel '{channel_name}' already exists.")
            return False

        logger.info(f"Creating new text channel: {channel_name}")
        await self.guild.create_text_channel(channel_name, category=category_id)
        return True

    async def create_voice_channel(self, channel_name: str, category_id: int = None) -> bool:
        """
        Creates a voice channel in the guild if no duplicate exists.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        existing_channel = self._get_voice_channel_by_name(channel_name, category_id)
        if existing_channel:
            logger.info(f"Channel '{channel_name}' already exists.")
            return False

        logger.info(f"Creating new voice channel: {channel_name}")
        await self.guild.create_voice_channel(channel_name, category=category_id)
        return True

    async def delete_text_channel(self, channel_name: str) -> bool:
        """
        Deletes a text channel by name if it exists.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        channel = self._get_text_channel_by_name(channel_name)
        if not channel:
            logger.info(f"Channel '{channel_name}' not found.")
            return False

        try:
            logger.info(f"Deleting text channel '{channel_name}'.")
            await channel.delete()
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to delete text channel '{channel_name}': {e}")
            return False

    async def delete_voice_channel(self, channel_name: str) -> bool:
        """
        Deletes a voice channel by name if it exists.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        channel = self._get_voice_channel_by_name(channel_name)
        if not channel:
            logger.info(f"Channel '{channel_name}' not found.")
            return False

        try:
            logger.info(f"Deleting voice channel '{channel_name}'.")
            await channel.delete()
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to delete voice channel '{channel_name}': {e}")
            return False

    # ---------- ROLES ----------
    async def create_role(self, role_name: str, color: Optional[Color] = None, mentionable: bool = False) -> bool:
        """
        Creates a role in the guild if it does not already exist.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        existing_role = self._get_role_by_name(role_name)
        if existing_role:
            logger.info(f"Role '{role_name}' already exists.")
            return False

        try:
            logger.info(f"Creating new role: {role_name}")
            await self.guild.create_role(name=role_name, color=color, mentionable=mentionable)
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to create role '{role_name}': {e}")
            return False

    async def delete_role(self, role_name: str) -> bool:
        """
        Deletes a role by its name if it exists in the guild.
        """
        if not self.guild:
            logger.error("Guild not found.")
            return False

        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found.")
            return False

        try:
            logger.info(f"Deleting role '{role_name}'.")
            await role.delete()
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to delete role '{role_name}': {e}")
            return False

    async def check_user_roles(user: discord.Member, authorized_roles: list) -> bool:
        user_roles = [role.name.lower() for role in user.roles]
        authorized_roles = [role.lower() for role in authorized_roles]

        if any(role in user_roles for role in authorized_roles):
            return True
        else:
            return False

    async def assign_user_role(self, user: discord.Member, role_name: str) -> bool:
        """
        Assigns a role to a user if they don't already have it.
        """
        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found.")
            return False

        if any(r.name == role_name for r in user.roles):
            logger.info(f"User '{user.name}' already has the '{role_name}' role.")
            return False

        try:
            await user.add_roles(role)
            logger.info(f"Assigned '{role_name}' role to user '{user.name}'.")
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to assign '{role_name}' role to user '{user.name}': {e}")
            return False

    async def revoke_user_role(self, user: discord.Member, role_name: str) -> bool:
        """
        Revokes a role from a user if they have it.
        """
        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found.")
            return False

        if all(r.name != role_name for r in user.roles):
            logger.info(f"User '{user.name}' does not have the '{role_name}' role.")
            return False

        try:
            await user.remove_roles(role)
            logger.info(f"Revoked '{role_name}' role from user '{user.name}'.")
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to revoke '{role_name}' role from user '{user.name}': {e}")
            return False

    # ---------- COGS ----------
    def fetch_cog(self, cog_name: str, cog_type: type[T]) -> T:
        """
        Fetches a cog by name and type. Raises ValueError if not found or wrong type.
        """
        cog = self.bot.get_cog(cog_name)
        if not cog or not isinstance(cog, cog_type):
            raise ValueError(f"Cog {cog_name} not loaded or wrong type")
        return cog

    # ---------- HELPERS ----------
    async def get_guild_member_by_id(self, user_id: int) -> discord.Member | None:
        if not self.guild:
            logger.error("Guild not found.")
            return None
        member = self.guild.get_member(user_id)
        if member is None:
            logger.info(f"Member with ID {user_id} not found.")
        return member

    def _get_text_channel_by_name(self, channel_name: str, category_id: int = None) -> discord.TextChannel | None:
        for channel in self.guild.text_channels:
            if channel.name == channel_name and (category_id is None or channel.category_id == category_id):
                return channel
        return None

    def _get_voice_channel_by_name(self, channel_name: str, category_id: int = None) -> discord.VoiceChannel | None:
        for channel in self.guild.voice_channels:
            if channel.name == channel_name and (category_id is None or channel.category_id == category_id):
                return channel
        return None

    def _get_role_by_name(self, role_name: str) -> discord.Role | None:
        if not self.guild:
            logger.error("Guild not found.")
            return None
        for role in self.guild.roles:
            if role.name == role_name:
                return role
        return None
