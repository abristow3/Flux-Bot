from discord import Member
from discord import Color
from typing import Optional

class DiscordUtils:
    def __init__(self, guild_id: str):
        self.guild_id = guild_id

    # ---------- CHANNELS ----------
    async def create_text_channel(self, channel_name: str) -> None:
        ...

    async def delete_text_channel(self, channel_name: str) -> None:
        ...

    async def create_voice_channel(self, channel_name: str) -> None:
        ...

    async def delete_voice_channel(self, channel_name: str) -> None:
        ...

    # ---------- ROLES ----------
    async def create_role(self, role_name: str, color: Optional[Color] = None, mentionable: bool = False) -> None:
        ...

    async def delete_role(self, role_name: str) -> None:
        ...

    async def assign_user_role(self, user: Member, role_name: str) -> None:
        ...

    async def revoke_user_role(self, user: Member, role_name: str) -> None:
        ...

    # ---------- HELPERS ----------
    def _get_voice_channel_list(self) -> list:
        ...

    def _get_text_channel_list(self) -> list:
        ...

    def _get_role_list(self) -> list:
        ...

    async def _get_member_by_id(self, user_id: str) -> Member:
        ...
