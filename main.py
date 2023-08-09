import asyncio
import datetime
import os

import aiohttp
import discord
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from discord import Intents
import a2s

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

# CONFIGURATION
CONFIG = {
    'BOT_TOKEN': os.environ['BOT_TOKEN'],
    'SERVER_GUID': os.environ['SERVER_GUID'],
    'GAME': os.environ.get('GAME', 'BF4')
}

# CONSTANTS
BF4_BFH_URL = "https://keeper.battlelog.com/snapshot/{server_guid}"
BF3_URL = "https://battlelog.battlefield.com/bf3/servers/show/pc/{server_guid}?json=1&join=false"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class LivePlayercountBot(discord.Client):
    """Discord bot to display the BL true playercount in the bot status"""

    async def on_ready(self):
        print(
            f"Logged on as {self.user}\nStarted monitoring server {CONFIG['SERVER_GUID']}")
        status = ""
        async with aiohttp.ClientSession() as session:
            while True:
                newstatus = await get_playercount(session)
                if newstatus != status:  # avoid spamming the discord API
                    await self.change_presence(activity=discord.Game(newstatus))
                    status = newstatus
                await asyncio.sleep(10)


async def get_playercount(session):
    game = CONFIG['GAME']
    server_guid = CONFIG['SERVER_GUID']

    if game in GAME_HANDLERS:
        return await GAME_HANDLERS[game](session, server_guid)
    else:
        raise Exception(f"Unsupported Game: {game}")


async def handle_bf4_bfh(session, server_guid):
    url = BF4_BFH_URL.format(server_guid=server_guid)
    async with session.get(url, headers=headers) as response:
        if response.status < 200 or response.status >= 300:
            print(
                f"Error: Received status code {response.status} when fetching {url}")
            return "Error fetching data"

        data = await response.json()
        playercount = sum(len(data["snapshot"]["teamInfo"][str(
            n)]["players"]) for n in range(len(data["snapshot"]["teamInfo"])))
        max_slots = data["snapshot"]["maxPlayers"]
        return f"{playercount}/{max_slots}"


async def handle_bf3(session, server_guid):
    url = BF3_URL.format(server_guid=server_guid)
    async with session.get(url, headers=headers) as response:
        if response.status < 200 or response.status >= 300:
            print(
                f"Error: Received status code {response.status} when fetching {url}")
            return "Error fetching data"

        data = await response.json()
        max_slots = data["message"]["SERVER_INFO"]["slots"]["2"]["max"]
        playercount = len(data["message"]["SERVER_PLAYERS"])
        return f"{playercount}/{max_slots}"


async def handle_gametracker(session, server_guid):
    async with session.get(server_guid, headers=headers) as response:
        if response.status < 200 or response.status >= 300:
            print(
                f"Error: Received status code {response.status} when fetching {server_guid}")
            return "Error fetching data"

        page = await response.text()
        soup = BeautifulSoup(page, "html.parser")

        num_players_element = soup.find(id="HTML_num_players")
        max_players_element = soup.find(id="HTML_max_players")

        # Check if the elements were found
        if num_players_element is None or max_players_element is None:
            print(
                f"Error: Unable to find the required elements on the page {server_guid}")
            return "Error fetching data"

        num_players = num_players_element.text
        max_players = max_players_element.text
        return f"{num_players}/{max_players}"


async def handle_source_server(_, server_guid):
    # Extract IP and port from the server_guid
    ip, port = server_guid.split(":")
    port = int(port)

    try:
        # Query the server
        address = (ip, port)
        info = a2s.info(address)

        # Extract player count and max players
        num_players = info.player_count
        max_players = info.max_players
        return f"{num_players}/{max_players}"

    except Exception as e:
        print(f"Error querying SOURCE server: {e}")
        return "Error fetching data"

GAME_HANDLERS = {
    'BF4': handle_bf4_bfh,
    'BFH': handle_bf4_bfh,
    'BF3': handle_bf3,
    'GAMETRACKER': handle_gametracker,
    'SOURCE': handle_source_server
}

intents = Intents.default()

if __name__ == "__main__":
    assert CONFIG['SERVER_GUID'] and CONFIG['BOT_TOKEN'] and CONFIG['GAME'], "Config is empty, please fix"
    print("Initiating bot")
    LivePlayercountBot(intents=intents).run(CONFIG['BOT_TOKEN'])
