from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from config import OWNER_ID
from database.manager import get_all_active_users, deactivate_user
from user_clients.manager import user_client_manager
from ..app import bot_client
from ..app import bot_client

# Command Filters
admins_only = filters.private & filters.user(OWNER_ID)

@bot_client.on_message(filters.command("deluser") & admins_only)
async def deluser_command(client: Client, message: Message):
    """
    Deactivates a managed user and stops their client instance immediately.
    Usage: /deluser <user_id>
    """
    if len(message.command) < 2:
        await message.reply("Usage: /deluser <user_id>")
        return

    try:
        user_id_to_del = int(message.command[1])
        
        # 1. Stop the client instance if it's running
        stopped = await user_client_manager.stop_client(user_id_to_del)
        if stopped:
            await message.reply(f"✔️ Client for user `{user_id_to_del}` stopped successfully.")
        else:
            await message.reply(f"⚠️ Client for user `{user_id_to_del}` was not running.")

        # 2. Deactivate the user in the database
        if await deactivate_user(user_id_to_del):
            await message.reply(f"✅ User `{user_id_to_del}` has been deactivated in the database.")
        else:
            await message.reply(f"⚠️ Could not find user `{user_id_to_del}` in the database.")

    except ValueError:
        await message.reply("Invalid User ID provided. It must be an integer.")
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

@bot_client.on_message(filters.command("listusers") & admins_only)
async def listusers_command(client: Client, message: Message):
    """Lists all active managed users and their client status."""
    try:
        users = await get_all_active_users()
        if not users:
            await message.reply("No active users are configured in the database.")
            return

        response = "Managed Users (Active in DB):\n\n"
        for user in users:
            user_id = user['user_id']
            status = "✅ Running" if user_id in user_client_manager.running_clients else "❌ Stopped"
            response += f"- **User ID:** `{user_id}` | **Status:** {status}\n"
        
        await message.reply(response)
    except Exception as e:
        await message.reply(f"An error occurred: {e}")

# --- Message Handlers list is no longer needed ---

# manage_handlers = [
#     MessageHandler(deluser_command, filters.command("deluser") & admins_only),
#     MessageHandler(listusers_command, filters.command("listusers") & admins_only),
# ]
