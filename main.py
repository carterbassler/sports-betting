from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
import asyncio
import discord
from api import match_events_to_games_ev

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
print(TOKEN)

intents: Intents = Intents.default()
client: Client = Client(intents=intents)
CHANNEL_ID = 1314304239350055012

# Makes Sure We Don't Query for Already Sent Bets
seen_bets = set()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("Channel not found! Check the CHANNEL_ID.")
        return

    # Start dynamic polling
    await dynamic_poll(channel)


async def dynamic_poll(channel, initial_interval=20, max_interval=120, interval_step=10):
    """
    Polls the API dynamically, adjusting the interval based on activity.

    Args:
        channel: The Discord channel to send messages.
        initial_interval: Initial polling interval in seconds.
        max_interval: Maximum interval to back off to in seconds.
        interval_step: Step to increase interval on no activity.
    """
    interval = initial_interval

    while True:
        try:
            # Fetch all messages from the API
            all_messages = match_events_to_games_ev()
            
            # Filter for new messages
            new_messages = [
                message for message in all_messages
                if message['outcome_id'] not in seen_bets
            ]
            
            if new_messages:
                # Send all new messages
                for message in new_messages:
                    embed_message = create_ev_message(message)
                    await channel.send(embed=embed_message)
                    # Mark as seen
                    seen_bets.add(message['outcome_id'])
                
                # Reset the interval to be more responsive
                interval = initial_interval
            else:
                # Increase the interval for less frequent polling
                interval = min(interval + interval_step, max_interval)

        except Exception as e:
            print(f"An error occurred: {e}")
            # Back off in case of an error
            interval = max_interval

        print(f"Next poll in {interval} seconds.")
        await asyncio.sleep(interval)


def create_ev_message(message: dict) -> discord.Embed:
    """
    Creates a Discord embed message for EV bets.

    Args:
        message: The bet details as a dictionary.

    Returns:
        A Discord embed object.
    """
    embed = discord.Embed(
        title=message['game_name'],
        description=f"[{message['bet_line']}]({message['deeplink']})",
        colour=discord.Colour.dark_teal()
    )
    embed.add_field(name="Book", value=message['book'], inline=False)
    embed.add_field(name="EV", value=f"{message['ev'] * 100}%", inline=False)
    embed.set_footer(text='PLACEHOLDER')
    
    return embed


def create_arb_message(message: dict) -> discord.Embed:
    """
    Placeholder for creating arb messages (needs fixing).

    Args:
        message: The bet details as a dictionary.

    Returns:
        A Discord embed object.
    """
    message = discord.Embed(
        colour=discord.Colour.dark_teal(),
        description=bet_type,
        title=event,
    )
    # NEED TO FIX THIS
    message.add_field(name=line1, value=line1, inline=False)
    message.add_field(name=line2, value=line2, inline=False)
    message.set_footer(text=datetime)
    return message


# Run the bot
client.run(TOKEN)
