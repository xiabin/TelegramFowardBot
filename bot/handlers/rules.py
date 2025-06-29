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
from ..app import bot_client
from ..app import bot_client

logger = logging.getLogger(__name__)

# Command Filters
owner_only = filters.private & filters.user(OWNER_ID)

@bot_client.on_message(filters.command("addrule") & owner_only)
async def addrule_command(client: Client, message: Message):
    """
    Adds a forwarding rule for a managed user using a JSON object.
    Usage: /addrule <managed_user_id> { "source_chats": [...], "destination_chats": [...] }
    Example: /addrule 12345 { "source_chats": [-100123], "destination_chats": [-100456] }
    """
    if len(message.command) < 3:
        await message.reply(
            "<b>Usage:</b> <code>/addrule &lt;user_id&gt; &lt;json_config&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/addrule 1234567 "
            '{"source_chats": [-100123456], "destination_chats": [-100789012]}</code>'
        )
        return

    try:
        user_id = int(message.command[1])
        rule_json = " ".join(message.command[2:])
        rule_config = json.loads(rule_json)

        # Basic validation of the config
        if 'source_chats' not in rule_config or 'destination_chats' not in rule_config:
            await message.reply("JSON config must include 'source_chats' and 'destination_chats' keys.")
            return
        if not isinstance(rule_config['source_chats'], list) or not isinstance(rule_config['destination_chats'], list):
            await message.reply("'source_chats' and 'destination_chats' must be lists of chat IDs.")
            return

        if not await get_user_by_id(user_id):
            await message.reply(f"No managed user found with ID `{user_id}`.")
            return

        rule = await add_forwarding_rule(user_id, rule_config)
        await message.reply(
            f"✅ Rule added successfully for user `{user_id}`.\n"
            f"<b>Rule ID:</b> <code>{rule['_id']}</code>"
        )

    except ValueError:
        await message.reply("Invalid User ID. It must be an integer.")
    except json.JSONDecodeError:
        await message.reply("Invalid JSON provided. Please check the format.")
    except Exception as e:
        logger.error(f"Error in addrule_command: {e}", exc_info=True)
        await message.reply(f"An error occurred: {e}")

@bot_client.on_message(filters.command("listrules") & owner_only)
async def listrules_command(client: Client, message: Message):
    """
    Lists all forwarding rules for a specific managed user.
    Usage: /listrules <managed_user_id>
    """
    if len(message.command) < 2:
        await message.reply("Usage: /listrules <managed_user_id>")
        return

    try:
        user_id = int(message.command[1])
        if not await get_user_by_id(user_id):
            await message.reply(f"No managed user found with ID `{user_id}`.")
            return
            
        rules = await get_forwarding_rules_for_user(user_id)
        if not rules:
            await message.reply(f"No forwarding rules found for user `{user_id}`.")
            return

        response = f"<b>Forwarding rules for user `{user_id}`:</b>\n\n"
        for rule in rules:
            sources = ", ".join(map(str, rule.get('source_chats', [])))
            dests = ", ".join(map(str, rule.get('destination_chats', [])))
            response += (
                f"<b>Rule ID:</b> <code>{rule['_id']}</code>\n"
                f"  <b>From:</b> <code>{sources if sources else 'Any Chat'}</code>\n"
                f"  <b>To:</b> <code>{dests}</code>\n\n"
            )
        
        await message.reply(response)
    except ValueError:
        await message.reply("Invalid User ID provided.")
    except Exception as e:
        logger.error(f"Error in listrules_command: {e}", exc_info=True)
        await message.reply(f"An error occurred: {e}")

@bot_client.on_message(filters.command("delrule") & owner_only)
async def delrule_command(client: Client, message: Message):
    """
    Deletes a forwarding rule by its unique ID.
    Usage: /delrule <rule_id>
    """
    if len(message.command) < 2:
        await message.reply("Usage: /delrule <rule_id>")
        return

    try:
        rule_id = message.command[1]
        if await delete_forwarding_rule(rule_id):
            await message.reply(f"✅ Rule <code>{rule_id}</code> has been deleted.")
        else:
            await message.reply(f"Could not find a rule with ID <code>{rule_id}</code> to delete.")
    except Exception as e:
        logger.error(f"Error in delrule_command: {e}", exc_info=True)
        await message.reply(f"An error occurred: {e}")
