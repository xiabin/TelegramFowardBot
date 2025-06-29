from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from config import OWNER_ID
from database.manager import get_all_active_users, deactivate_user
from user_clients.manager import user_client_manager

# Command Filters
owner_only = filters.private & filters.user(OWNER_ID)

@Client.on_message(filters.command("deluser") & owner_only,group=1)
async def deluser_command(client: Client, message: Message):
    """
    停用一个已管理的用户并立即停止他们的客户端实例。
    用法：/deluser <user_id>
    """
    if len(message.command) < 2:
        await message.reply("用法：/deluser <user_id>")
        return

    try:
        user_id_to_del = int(message.command[1])
        
        # 1. 如果客户端正在运行，则停止它
        stopped = await user_client_manager.stop_client(user_id_to_del)
        if stopped:
            await message.reply(f"✔️ 用户 `{user_id_to_del}` 的客户端已成功停止。")
        else:
            await message.reply(f"⚠️ 用户 `{user_id_to_del}` 的客户端未运行。")

        # 2. 在数据库中停用用户
        if await deactivate_user(user_id_to_del):
            await message.reply(f"✅ 用户 `{user_id_to_del}` 已从数据库中停用。")
        else:
            await message.reply(f"⚠️ 无法在数据库中找到用户 `{user_id_to_del}`。")

    except ValueError:
        await message.reply("提供的用户ID无效。它必须是整数。")
    except Exception as e:
        await message.reply(f"发生错误：{e}")

@Client.on_message(filters.command("listusers") & owner_only,1)
async def listusers_command(client: Client, message: Message):
    """列出所有活动的已管理用户及其客户端状态。"""
    try:
        users = await get_all_active_users()
        if not users:
            await message.reply("数据库中未配置任何活动用户。")
            return

        response = "已管理用户（在DB中活动）：\n\n"
        for user in users:
            user_id = user['user_id']
            status = "✅ 运行中" if user_id in user_client_manager.running_clients else "❌ 已停止"
            response += f"- **用户ID:** `{user_id}` | **状态:** {status}\n"
        
        await message.reply(response)
    except Exception as e:
        await message.reply(f"发生错误：{e}")

