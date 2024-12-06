from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
import asyncio
import discord
from api import match_events_to_games_ev, match_live_events_to_games_ev, match_events_to_games_arb

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

intents: Intents = Intents.default()
client: Client = Client(intents=intents)
PREMATCH_CHANNEL_ID = 1314304239350055012
LIVE_CHANNEL_ID = 1314304272338255872
ARBS_CHANNEL_ID = 1314688996143665192

# Makes Sure We Don't Query for Already Sent Bets
seen_bets = set()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    prematch_ev_channel = client.get_channel(PREMATCH_CHANNEL_ID)
    live_ev_channel = client.get_channel(LIVE_CHANNEL_ID)
    arbs_channel = client.get_channel(ARBS_CHANNEL_ID)

    # Start dynamic polling
    await asyncio.gather(
        arbs_dynamic_poll(arbs_channel),
        live_ev_dynamic_poll(live_ev_channel),
        prematch_ev_dynamic_poll(prematch_ev_channel)
    )


async def arbs_dynamic_poll(channel, initial_interval=10, max_interval=200, interval_step=5):
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
            all_messages = match_events_to_games_arb()

            # Filter for new messages
            new_messages = [
                message for message in all_messages
                if message['outcome_id'] not in seen_bets
            ]

            if new_messages:
                # Send all new messages
                for message in new_messages:
                    embed_message = create_arb_message(message)
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


async def live_ev_dynamic_poll(channel, initial_interval=10, max_interval=1000, interval_step=10):
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
            all_messages = match_live_events_to_games_ev()

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


async def prematch_ev_dynamic_poll(channel, initial_interval=20, max_interval=120, interval_step=10):
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
    embed.add_field(name="EV", value=message['ev'], inline=False)
    embed.set_footer(text=message['datetime'])

    return embed


def create_arb_message(message: dict) -> discord.Embed:
    """
    Placeholder for creating arb messages (needs fixing).

    Args:
        message: The bet details as a dictionary.

    Returns:
        A Discord embed object.
    """
    embed = discord.Embed(
        colour=discord.Colour.dark_teal(),
        description=message['bet_line'],
        title=message['game_name'],
    )
    # NEED TO FIX THIS
    embed.add_field(
        name=message['side1']['bet_info'],
        value=f"[Link]({message['side1']['deeplink']})",
        inline=False
    )
    embed.add_field(
        name=message['side2']['bet_info'],
        value=f"[Link]({message['side2']['deeplink']})",
        inline=False
    )

    embed.set_footer(text=message['datetime'])
    return embed


# Run the bot
client.run(TOKEN)
