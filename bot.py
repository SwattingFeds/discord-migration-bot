import os
import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("migration-bot")

TOKEN = os.getenv("DISCORD_TOKEN")
DESTINATION_INVITE_URL = os.getenv("DESTINATION_INVITE_URL", "").strip()
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID", "0") or 0)
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0") or 0)

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")
if not DESTINATION_INVITE_URL.startswith(("https://discord.gg/", "https://discord.com/invite/")):
    raise RuntimeError("Set DESTINATION_INVITE_URL to a valid Discord invite URL.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Lightweight runtime counters. These reset when the Render worker restarts.
stats = {"invite_requests": 0, "announcements": 0, "started_at": None}


def is_admin(interaction: discord.Interaction) -> bool:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    return bool(ADMIN_ROLE_ID and any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles))


@bot.event
async def on_ready():
    if stats["started_at"] is None:
        stats["started_at"] = datetime.now(timezone.utc)
    try:
        synced = await bot.tree.sync()
        log.info("Logged in as %s; synced %d slash commands", bot.user, len(synced))
    except Exception:
        log.exception("Slash command sync failed")
    log.info("Bot is ready.")


@bot.tree.command(name="invite", description="Get the invite link for the new server.")
async def invite(interaction: discord.Interaction):
    stats["invite_requests"] += 1
    await interaction.response.send_message(
        f"You're welcome to join the new server here: {DESTINATION_INVITE_URL}",
        ephemeral=True,
    )


@bot.tree.command(name="dmoptin", description="Ask the bot to DM you the new server invite.")
async def dmoptin(interaction: discord.Interaction):
    # This sends a DM only to the member who invoked the command.
    try:
        await interaction.user.send(
            f"Here is the invite you requested: {DESTINATION_INVITE_URL}"
        )
        stats["invite_requests"] += 1
        await interaction.response.send_message(
            "I sent you the invite in a DM.", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "I couldn't DM you. Check your server privacy settings, then use /invite instead.",
            ephemeral=True,
        )


@bot.tree.command(name="announce", description="Post a server-move announcement.")
@app_commands.describe(message="The announcement text to post")
async def announce(interaction: discord.Interaction, message: str):
    if not is_admin(interaction):
        await interaction.response.send_message(
            "Only server administrators (or the configured admin role) can use this command.",
            ephemeral=True,
        )
        return

    if not ANNOUNCEMENT_CHANNEL_ID:
        await interaction.response.send_message(
            "Set ANNOUNCEMENT_CHANNEL_ID in Render environment variables first.",
            ephemeral=True,
        )
        return

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(ANNOUNCEMENT_CHANNEL_ID)
        except discord.HTTPException:
            channel = None

    if channel is None or not hasattr(channel, "send"):
        await interaction.response.send_message(
            "I couldn't find the configured announcement channel.",
            ephemeral=True,
        )
        return

    safe_message = message[:1500]
    await channel.send(
        f"{safe_message}\n\nIf you'd like to join, use this invite: {DESTINATION_INVITE_URL}",
        allowed_mentions=discord.AllowedMentions.none(),
    )
    stats["announcements"] += 1
    await interaction.response.send_message("Announcement posted.", ephemeral=True)


@bot.tree.command(name="stats", description="Show migration invite-request statistics.")
async def migration_stats(interaction: discord.Interaction):
    started = stats["started_at"]
    started_text = started.strftime("%Y-%m-%d %H:%M UTC") if started else "starting"
    await interaction.response.send_message(
        f"**Migration bot stats**\n"
        f"Invite requests since this worker started: **{stats['invite_requests']}**\n"
        f"Announcements posted: **{stats['announcements']}**\n"
        f"Worker started: **{started_text}**",
        ephemeral=True,
    )


bot.run(TOKEN)
