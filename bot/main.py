import logging
from .app import bot_client

# 导入handlers模块以确保装饰器被执行
from . import handlers

LOGGER = logging.getLogger(__name__)

# 保持向后兼容的BotService类（如果其他地方还在使用）
class BotService:
    """A service class to manage the lifecycle of the main Telegram bot."""

    def __init__(self):
        self.bot = bot_client

    async def start(self):
        """Starts the main bot client."""
        LOGGER.info("Starting main bot client...")
        await self.bot.start()
        me = await self.bot.get_me()
        
        # 输出已注册的handlers数量用于调试
        handler_count = len(self.bot.dispatcher.groups)
        LOGGER.info(f"Bot '{me.first_name}' started successfully! Registered handler groups: {handler_count}")
        
        # 详细输出每个group的handlers数量
        for group_id, group in self.bot.dispatcher.groups.items():
            handler_count_in_group = len(group)
            LOGGER.info(f"Group {group_id}: {handler_count_in_group} handlers")

    async def stop(self):
        """Stops the main bot client."""
        if self.bot.is_initialized:
            LOGGER.info("Stopping main bot client...")
            await self.bot.stop()
            LOGGER.info("Main bot client stopped.")

# A single instance of the BotService for the entire application
bot_service = BotService()
