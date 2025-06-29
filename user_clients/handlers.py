import logging
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.manager import get_forwarding_rules_for_user
from bot.app import bot_client

logger = logging.getLogger(__name__)

# A broad filter to capture all relevant messages for forwarding.
# Includes private messages and group messages where the user is mentioned. Excludes messages sent by the user client itself or by other bots.
FORWARD_FILTER = (filters.private | (filters.group & filters.mentioned)) & ~filters.me & ~filters.bot

async def _get_message_details(message: Message) -> (str, str, bool):
    """
    Helper function to get a descriptive content type, details, and media status from a message.
    """
    content_type = "未知消息类型"
    content_detail = ""
    is_media = False

    if message.text:
        content_type = "文本消息"
        content_detail = f"<b>Message:</b> {message.text[:200]}" # Limit length
    elif message.photo:
        content_type = "图片"
        if message.caption:
            content_detail = f"<b>Caption:</b> {message.caption}"
        is_media = True
    elif message.video_note:
        content_type = "圆形视频"
        is_media = True
    elif message.video:
        content_type = "视频"
        if message.video.file_name:
            content_detail = f"<b>File:</b> {message.video.file_name}"
        if message.caption:
            content_detail += f"\n<b>Caption:</b> {message.caption}"
        is_media = True
    elif message.document:
        content_type = "文件"
        if message.document.file_name:
            content_detail = f"<b>File:</b> {message.document.file_name}"
        if message.caption:
            content_detail += f"\n<b>Caption:</b> {message.caption}"
        is_media = True
    elif message.audio:
        content_type = "音频"
        if message.audio.file_name:
            content_detail = f"<b>File:</b> {message.audio.file_name}"
        is_media = True
    elif message.voice:
        content_type = "语音消息"
        is_media = True
    elif message.sticker:
        content_type = "贴纸"
        if message.sticker.emoji:
            content_detail = f"<b>Emoji:</b> {message.sticker.emoji}"
        is_media = True
    elif message.animation:
        content_type = "动画"
        if message.animation.file_name:
            content_detail = f"<b>File:</b> {message.animation.file_name}"
        is_media = True
    elif message.contact:
        content_type = "联系人"
        content_detail = f"<b>Name:</b> {message.contact.first_name}"
        if message.contact.phone_number:
            content_detail += f"\n<b>Phone:</b> {message.contact.phone_number}"
    elif message.location:
        content_type = "位置"
        content_detail = f"<b>Longitude:</b> {message.location.longitude}\n<b>Latitude:</b> {message.location.latitude}"
    elif message.venue:
        content_type = "地点"
        content_detail = f"<b>Title:</b> {message.venue.title}\n<b>Address:</b> {message.venue.address}"
    
    return content_type, content_detail.strip(), is_media

async def forwarding_handler(client: Client, message: Message):
    """
    Handles all incoming messages for a user client, checks against forwarding rules,
    and forwards the message to the appropriate destinations with rich notifications.
    """
    user_id = client.me.id
    user_mention = message.from_user.mention if message.from_user else "未知"
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
            should_forward = False
            
            # 1. Handle mentions specifically
            if message.mentioned and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                sender = message.from_user.mention if message.from_user else "Someone"
                notification_text = (
                    f"🔔 **您在 {message.chat.title} 被提及**\n\n"
                    f"<b>来自:</b> {sender}\n"
                    f"<b>消息内容:</b> {message.text or message.caption or '...'}\n\n"
                )
                if message.link:
                    reply_markup = InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="💬 查看消息", url=message.link)]]
                    )
                # 群组提及只通知，不转发。
                should_forward = False

            # 2. Handle other messages
            else:
                content_type, content_detail, is_media = await _get_message_details(message)
                notification_text = (
                    f"🔔 新的{content_type} 来自 {user_mention}\n\n"
                    f"{content_detail}\n\n"
                ).strip()

                
                # Only forward private messages that are media
                if is_media:
                    should_forward = True

            # Send the notification message via the BOT
            await bot_client.send_message(
                chat_id=dest_chat,
                text=notification_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
            )

            # Then, forward the original message(s) if needed
            if should_forward:
                forwarded = await message.forward(chat_id=bot_client.me.id,disable_notification=True)
                if forwarded:
                    await bot_client.send_message(
                        chat_id=dest_chat,
                        text=f"✅ 以上是转发的{content_type}",
                        reply_markup=reply_markup,
                        disable_web_page_preview=True,
                        parse_mode=enums.ParseMode.HTML,
                    )
                logger.info(f"User client {user_id}: Successfully forwarded message {message.id} to {dest_chat}.")
            else:
                logger.info(f"User client {user_id}: Sent notification for message {message.id} to {dest_chat} (no forward).")

        except Exception as e:
            logger.error(
                f"User client {user_id}: Failed to process message {message.id} for destination {dest_chat}. Error: {e}",
                exc_info=True
            )

def register_handlers(client: Client):
    """
    Registers all necessary handlers for a user client instance.
    This approach is used instead of decorators to support multiple client instances.
    """
    client.add_handler(MessageHandler(forwarding_handler, FORWARD_FILTER), group=1)
    logger.info("Registered user client message handlers.")
