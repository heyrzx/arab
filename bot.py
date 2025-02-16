from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

from aiohttp import web
from plugins import web_server
from os import environ

PORT = environ.get("PORT", "8080")

class Bot(Client):

    def __init__(self):
        super().__init__(
        "vj join request bot",
         api_id=API_ID,
         api_hash=API_HASH,
         bot_token=BOT_TOKEN,
         plugins=dict(root="plugins"),
         workers=50,
         sleep_threshold=10
        )

      
    async def start(self):
            
        await super().start()
        me = await self.get_me()
        self.username = '@' + me.username
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
            
        print('Bot Started Powered By @VJ_Botz')


    async def stop(self, *args):

        await super().stop()
        print('Bot Stopped Bye')

Bot().run()
