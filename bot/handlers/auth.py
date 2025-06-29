import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.errors import (
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
)
from config import API_ID, API_HASH, OWNER_ID
from database.manager import add_managed_user
from user_clients.manager import user_client_manager
from ..app import bot_client

logger = logging.getLogger(__name__)

# In-memory dictionary to store conversation state for adding users
user_auth_sessions = {}

# Custom filter for the owner
owner_only = filters.private 

@bot_client.on_message(filters.command("adduser") & owner_only)
async def adduser_command(client: Client, message: Message):
    """Starts the process of adding a new managed user."""
    logger.info(f"Received /adduser command from owner {message.from_user.id}")
    
    admin_id = message.from_user.id
    if admin_id in user_auth_sessions:
        await message.reply("You are already in the middle of an add-user process. Send /cancel to stop.")
        return

    user_auth_sessions[admin_id] = {"step": "phone"}
    await message.reply(
        "Starting the process to add a new managed user...\n\n"
        "**Step 1:** Please provide the phone number for the account (e.g., +1234567890).\n\n"
        "Send /cancel at any time to stop."
    )

@bot_client.on_message(filters.command("cancel") & owner_only)
async def cancel_command(client: Client, message: Message):
    """Cancels the current operation."""
    admin_id = message.from_user.id
    if admin_id in user_auth_sessions:
        session_data = user_auth_sessions.pop(admin_id)
        temp_client = session_data.get("client")
        if temp_client and temp_client.is_connected:
            await temp_client.disconnect()
        await message.reply("Operation cancelled.")
    else:
        await message.reply("No active operation to cancel.")

@bot_client.on_message(filters.text & ~filters.command(["adduser", "cancel"]) & owner_only)
async def conversation_handler(client: Client, message: Message):
    """Handles the conversation for adding a user."""
    admin_id = message.from_user.id
    if admin_id not in user_auth_sessions:
        return

    session_data = user_auth_sessions[admin_id]
    step = session_data.get("step")

    try:
        if step == "phone":
            await process_phone_step(message, session_data)
        elif step == "code":
            await process_code_step(message, session_data)
        elif step == "password":
            await process_password_step(message, session_data)
    except Exception as e:
        logger.error(f"Error during user add process for admin {admin_id}: {e}", exc_info=True)
        await message.reply(f"An unexpected error occurred: {e}.\nPlease try again or /cancel.")
        user_auth_sessions.pop(admin_id, None)

async def process_phone_step(message: Message, session_data: dict):
    phone_number = message.text
    temp_client = Client(f"temp_{message.from_user.id}", API_ID, API_HASH, in_memory=True)
    await temp_client.connect()
    
    sent_code = await temp_client.send_code(phone_number)
    
    session_data.update({
        "step": "code",
        "phone": phone_number,
        "phone_code_hash": sent_code.phone_code_hash,
        "client": temp_client
    })
    await message.reply("**Step 2:** Verification code sent. Please provide the code.")

async def process_code_step(message: Message, session_data: dict):
    code = message.text
    temp_client = session_data["client"]
    try:
        await temp_client.sign_in(session_data["phone"], session_data["phone_code_hash"], code)
        await finalize_session(message, session_data)
    except SessionPasswordNeeded:
        session_data["step"] = "password"
        await message.reply("**Step 3:** Two-step verification is enabled. Please provide your password.")
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await message.reply("Invalid or expired code. Please try again or send /cancel.")

async def process_password_step(message: Message, session_data: dict):
    password = message.text
    temp_client = session_data["client"]
    try:
        await temp_client.check_password(password)
        await finalize_session(message, session_data)
    except PasswordHashInvalid:
        await message.reply("Invalid password. Please try again or send /cancel.")

async def finalize_session(message: Message, session_data: dict):
    """Finalizes the session, saves it, and starts the client immediately."""
    temp_client = session_data["client"]
    session_string = await temp_client.export_session_string()
    new_user_me = await temp_client.get_me()
    
    await temp_client.disconnect()
    
    # 1. Save the user to the database
    await add_managed_user(new_user_me.id, session_string)
    await message.reply(f"✅ User `{new_user_me.id}` ({new_user_me.first_name}) saved to database.")

    # 2. Start the user client instance immediately
    await message.reply(f"🚀 Starting client for `{new_user_me.id}`...")
    success = await user_client_manager.start_client(new_user_me.id, session_string)

    if success:
        await message.reply(f"✅ Client for `{new_user_me.id}` started successfully!")
    else:
        await message.reply(f"❌ Failed to start client for `{new_user_me.id}`. Check logs for details.")

    # Clean up the session
    user_auth_sessions.pop(message.from_user.id, None)

# This handler will catch any message that wasn't handled by other handlers in this file
@bot_client.on_message(owner_only, group=1)
async def unhandled_message_handler(client: Client, message: Message):
    """Replies to any unhandled message from the owner."""
    logger.info(f"Received an unhandled message from owner {message.from_user.id}")
    await message.reply("I received your message, but I'm not sure what you want me to do.")
