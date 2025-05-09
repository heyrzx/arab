import logging
import asyncio
import os
from aiohttp import web, ClientSession
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = os.environ.get("PORT", "8080")

# Simple web server with keep-alive endpoint
async def create_web_server():
    app = web.Application()
    routes = web.RouteTableDef()
    
    @routes.get("/")
    async def home_handler(request):
        return web.Response(text="Bot is running!")
    
    @routes.get("/ping")
    async def ping_handler(request):
        return web.Response(text="pong")
    
    app.add_routes(routes)
    return app

# Keep alive function that periodically pings itself
async def keep_alive():
    app_url = os.environ.get("APP_URL", "written-salomi-trexaarb-ad0c8e0b.koyeb.app")  # Change this to your actual app URL
    ping_interval = 120  # 2 minutes
    
    logging.info(f"Starting keep-alive service, pinging every {ping_interval} seconds")
    
    while True:
        try:
            async with ClientSession() as session:
                ping_url = f"https://{app_url}/ping"
                async with session.get(ping_url, timeout=10) as response:
                    if response.status == 200:
                        logging.info("Keep-alive ping successful")
                    else:
                        logging.warning(f"Keep-alive ping returned status {response.status}")
        except Exception as e:
            logging.error(f"Keep-alive ping failed: {str(e)}")
            # Try to reconnect if connection fails
            await asyncio.sleep(30)  # Wait 30 seconds before retry
            continue
        
        await asyncio.sleep(ping_interval)

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
        try:
            await super().start()
            me = await self.get_me()
            self.username = '@' + me.username
            
            # Setup web server
            app = web.AppRunner(await create_web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            site = web.TCPSite(app, bind_address, PORT)
            await site.start()
            
            # Start keep-alive task
            asyncio.create_task(keep_alive())
            
            logging.info(f"Bot started as {me.first_name} ({self.username})")
            logging.info("Keep-alive service active, preventing host sleep...")
            print('Bot Started Powered By @VJ_Botz')
        except Exception as e:
            logging.error(f"Error in start method: {str(e)}")
            # Retry after a delay if there was an error
            await asyncio.sleep(10)
            await self.start()

    async def stop(self, *args):
        try:
            await super().stop()
            logging.info('Bot Stopped')
            print('Bot Stopped Bye')
        except Exception as e:
            logging.error(f"Error during shutdown: {str(e)}")

# Error handling for main execution
try:
    app = Bot()
    app.run()
except Exception as e:
    logging.critical(f"Fatal error in main execution: {str(e)}")
    # Wait and attempt to restart
    import time
    time.sleep(30)
    try:
        app = Bot()
        app.run()
    except Exception as restart_error:
        logging.critical(f"Failed to restart after error: {str(restart_error)}")
