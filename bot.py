from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

from aiohttp import web
from os import environ
import asyncio

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
        
        # Create a simple web app with a health check endpoint
        app = web.Application()
        app.router.add_get('/', self.handle_home)
        app.router.add_get('/health', self.handle_health)
        
        # Start the web server
        app_runner = web.AppRunner(app)
        await app_runner.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app_runner, bind_address, PORT).start()
        
        # Start the keep alive task
        asyncio.create_task(self.keep_alive())
        
        print('Bot Started Powered By @VJ_Botz')

    async def handle_home(self, request):
        return web.Response(text=f"Bot {self.username} is running!")
        
    async def handle_health(self, request):
        return web.Response(text="Bot is alive!", status=200)
        
    async def keep_alive(self):
        """Send periodic requests to keep the bot alive"""
        while True:
            try:
                await asyncio.sleep(180)  # 3 minutes
                print("Keep-alive ping...")
            except Exception as e:
                print(f"Keep-alive error: {e}")

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')

Bot().run()
