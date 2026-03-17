import logging

import discord
from discord.ext import tasks, commands

logger = logging.getLogger(__name__)


class MessageJanitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.osrs_news_channel_id = 414442125577682974
        self.string_to_sweep = "[Original Message Deleted]"

    async def cog_load(self) -> None:
        try:
            self.start_message_janitor.start()
        except Exception as e:
            logger.error(f"[Message Janitor Cog] Failed to load Message Janitor Cog: {e}")
            return

    async def cog_unload(self) -> None:
        if self.start_message_janitor.is_running():
            self.start_message_janitor.stop()

    async def _delete_message(self) -> None:

        channel = self.bot.get_channel(self.osrs_news_channel_id) or \
                  await self.bot.fetch_channel(self.osrs_news_channel_id)

        # Go through the last 100 messages
        async for message in channel.history(limit=100):
            if self.string_to_sweep in message.content:
                try:
                    await message.delete()
                except discord.Forbidden:
                    logger.error("[Message Janitor Cog] Missing permissions to delete messages.")
                    return
                except discord.HTTPException as e:
                    logger.error(f"[Message Janitor Cog] Failed to delete message: {e}")

    @tasks.loop(seconds=15)
    async def start_message_janitor(self) -> None:
        try:
            await self._delete_message()
        except Exception as e:
            logger.error(f"[Message Janitor Cog] Error when sweeping messages", exc_info=e)

    @start_message_janitor.before_loop
    async def before_message_janitor(self):
        await self.bot.wait_until_ready()
