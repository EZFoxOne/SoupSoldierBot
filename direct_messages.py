from captcha_generator import is_banned, is_permanent_banned, start_unlock_process, is_pending_unlock,\
    verify_captcha, unlock_user
from database_tools import record_user


def handle_direct_messages(update, context):
    if update.effective_message.text == "/unlockme":
        if is_banned(update.effective_user.id):
            if is_permanent_banned(update.effective_user.id):
                context.bot.send_message(update.effective_user.id,
                                         "You have been permanently banned. No further unlocks are possible.\n\n"
                                         "If you believe this is an error, please reach out to an admin in Soup's Shill Shack. "
                                         "Allow up to 90 days to receive a response on this particular issue.")
                return
            start_unlock_process(update.effective_user.id, context)
        else:
            context.bot.send_message(update.effective_chat.id, "This account is already unlocked")
        return
    else:
        if is_pending_unlock(update.effective_user.id, context):
            result = verify_captcha(update.effective_user.id, update.effective_message.text)
            if result:
                unlock_user(update.effective_user.id, context)
            else:
                context.bot.send_message(update.effective_user.id, "Invalid CAPTCHA response")

    record_user(update.effective_user, update.effective_message, context, chat_type="private")
