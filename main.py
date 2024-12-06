from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
import asyncio
import discord
from api import match_events_to_games

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
print(TOKEN)

intents : Intents = Intents.default()

client : Client = Client(intents=intents)
CHANNEL_ID = 1314270624541315183

#Makes Sure We Don't Query for Already Sent Bets
seen_bets = set()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("Channel not found! Check the CHANNEL_ID.")
        return

    while True:
        try:
            all_messages = match_events_to_games()
            for message in all_messages:
                embed_message = create_ev_message(message)
                await channel.send(embed=embed_message)
                await asyncio.sleep(5)  # Wait 5 seconds before sending the next message (TEMPORARY PLACEHOLDER)
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(15)

def create_ev_message(message: dict) -> discord.Embed:
    embed = discord.Embed(
        title=message['game_name'],
        description=f"[{message['bet_line']}]({message['deeplink']})",
        colour=discord.Colour.dark_teal()
    )
    embed.add_field(name="Book", value=message['book'], inline=False)
    embed.add_field(name="EV", value=f"{message['ev'] * 100}%", inline=False)
    embed.set_footer(text='PLACEHOLDER')
    
    return embed

def create_arb_message(event: str, bet_type: str, line1 : str, line2 : str, url1: str, url2 : str, datetime : str):
    message = discord.Embed(
        colour=discord.Colour.dark_teal(),
        description=bet_type,
        title=event,
    )
    #NEED TO FIX THIS
    message.add_field(name=line1, value=line1, inline=False)
    message.add_field(name=line2, value=line2, inline=False)
    message.set_footer(text=datetime)
    return message

# Run the bot
client.run(TOKEN)

