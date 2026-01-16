import colorsys
import logging
from typing import Optional
import discord
from discord import app_commands
from src.main import BotClient
from src.cogs.BingoCog import BingoCog

logger = logging.getLogger(__name__)

async def bingo_setup(interaction: discord.Interaction, discord_bot: BotClient, sheet_id: str, channels: bool) -> None:
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    authorized_roles = ["General", "Captain", "Lieutenant"]
    authorized = await discord_bot.utils.check_user_roles(user=interaction.user, authorized_roles=authorized_roles)
    
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
        except Exception as e:
            await interaction.followup.send(f"Failed to load BingoCog: {e}", ephemeral=True)
            return

    await interaction.followup.send("Bingo setup loaded successfully.", ephemeral=True)


def register_bingo_commands(tree: app_commands.CommandTree, discord_bot: BotClient) -> None:
    @tree.command(name="bingo_setup", description="Sets up roles, team channels, and permissions for the bingo event")
    @app_commands.describe(sheet_id="The GDoc sheet ID for the event configuration",
                           channels="Flag for event text/voice channel creation. Defaults to False.")
    async def bingo_setup_cmd(interaction: discord.Interaction, sheet_id: str, channels: bool = False):
        logger.info("[Bingo Commands] /bingo_setup command called")
        await interaction.response.defer()
        await bingo_setup(interaction, discord_bot=discord_bot, sheet_id=sheet_id, channels=channels)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SHEET_ID = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
