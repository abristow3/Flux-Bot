import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
import discord
from discord.ext import tasks, commands

logger = logging.getLogger(__name__)


class SotwCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wom_base_url = "https://api.wiseoldman.net/v2"
        self.wom_group_id = 141
        self.flux_devs_channel_id = 1386683231289479241
        self.sotw_winner_role_id = 1570411127081537577
        self.sotw_title_keyword = "SOTW"
        self.storage_path = Path("data/sotw_competitions.json")
        self.competitions: dict[str, str] = {}
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self) -> None:
        try:
            self.competitions = self._load_competitions()
            self.session = aiohttp.ClientSession(headers={"User-Agent": "FluxBot"})
            self.start_sotw_check.start()
        except Exception as e:
            logger.error(f"[SOTW Cog] Failed to load SOTW Cog: {e}")
            return

    async def cog_unload(self) -> None:
        if self.start_sotw_check.is_running():
            self.start_sotw_check.stop()

        if self.session:
            await self.session.close()

    def _load_competitions(self) -> dict[str, str]:
        if not self.storage_path.exists():
            return {}

        with self.storage_path.open("r") as file:
            return json.load(file)

    def _save_competitions(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        with self.storage_path.open("w") as file:
            json.dump(self.competitions, file, indent=4)

    @staticmethod
    def _parse_time(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _normalize(name: str) -> str:
        return name.lower().replace("_", " ").replace("-", " ")

    async def _fetch_json(self, endpoint: str):
        async with self.session.get(f"{self.wom_base_url}{endpoint}") as response:
            response.raise_for_status()
            return await response.json()

    def _find_member(self, guild: discord.Guild, username: str) -> discord.Member | None:
        target = self._normalize(username)

        for member in guild.members:
            if target in self._normalize(member.display_name):
                return member

        return None

    async def _track_active_competitions(self) -> None:
        competitions = await self._fetch_json(f"/groups/{self.wom_group_id}/competitions")
        now = datetime.now(timezone.utc)

        for competition in competitions:
            comp_id = str(competition["id"])

            if self.sotw_title_keyword.lower() not in competition["title"].lower():
                continue

            starts_at = self._parse_time(competition["startsAt"])
            ends_at = self._parse_time(competition["endsAt"])

            # Only track active comps we haven't seen yet
            if starts_at <= now < ends_at and comp_id not in self.competitions:
                self.competitions[comp_id] = competition["endsAt"]
                self._save_competitions()
                logger.info(f"[SOTW Cog] Tracking competition {comp_id}: {competition['title']}")

    def _get_winner(self, competition: dict) -> str | None:
        comp_id = competition["id"]
        participations = competition.get("participations", [])

        if not participations:
            logger.info(f"[SOTW Cog] Competition {comp_id} had no participants.")
            return None

        top = max(participations, key=lambda p: p["progress"]["gained"])

        if top["progress"]["gained"] <= 0:
            logger.info(f"[SOTW Cog] Competition {comp_id} had no XP gained.")
            return None

        return top["player"]["displayName"]

    async def _process_competition(self, comp_id: str) -> bool:
        try:
            competition = await self._fetch_json(f"/competitions/{comp_id}")
            winner_name = self._get_winner(competition)

            if winner_name is None:
                return True

            guild = self.bot.get_guild(self.bot.guild_id)
            if guild is None:
                logger.error(f"[SOTW Cog] Could not find guild {self.bot.guild_id}.")
                return False

            member = self._find_member(guild, winner_name)

            # No match, so let the devs handle it manually
            if member is None:
                channel = self.bot.get_channel(self.flux_devs_channel_id) or \
                          await self.bot.fetch_channel(self.flux_devs_channel_id)

                await channel.send(
                    f"SOTW winner **{winner_name}** for **{competition['title']}** (ID: `{comp_id}`) "
                    f"could not be matched to a Discord member. Please assign the role manually."
                )
                return True

            role = guild.get_role(self.sotw_winner_role_id)
            if role is None:
                logger.error(f"[SOTW Cog] Could not find role {self.sotw_winner_role_id}.")
                return False

            if role not in member.roles:
                await member.add_roles(role, reason=f"Won SOTW competition {comp_id}")
                logger.info(f"[SOTW Cog] Assigned {role.name} to {member.display_name}.")

            return True

        except discord.Forbidden:
            logger.error("[SOTW Cog] Missing permissions to assign roles or send messages.")
            return False
        except Exception as e:
            logger.error(f"[SOTW Cog] Failed to process competition {comp_id}", exc_info=e)
            return False

    async def _process_ended_competitions(self) -> None:
        now = datetime.now(timezone.utc)

        for comp_id, ends_at in list(self.competitions.items()):
            if self._parse_time(ends_at) > now:
                continue

            # Only remove once fully processed, otherwise retry next run
            if await self._process_competition(comp_id):
                del self.competitions[comp_id]
                self._save_competitions()

    @tasks.loop(hours=24)
    async def start_sotw_check(self) -> None:
        try:
            await self._track_active_competitions()
            await self._process_ended_competitions()
        except Exception as e:
            logger.error(f"[SOTW Cog] Error when checking SOTW competitions", exc_info=e)

    @start_sotw_check.before_loop
    async def before_sotw_check(self):
        await self.bot.wait_until_ready()
        