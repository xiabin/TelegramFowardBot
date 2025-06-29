import asyncio
import logging
from pyrogram import Client
from config import API_ID, API_HASH, PROXY
from user_clients.handlers import register_handlers

logger = logging.getLogger(__name__)


class UserClientManager:
    """
    Manages the lifecycle of multiple Pyrogram user clients.
    Allows for dynamic starting and stopping of clients without a full restart.
    """

    def __init__(self):
        self.running_clients = {}  # {user_id: client_instance}

    async def start_client(self, user_id: int, session_string: str) -> bool:
        """
        Initializes, starts, and manages a single user client.
        If the client is already running, it will be restarted.
        """
        if user_id in self.running_clients:
            logger.info(f"Client for user {user_id} is already running. Restarting...")
            await self.stop_client(user_id)

        logger.info(f"Starting client for user {user_id}...")
        try:
            client_params = {
                "name": f"user_{user_id}",
                "api_id": API_ID,
                "api_hash": API_HASH,
                "session_string": session_string,
                "in_memory": True,
            }
            if PROXY:
                client_params["proxy"] = PROXY
                
            client = Client(**client_params)
            
            await client.start()
            register_handlers(client)

            me = await client.get_me()
            logger.info(f"Client for user {me.first_name} ({me.id}) started successfully.")

            self.running_clients[user_id] = client
            return True

        except Exception as e:
            logger.error(f"Failed to start client for user {user_id}. Error: {e}", exc_info=True)
            return False

    async def stop_client(self, user_id: int) -> bool:
        """Stops a specific running user client."""
        if user_id not in self.running_clients:
            logger.warning(f"Attempted to stop a non-running client for user {user_id}.")
            return False

        logger.info(f"Stopping client for user {user_id}...")
        client = self.running_clients.pop(user_id)
        
        if client.is_initialized:
            await client.stop()
        
        logger.info(f"Client for user {user_id} stopped.")
        return True

    async def start_all_from_db(self):
        """
        Loads all active users from the database and starts their clients.
        To be called on application startup.
        """
        from database.manager import get_all_active_users  # Local import
        
        logger.info("Starting all active user clients from database...")
        active_users = await get_all_active_users()
        if not active_users:
            logger.info("No active users found in the database.")
            return

        for user in active_users:
            await self.start_client(user['user_id'], user['session_string'])

    async def stop_all(self):
        """Stops all running user clients gracefully."""
        logger.info("Stopping all user clients...")
        user_ids = list(self.running_clients.keys())
        for user_id in user_ids:
            await self.stop_client(user_id)
        logger.info("All user clients have been stopped.")

# A single instance of the manager to be used throughout the application
user_client_manager = UserClientManager()
