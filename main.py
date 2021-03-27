import asyncio
import datetime
import os
import sys

import aiohttp
import discord

# CONFIG
BOT_TOKEN = os.environ['BOT_TOKEN']
SERVER_GUID = os.environ['SERVER_GUID']
GAME = os.environ['GAME'] or 'BF4'


class LivePlayercountBot(discord.Client):
    """Discord bot to display the BL true playercount in the bot status"""

    async def on_ready(self):
        print(f"Logged on as {self.user}\n" f"Started monitoring server {SERVER_GUID}")
        status = ""
        async with aiohttp.ClientSession() as session:
            while True:
                newstatus = await get_playercount(session)
                if newstatus != status:  # avoid spam to the discord API
                    await self.change_presence(activity=discord.Game(newstatus))
                    status = newstatus
                await asyncio.sleep(10)


async def get_playercount(session):
    try:
        x = datetime.datetime.now()
        if GAME == 'BF4' or GAME == 'BFH':
            url = f"https://keeper.battlelog.com/snapshot/{SERVER_GUID}"
            async with session.get(url) as r:
                page = await r.json()
                true_playercount = 0
                for n in range(len(page["snapshot"]["teamInfo"])):
                    true_playercount += len(page["snapshot"]["teamInfo"][str(n)]["players"])
                max_slots = page["snapshot"]["maxPlayers"]
                print('[' + x.strftime("%X") + '] Player Count: ' + f"{true_playercount}/{max_slots}")
                return f"{true_playercount}/{max_slots}"  # discord status message
        elif GAME == 'BF3':
            url = f"https://battlelog.battlefield.com/bf3/servers/show/pc/{SERVER_GUID}?json=1&join=false"
            async with session.get(url) as r:
                page = await r.json()
                max_slots = page["message"]["SERVER_INFO"]["slots"]["2"]["max"]
                true_playercount = len(page["message"]["SERVER_PLAYERS"])
                print('[' + x.strftime("%X") + '] Player Count: ' + f"{true_playercount}/{max_slots}")
                return f"{true_playercount}/{max_slots}"  # discord status message
        elif GAME == 'BC2' or GAME == 'GAMETRACKER':
            async with session.get(SERVER_GUID) as r:
                page = await r.text()
                # isolate playercount value
                page = page.split('"HTML_num_players">')[1].split('</span>\n\t\t\t<br/>\n\t\t\t')[0]
                playercount = page.replace('</span> / <span id="HTML_max_players">', '/')
                print('[' + x.strftime("%X") + '] Player Count: ' + playercount)
                return playercount  # discord status message
        else:
            raise Exception("Unsupported Game")

    except Exception as e:
        print(f"Error getting data: {e}")  # BL autism


if __name__ == "__main__":
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+"
    assert SERVER_GUID and BOT_TOKEN and GAME, "Config is empty, pls fix"
    print("Initiating bot")
    LivePlayercountBot().run(BOT_TOKEN)
