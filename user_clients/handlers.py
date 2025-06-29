import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.manager import get_forwarding_rules_for_user
from bot.main import bot_client

logger = logging.getLogger(__name__)

# A broad filter to capture all relevant messages for forwarding.
# Includes private, group, and channel messages. Excludes messages sent by the user client itself or by other bots.
FORWARD_FILTER = (filters.private | filters.group | filters.channel) & ~filters.me & ~filters.bot

async def _get_message_details(message: Message) -> (str, str):
    """
    Helper function to get a descriptive content type and details from a message,
    based on the logic from the provided ubot_plugin.py.
    """
    content_type = "Unknown Message Type"
    content_detail = ""

    if message.text:
        content_type = "Text Message"
        content_detail = f"<b>Message:</b> {message.text[:200]}" # Limit length
    elif message.photo:
        content_type = "Photo"
        if message.caption:
            content_detail = f"<b>Caption:</b> {message.caption}"
    elif message.video:
        content_type = "Video"
        if message.video.file_name:
            content_detail = f"<b>File:</b> {message.video.file_name}"
        if message.caption:
            content_detail += f"\n<b>Caption:</b> {message.caption}"
    elif message.document:
        content_type = "File"
        if message.document.file_name:
            content_detail = f"<b>File:</b> {message.document.file_name}"
        if message.caption:
            content_detail += f"\n<b>Caption:</b> {message.caption}"
    elif message.audio:
        content_type = "Audio"
        if message.audio.file_name:
            content_detail = f"<b>File:</b> {message.audio.file_name}"
    elif message.voice:
        content_type = "Voice Message"
    elif message.sticker:
        content_type = "Sticker"
        if message.sticker.emoji:
            content_detail = f"<b>Emoji:</b> {message.sticker.emoji}"
    # Add other types as needed from the example
    
    return content_type, content_detail.strip()

async def _get_source_details(message: Message) -> str:
    """Gets a descriptive string for the source of a message."""
    if message.chat.type == enums.ChatType.PRIVATE:
        return f"a private message from {message.from_user.mention}"
    elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return f"the group <b>{message.chat.title}</b>"
    elif message.chat.type == enums.ChatType.CHANNEL:
        return f"the channel <b>{message.chat.title}</b>"
    return "an unknown chat"

@Client.on_message(FORWARD_FILTER, group=1)
async def forwarding_handler(client: Client, message: Message):
    """
    Handles all incoming messages for a user client, checks against forwarding rules,
    and forwards the message to the appropriate destinations with rich notifications.
    """
    user_id = client.me.id
    user_mention = client.me.mention
    source_chat_id = message.chat.id
    logger.info(f"User client {user_id}: Received message {message.id} from chat {source_chat_id}.")

    try:
        rules = await get_forwarding_rules_for_user(user_id)
    except Exception as e:
        logger.error(f"User client {user_id}: Could not retrieve forwarding rules. Error: {e}", exc_info=True)
        return

    matching_destination_chats = set()
    
    # Determine which destinations to forward to based on rules
    for rule in rules:
        # An empty source_chats list means the rule applies to all sources
        is_match_all_rule = not rule.get('source_chats')
        
        if is_match_all_rule or source_chat_id in rule.get('source_chats', []):
            dests = rule.get('destination_chats', [])
            logger.info(f"User client {user_id}: Message {message.id} matched rule {rule['_id']}. Adding destinations: {dests}")
            for dest in dests:
                matching_destination_chats.add(dest)

    # If no rules matched, forward to user's PM by default
    if not matching_destination_chats:
        logger.info(f"User client {user_id}: No rules matched message {message.id}. Forwarding to user's PM by default.")
        target_chats = {user_id}
    else:
        target_chats = matching_destination_chats

    # Perform the forwarding and send a notification
    for dest_chat in target_chats:
        try:
            notification_text = ""
            reply_markup = None
            
            # 1. Handle mentions specifically
            if message.mentioned and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                sender = message.from_user.mention if message.from_user else "Someone"
                notification_text = (
                    f"🔔 **You were mentioned in {message.chat.title}**\n\n"
                    f"<b>From:</b> {sender}\n"
                    f"<b>Message:</b> {message.text or message.caption or '...'}\n\n"
                    f"(Forwarded for user {user_mention} by TeleFwdBot)"
                )
                if message.link:
                    reply_markup = InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="💬 View Message", url=message.link)]]
                    )

            # 2. Handle other messages
            else:
                content_type, content_detail = await _get_message_details(message)
                source_details = await _get_source_details(message)
                notification_text = (
                    f"🔔 New {content_type} from {source_details}\n\n"
                    f"{content_detail}\n\n"
                    f"(Forwarded for user {user_mention} by TeleFwdBot)"
                ).strip()

                # Create a button to jump to the source
                button_text = None
                button_url = None
                if message.chat.type == enums.ChatType.PRIVATE and message.from_user:
                    button_text = "💬 Go to Chat"
                    button_url = f"tg://user?id={message.from_user.id}"
                elif message.link:
                    button_text = "💬 View Message"
                    button_url = message.link
                
                if button_text and button_url:
                    reply_markup = InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text=button_text, url=button_url)]]
                    )

            # Send the notification message via the BOT
            await bot_client.send_message(
                chat_id=dest_chat,
                text=notification_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )

            # Then, forward the original message(s) using the USER client
            await message.forward(chat_id=dest_chat)
            
            logger.info(f"User client {user_id}: Successfully forwarded message {message.id} to {dest_chat}.")
        
        except Exception as e:
            logger.error(
                f"User client {user_id}: Failed to forward message {message.id} to destination {dest_chat}. Error: {e}",
                exc_info=True
            )
