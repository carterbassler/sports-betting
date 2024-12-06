import discord
from discord.ext import commands
from typing import Final
import os
import sys

# Prompt for user input for the channel ID
if len(sys.argv) < 2:
    print("Usage: python script.py <channel_id>")
    sys.exit(1)

channel_id = int(sys.argv[1])

# Replace 'your_token_here' with your Discord bot token
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# Intents are required to interact with Discord channels
intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found.")
        await bot.close()
        return

    print(f"Clearing messages in channel: {channel.name} ({channel_id})")

    try:
        deleted = await channel.purge(limit=None)
        print(f"Deleted {len(deleted)} messages.")
    except Exception as e:
        print(f"Failed to clear messages: {e}")

    await bot.close()

bot.run(TOKEN)
