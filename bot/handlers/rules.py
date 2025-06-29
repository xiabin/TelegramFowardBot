import json
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from database.manager import (
    add_forwarding_rule,
    get_forwarding_rules_for_user,
    delete_forwarding_rule,
    get_user_by_id,
)

logger = logging.getLogger(__name__)

# Command Filters
owner_only = filters.private & filters.user(OWNER_ID)

@Client.on_message(filters.command("addrule") & owner_only)
async def addrule_command(client: Client, message: Message):
    """
    为托管用户添加一个转发规则，使用JSON对象格式。
    用法: /addrule <托管用户ID> { "source_chats": [...], "destination_chats": [...] }
    示例: /addrule 12345 { "source_chats": [-100123], "destination_chats": [-100456] }
    """
    if len(message.command) < 3:
        await message.reply(
            "用法: /addrule <托管用户ID> { \"source_chats\": [...], \"destination_chats\": [...] }\n\n"
            "示例: /addrule 12345 { \"source_chats\": [-100123], \"destination_chats\": [-100456] }"
        )
        return

    try:
        user_id = int(message.command[1])
        rule_json = " ".join(message.command[2:])
        rule_config = json.loads(rule_json)

        # Basic validation of the config
        if 'source_chats' not in rule_config or 'destination_chats' not in rule_config:
            await message.reply("JSON配置必须包含 'source_chats' 和 'destination_chats' 键。")
            return
        if not isinstance(rule_config['source_chats'], list) or not isinstance(rule_config['destination_chats'], list):
            await message.reply("'source_chats' 和 'destination_chats' 必须是聊天ID的列表。")
            return

        if not await get_user_by_id(user_id):
            await message.reply(f"未找到ID为 `{user_id}` 的托管用户。")
            return

        rule = await add_forwarding_rule(user_id, rule_config)
        await message.reply(
            f"✅ 用户 `{user_id}` 的转发规则已成功添加。\n"
            f"<b>规则ID:</b> <code>{rule['_id']}</code>"
        )

    except ValueError:
        await message.reply("无效的用户ID。它必须是整数。")
    except json.JSONDecodeError:
        await message.reply("无效的JSON提供。请检查格式。")
    except Exception as e:
        logger.error(f"Error in addrule_command: {e}", exc_info=True)
        await message.reply(f"发生错误: {e}")

@Client.on_message(filters.command("listrules") & owner_only)
async def listrules_command(client: Client, message: Message):
    """
    列出特定托管用户的所有转发规则。
    用法: /listrules <托管用户ID>
    """
    if len(message.command) < 2:
        await message.reply("用法: /listrules <托管用户ID>")
        return

    try:
        user_id = int(message.command[1])
        if not await get_user_by_id(user_id):
            await message.reply(f"未找到ID为 `{user_id}` 的托管用户。")
            return
            
        rules = await get_forwarding_rules_for_user(user_id)
        if not rules:
            await message.reply(f"未找到用户 `{user_id}` 的转发规则。")
            return

        response = f"<b>用户 `{user_id}` 的转发规则:</b>\n\n" 
        for rule in rules:
            sources = ", ".join(map(str, rule.get('source_chats', [])))
            dests = ", ".join(map(str, rule.get('destination_chats', [])))
            response += (
                f"<b>规则ID:</b> <code>{rule['_id']}</code>\n"
                f"  <b>来源:</b> <code>{sources if sources else 'Any Chat'}</code>\n"
                f"  <b>目标:</b> <code>{dests}</code>\n\n"
            )
        
        await message.reply(response)
    except ValueError:
        await message.reply("无效的用户ID。它必须是整数。")
    except Exception as e:
        logger.error(f"Error in listrules_command: {e}", exc_info=True)
        await message.reply(f"发生错误: {e}")

@Client.on_message(filters.command("delrule") & owner_only)
async def delrule_command(client: Client, message: Message):
    """
    通过其唯一ID删除一个转发规则。
    用法: /delrule <规则ID>
    """
    if len(message.command) < 2:
        await message.reply("用法: /delrule <规则ID>")
        return

    try:
        rule_id = message.command[1]
        if await delete_forwarding_rule(rule_id):
            await message.reply(f"✅ 规则 <code>{rule_id}</code> 已删除。")
        else:
            await message.reply(f"无法找到ID为 <code>{rule_id}</code> 的规则。")
    except Exception as e:
        logger.error(f"Error in delrule_command: {e}", exc_info=True)
        await message.reply(f"发生错误: {e}")
