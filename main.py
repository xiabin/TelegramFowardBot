import asyncio
import logging
import signal
import uvloop
from logging.handlers import TimedRotatingFileHandler
from bot.main import bot_service
from user_clients.manager import user_client_manager
from database.manager import db_client

uvloop.install()

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

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

logging.getLogger("pyrogram").setLevel(logging.WARNING)  # Reduce pyrogram's verbosity
LOGGER = logging.getLogger(__name__)


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
        await asyncio.Event().wait()
    except Exception as e:
        LOGGER.error(f"An error occurred during startup or runtime: {e}", exc_info=True)


async def shutdown(sig):
    """
    Handles graceful shutdown of the application.
    """
    LOGGER.info(f"Received exit signal {sig.name}... Shutting down.")

    # Create a shutdown task to prevent it from being cancelled
    shutdown_task = asyncio.create_task(_perform_shutdown())

    # Wait for the shutdown to complete
    await shutdown_task


async def _perform_shutdown():
    """Helper function to perform the actual shutdown operations."""
    LOGGER.info("Stopping user clients...")
    await user_client_manager.stop_all()

    LOGGER.info("Stopping bot...")
    await bot_service.stop()

    LOGGER.info("Closing database connection...")
    db_client.close()

    LOGGER.info("Shutdown complete.")
    
    # Gracefully stop the event loop
    loop = asyncio.get_running_loop()
    loop.stop()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    try:
        LOGGER.info("Application starting up.")
        asyncio.run(main())
        loop.run_forever()  # Run the event loop until stop() is called
    finally:
        LOGGER.info("Event loop stopped. Cleaning up...")
        # Ensure all tasks are cancelled before closing the loop
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        
        # Gather all tasks to allow them to process cancellation
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        LOGGER.info("Application shut down gracefully.")
