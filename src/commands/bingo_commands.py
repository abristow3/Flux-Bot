from datetime import datetime, timedelta
import pytz
import discord
from discord.ext import tasks
from discord import app_commands
import logging

logger = logging.getLogger(__name__)
UTC = pytz.utc
US_EASTERN = pytz.timezone("US/Eastern")
GMT = pytz.timezone("GMT")

config = {
    "BINGO_START_DATE": "23/01/2026",
    "BINGO_START_TIME_GMT": "14:00",
    "BINGO_END_DATE": "26/01/2026",
    "BINGO_END_TIME_GMT": "14:00",
    "SIGNUP_END_DATE": "18/01/2026",
    "SIGNUP_END_TIME_GMT": "14:00",
    "REMINDER_START_24HR": "@Bingo Bingo starts in 24 hours, please make sure you've read all the rules carefully.",
    "REMINDER_END_24HR": "@Bingo 24 hours left in the bingo!",
    "REMINDER_SIGNUP_24HR": "Bingo sign-ups close in 24 hours, last chance to sign up, make sure you've paid your buy-ins!",
    "EVENTS_CHANNEL_ID": 1452696803706408980,
    "START_MESSAGE": "@Bingo! Bingo starts now!",
    "END_MESSAGE": "@Bingo! Bingo is now over."
}


# Build timezone-aware datetime objects, including start/end message reminders
def build_bingo_datetimes(config):
    bingo_start_dt = GMT.localize(datetime.strptime(
        f"{config['BINGO_START_DATE']} {config['BINGO_START_TIME_GMT']}",
        "%d/%m/%Y %H:%M"
    ))

    bingo_end_dt = GMT.localize(datetime.strptime(
        f"{config['BINGO_END_DATE']} {config['BINGO_END_TIME_GMT']}",
        "%d/%m/%Y %H:%M"
    ))

    signup_end_dt = GMT.localize(datetime.strptime(
        f"{config['SIGNUP_END_DATE']} {config['SIGNUP_END_TIME_GMT']}",
        "%d/%m/%Y %H:%M"
    ))

    reminders = {
        # 24hr reminders
        "reminder_bingo_start": (bingo_start_dt - timedelta(days=1), config["REMINDER_START_24HR"]),
        "reminder_bingo_end": (bingo_end_dt - timedelta(days=1), config["REMINDER_END_24HR"]),
        "reminder_signup_end": (signup_end_dt - timedelta(days=1), config["REMINDER_SIGNUP_24HR"]),
        # Exact start/end messages
        "bingo_start_message": (bingo_start_dt, config["START_MESSAGE"]),
        "bingo_end_message": (bingo_end_dt, config["END_MESSAGE"])
    }

    return {
        "bingo_start_dt": bingo_start_dt,
        "bingo_end_dt": bingo_end_dt,
        "signup_end_dt": signup_end_dt,
        "reminders": reminders
    }


# Format a datetime in both GMT and US Eastern
def format_datetime_both_timezones(dt_gmt):
    dt_eastern = dt_gmt.astimezone(US_EASTERN)
    return dt_gmt.strftime("%d/%m/%Y %H:%M %Z"), dt_eastern.strftime("%d/%m/%Y %H:%M %Z")


# Main setup command
async def bingo_setup(interaction: discord.Interaction, discord_bot) -> None:
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    authorized_roles = ["General", "Captain", "Lieutenant"]
    authorized = await discord_bot.utils.check_user_roles(interaction.user, authorized_roles)

    if not authorized:
        await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
        return

    # Build the datetimes
    bingo_times = build_bingo_datetimes(config)

    # Print reminders (for verification)
    for key, value in bingo_times["reminders"].items():
        dt_gmt, msg = value
        gmt_str, eastern_str = format_datetime_both_timezones(dt_gmt)
        print(f"{key}:\n  GMT: {gmt_str}\n  US Eastern: {eastern_str}\n  Message: {msg}\n")

    # Start the reminder loop
    if not bingo_reminder_loop.is_running():
        bingo_reminder_loop.start(bingo_times, discord_bot)

    # Send ephemeral follow-up to the user confirming the loop has started
    await interaction.followup.send(
        "✅ Bingo reminder loop has been started. All reminders are scheduled.",
        ephemeral=True
    )


# Task loop to send reminders at the right time (includes start/end messages)
@tasks.loop(seconds=20)
async def bingo_reminder_loop(bingo_times, discord_bot):
    logger.info("[Bingo Loop] beep")
    now = datetime.now(GMT)
    channel = discord_bot.get_channel(config["EVENTS_CHANNEL_ID"])
    if not channel:
        logger.warning("Events channel not found")
        return

    for key, value in list(bingo_times["reminders"].items()):
        dt_gmt, msg = value
        if now >= dt_gmt:
            gmt_str, eastern_str = format_datetime_both_timezones(dt_gmt)
            if key in ["bingo_start_message", "bingo_end_message"]:
                message = f"{msg}\n**Time:** GMT {gmt_str} / US Eastern {eastern_str}"
            else:
                message = f"{msg}\n**Reminder Time:** GMT {gmt_str} / US Eastern {eastern_str}"

            await channel.send(message)
            logger.info(f"Sent reminder: {key}")
            del bingo_times["reminders"][key]

    # Stop the loop if no reminders remain
    if not bingo_times["reminders"]:
        logger.info("All reminders sent. Stopping reminder loop.")
        bingo_reminder_loop.stop()


# Register the command
def register_bingo_commands(tree: app_commands.CommandTree, discord_bot) -> None:
    @tree.command(name="bingo_setup", description="Sets up announcement messages for the bingo event.")
    async def bingo_setup_cmd(interaction: discord.Interaction):
        logger.info("[Bingo Commands] /bingo_setup command called")
        await interaction.response.defer()
        await bingo_setup(interaction, discord_bot=discord_bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SHEET_ID = "1EMxj1y49C31AU2LXXEdpM2tyVUqOfqABH7TVAu3Fcqk"
