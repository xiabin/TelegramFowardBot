import logging
from .app import bot_client

LOGGER = logging.getLogger(__name__)

class BotService:
    """A service class to manage the lifecycle of the main Telegram bot."""

    def __init__(self):
        self.bot = bot_client

    async def start(self):
        """Starts the main bot client."""
        LOGGER.info("Starting main bot client...")
        await self.bot.start()
        me = await self.bot.get_me()
        LOGGER.info(f"Bot '{me.first_name}' started successfully!")

    async def stop(self):
        """Stops the main bot client."""
        if self.bot.is_initialized:
            LOGGER.info("Stopping main bot client...")
            await self.bot.stop()
            LOGGER.info("Main bot client stopped.")

# A single instance of the BotService for the entire application
bot_service = BotService()
