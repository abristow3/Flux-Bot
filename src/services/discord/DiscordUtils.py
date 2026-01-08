import logging
from typing import Optional

import discord
from discord import Color
from discord.ext import commands


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordUtils:
    def __init__(self, bot: commands.Bot, guild_id: int):
        """
        Initializes the DiscordUtils instance.

        :param bot: The instance of the bot.
        :param guild_id: The ID of the guild (server) where operations will be performed.
        """
        self.bot = bot
        self.guild_id = guild_id

    # ---------- CHANNELS ----------
    async def create_text_channel(self, channel_name: str, category_id: int = None) -> bool:
        """
        Creates a text channel in the guild if no duplicate exists.

        :param channel_name: The name of the channel to create.
        :param category_id: The category ID in which the channel should be created. Defaults to None (no category).
        :return: True if the channel was created, False if it already exists.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Check if a channel with the same name already exists
        existing_channel = self._get_text_channel_by_name(channel_name, category_id)
        if existing_channel:
            logger.info(f"Channel '{channel_name}' already exists in this category (or without category).")
            return False

        # Create the new channel
        logger.info(f"Creating new text channel: {channel_name}")
        await guild.create_text_channel(channel_name, category=category_id)
        return True

    async def create_voice_channel(self, channel_name: str, category_id: int = None) -> bool:
        """
        Creates a voice channel in the guild if no duplicate exists.

        :param channel_name: The name of the channel to create.
        :param category_id: The category ID in which the channel should be created. Defaults to None (no category).
        :return: True if the channel was created, False if it already exists.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Check if a channel with the same name already exists
        existing_channel = self._get_voice_channel_by_name(channel_name, category_id)
        if existing_channel:
            logger.info(f"Channel '{channel_name}' already exists in this category (or without category).")
            return False

        # Create the new channel
        logger.info(f"Creating new voice channel: {channel_name}")
        await guild.create_voice_channel(channel_name, category=category_id)
        return True

    async def delete_text_channel(self, channel_name: str) -> bool:
        """
        Deletes a text channel by name if it exists.

        :param channel_name: The name of the channel to delete.
        :return: True if the channel was deleted, False if not found or deletion failed.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Check if the channel exists
        channel = self._get_text_channel_by_name(channel_name)
        if not channel:
            logger.info(f"Channel '{channel_name}' not found.")
            return False

        # Delete the channel
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

        :param channel_name: The name of the channel to delete.
        :return: True if the channel was deleted, False if not found or deletion failed.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Check if the channel exists
        channel = self._get_voice_channel_by_name(channel_name)
        if not channel:
            logger.info(f"Channel '{channel_name}' not found.")
            return False

        # Delete the channel
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
        Creates a role in the guild if it does not already exist by the specified name.

        :param role_name: The name of the role to create.
        :param color: The color of the role (optional).
        :param mentionable: Whether the role can be mentioned (default is False).
        :return: True if the role was created, False if it already exists.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Check if the role already exists
        existing_role = self._get_role_by_name(role_name)

        # If it exists, log and do nothing
        if existing_role:
            logger.info(f"Role '{role_name}' already exists in the guild.")
            return False

        # Create the new role if it doesn't exist
        try:
            logger.info(f"Creating new role: {role_name}")
            await guild.create_role(name=role_name, color=color, mentionable=mentionable)
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to create role '{role_name}': {e}")
            return False

    async def delete_role(self, role_name: str) -> bool:
        """
        Deletes a role by its name if it exists in the guild.

        :param role_name: The name of the role to delete.
        :return: True if the role was deleted, False if not found.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return False

        # Get the role by name
        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found in the guild.")
            return False

        try:
            # Delete the role
            logger.info(f"Deleting role '{role_name}'.")
            await role.delete()
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to delete role '{role_name}': {e}")
            return False

    async def assign_user_role(self, user: discord.Member, role_name: str) -> bool:
        """
        Assigns a role to a user if they don't already have it.
        
        :param user: The member to assign the role to.
        :param role_name: The name of the role to assign.
        :return: True if the role was successfully assigned, False if the user already has it or if an error occurred.
        """
        # Check if the role exists
        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found.")
            return False

        # Check if the user already has the role
        if self._user_has_role(user, role_name):
            logger.info(f"User '{user.name}' already has the '{role_name}' role.")
            return False

        try:
            # Assign the role
            await user.add_roles(role)
            logger.info(f"Assigned '{role_name}' role to user '{user.name}'.")
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to assign '{role_name}' role to user '{user.name}': {e}")
            return False

    async def revoke_user_role(self, user: discord.Member, role_name: str) -> bool:
        """
        Revokes a role from a user if they have it.
        
        :param user: The member to revoke the role from.
        :param role_name: The name of the role to revoke.
        :return: True if the role was successfully revoked, False if the user doesn't have it or if an error occurred.
        """
        # Check if the role exists
        role = self._get_role_by_name(role_name)
        if not role:
            logger.info(f"Role '{role_name}' not found.")
            return False

        # Check if the user has the role
        if self._user_has_role(user, role_name):
            logger.info(f"User '{user.name}' does not have the '{role_name}' role.")
            return False

        try:
            # Revoke the role
            await user.remove_roles(role)
            logger.info(f"Revoked '{role_name}' role from user '{user.name}'.")
            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to revoke '{role_name}' role from user '{user.name}': {e}")
            return False

    # ---------- HELPERS ----------
    async def _get_guild_member_by_id(self, user_id: int) -> discord.Member | None:
        """
        Retrieves a member from the guild by their user ID.

        :param user_id: The ID of the user to search for.
        :return: The member object if found, otherwise None.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return None

        member = guild.get_member(user_id)
        if member is None:
            logger.info(f"Member with ID {user_id} not found in the guild.")
        return member

    def _get_guild_text_channels_list(self) -> list[discord.TextChannel]:
        """
        Retrieves all text channels in the guild.

        :return: A list of text channel objects in the guild.
        """
        guild = self.bot.get_guild(self.guild_id)
        return list(guild.text_channels) if guild else []

    def _get_guild_voice_channels_list(self) -> list[discord.VoiceChannel]:
        """
        Retrieves all voice channels in the guild.

        :return: A list of voice channel objects in the guild.
        """
        guild = self.bot.get_guild(self.guild_id)
        return list(guild.voice_channels) if guild else []

    def _get_text_channel_by_name(self, channel_name: str, category_id: int = None) -> discord.TextChannel | None:
        """
        Checks if a text channel with the specified name and category exists in the guild.

        :param channel_name: The name of the channel to search for.
        :param category_id: The category ID to filter by (optional).
        :return: The channel object if found, else None.
        """
        text_channels = self._get_guild_text_channels_list()
        for channel in text_channels:
            if channel.name == channel_name and (category_id is None or channel.category_id == category_id):
                return channel
        return None

    def _get_voice_channel_by_name(self, channel_name: str, category_id: int = None) -> discord.VoiceChannel | None:
        """
        Checks if a voice channel with the specified name and category exists in the guild.

        :param channel_name: The name of the channel to search for.
        :param category_id: The category ID to filter by (optional).
        :return: The channel object if found, else None.
        """
        voice_channels = self._get_guild_voice_channels_list()
        for channel in voice_channels:
            if channel.name == channel_name and (category_id is None or channel.category_id == category_id):
                return channel
        return None

    def _get_role_by_name(self, role_name: str) -> discord.Role | None:
        """
        Checks if a role with the specified name exists in the guild.

        :param role_name: The name of the role to search for.
        :return: The role object if found, else None.
        """
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild with ID {self.guild_id} not found.")
            return None

        for role in guild.roles:
            if role.name == role_name:
                return role
        return None

    def _user_has_role(self, user: discord.Member, role_name: str) -> bool:
        """
        Checks if the user already has a role with the specified name.

        :param user: The member to check.
        :param role_name: The name of the role to check.
        :return: True if the user has the role, False otherwise.
        """
        for role in user.roles:
            if role.name == role_name:
                return True
        return False
