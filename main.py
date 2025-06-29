import asyncio
import logging
import signal
from pyrogram import idle
import uvloop
from logging.handlers import TimedRotatingFileHandler
from bot.main import bot_service
from user_clients.manager import user_client_manager
from database.manager import db_client
from config import LOG_LEVEL

# Setup logging with rotation
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file = "logs/app.log"

# Use TimedRotatingFileHandler to rotate logs daily and keep 3 days of backups
file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=3
)
file_handler.setFormatter(log_formatter)

# Also log to console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

# Configure root logger with log level from environment variable
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

logging.getLogger("pyrogram").setLevel(logging.INFO)  # Reduce pyrogram's verbosity
LOGGER = logging.getLogger(__name__)

# Log the current log level being used
LOGGER.info(f"Application starting with log level: {LOG_LEVEL}")

async def main():
    """
    The main function to initialize and start all services concurrently.
    """
    LOGGER.info("Starting application and services...")
    
    try:
        # Using asyncio.gather to run bot and user clients concurrently
        await asyncio.gather(
            bot_service.start(),
            user_client_manager.start_all_from_db()
        )
        LOGGER.info("All services are running. Press Ctrl+C to stop.")
        # Keep the main coroutine alive to handle signals
        await idle()
    except asyncio.CancelledError:
        LOGGER.info("Main task cancelled during shutdown.")
    except Exception as e:
        LOGGER.error(f"An error occurred during startup or runtime: {e}", exc_info=True)


async def shutdown(sig):
    """
    Handles graceful shutdown of the application.
    """
    LOGGER.info(f"Received exit signal {sig.name}... Shutting down.")

    current_task = asyncio.current_task()
    tasks = [task for task in asyncio.all_tasks() if task is not current_task]

    if tasks:
        LOGGER.info(f"Cancelling {len(tasks)} outstanding tasks...")
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        LOGGER.info("All outstanding tasks have been cancelled.")

    LOGGER.info("Stopping user clients...")
    await user_client_manager.stop_all()

    LOGGER.info("Stopping bot...")
    await bot_service.stop()

    LOGGER.info("Closing database connection...")
    db_client.close()

    LOGGER.info("Shutdown complete.")

    # Gracefully stop the event loop
    # loop = asyncio.get_running_loop()
    # if loop.is_running():
    #     loop.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    try:
        LOGGER.info("Application starting up.")
        uvloop.install()
        loop.run_until_complete(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        LOGGER.info("Application shutdown request received.")
    finally:
        LOGGER.info("Event loop stopped. Cleaning up...")
        tasks = asyncio.all_tasks(loop=loop)
        if tasks:
            LOGGER.info(f"Waiting for {len(tasks)} tasks to complete...")
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        if not loop.is_closed():
            loop.close()
        LOGGER.info("Application shut down gracefully.")
