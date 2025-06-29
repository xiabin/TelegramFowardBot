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
from config import API_ID, API_HASH, OWNER_ID, PROXY
from database.manager import add_managed_user
from user_clients.manager import user_client_manager
from ..app import bot_client

logger = logging.getLogger(__name__)

# In-memory dictionary to store conversation state for adding users
user_auth_sessions = {}

# Custom filter for the owner
owner_only = filters.private 

@Client.on_message(filters.command("adduser") & owner_only)
async def adduser_command(client: Client, message: Message):
    """Starts the process of adding a new managed user."""
    logger.info(f"Received /adduser command from owner {message.from_user.id}")
    
    admin_id = message.from_user.id
    if admin_id in user_auth_sessions:
        await message.reply("您已经在添加用户流程中。发送 /cancel 以取消当前操作。")
        return

    user_auth_sessions[admin_id] = {"step": "phone"}
    await message.reply(
        "开始添加新托管用户流程...\n\n"
        "**步骤 1：** 请输入要添加账号的手机号（如：+861234567890）。\n\n"
        "随时发送 /cancel 以取消操作。"
    )

@Client.on_message(filters.command("cancel") & owner_only)
async def cancel_command(client: Client, message: Message):
    """Cancels the current operation."""
    admin_id = message.from_user.id
    if admin_id in user_auth_sessions:
        session_data = user_auth_sessions.pop(admin_id)
        temp_client = session_data.get("client")
        if temp_client and temp_client.is_connected:
            await temp_client.disconnect()
        await message.reply("操作已取消。")
    else:
        await message.reply("当前没有正在进行的操作可取消。")

@Client.on_message(filters.text & ~filters.command(["adduser", "cancel"]) & owner_only)
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
        await message.reply(f"发生意外错误：{e}。\n请重试或发送 /cancel 取消操作。")
        user_auth_sessions.pop(admin_id, None)

async def process_phone_step(message: Message, session_data: dict):
    phone_number = message.text
    
    # Prepare client parameters with proxy support
    client_params = {
        "name": f"temp_{message.from_user.id}",
        "api_id": API_ID,
        "api_hash": API_HASH,
        "in_memory": True
    }
    
    if PROXY:
        client_params["proxy"] = PROXY
        logger.info(f"Using proxy configuration for temporary client: {PROXY['hostname']}:{PROXY['port']}")
    
    temp_client = Client(**client_params)
    await temp_client.connect()
    
    sent_code = await temp_client.send_code(phone_number)
    
    session_data.update({
        "step": "code",
        "phone": phone_number,
        "phone_code_hash": sent_code.phone_code_hash,
        "client": temp_client
    })
    await message.reply("**步骤 2：** 验证码已发送，请输入收到的验证码。")

async def process_code_step(message: Message, session_data: dict):
    code = message.text
    temp_client = session_data["client"]
    try:
        await temp_client.sign_in(session_data["phone"], session_data["phone_code_hash"], code)
        await finalize_session(message, session_data)
    except SessionPasswordNeeded:
        session_data["step"] = "password"
        await message.reply("**步骤 3：** 该账号已开启两步验证，请输入密码。")
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await message.reply("验证码无效或已过期，请重试或发送 /cancel 取消操作。")

async def process_password_step(message: Message, session_data: dict):
    password = message.text
    temp_client = session_data["client"]
    try:
        await temp_client.check_password(password)
        await finalize_session(message, session_data)
    except PasswordHashInvalid:
        await message.reply("密码错误，请重试或发送 /cancel 取消操作。")

async def finalize_session(message: Message, session_data: dict):
    """Finalizes the session, saves it, and starts the client immediately."""
    temp_client = session_data["client"]
    session_string = await temp_client.export_session_string()
    new_user_me = await temp_client.get_me()
    
    await temp_client.disconnect()
    
    # 1. Save the user to the database
    await add_managed_user(new_user_me.id, session_string)
    await message.reply(f"✅ 用户 `{new_user_me.id}`（{new_user_me.first_name}）已保存到数据库。")

    # 2. Start the user client instance immediately
    await message.reply(f"🚀 正在启动 `{new_user_me.id}` 的客户端...")
    success = await user_client_manager.start_client(new_user_me.id, session_string)

    if success:
        await message.reply(f"✅ `{new_user_me.id}` 的客户端启动成功！")
    else:
        await message.reply(f"❌ `{new_user_me.id}` 的客户端启动失败，请查看日志获取详情。")

    # Clean up the session
    user_auth_sessions.pop(message.from_user.id, None)

