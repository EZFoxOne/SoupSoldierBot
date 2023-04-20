from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update
from datetime import datetime
from config import api_token, group_id
from database_tools import record_message, record_user, initialize_all_databases, handle_scheduler_queue, \
    send_banned_message, handle_send_message_queue
from captcha_generator import is_banned
from direct_messages import handle_direct_messages

initialize_all_databases()

updater = Updater(api_token, use_context=True)

# Comment the following line to run in main bot account (SoupSoldier)
# updater = Updater(dev_api_token, use_context=True) # leave this code live to run in dev bot (SoupSoldierDEV)

job_queue = updater.job_queue


# TODO: add internal handler for admins to bypass moderation if necessary
def main_handler(update: Update, context: CallbackContext):

    # Handling DMs for unlocking accounts
    if update.effective_chat.type == "private":
        handle_direct_messages(update, context)
        return

    if is_banned(update.effective_user.id):
        update.message.delete()
        send_banned_message(group_id, update.effective_user.id, context)
        return

    if update.effective_chat.id != group_id:
        return

    if update.effective_user.username == "GroupAnonymousBot":
        return

    if update.message.photo or update.message.animation or update.message.audio or update.message.video \
            or update.message.document or update.message.effective_attachment:
        record_user(update.effective_user, update.effective_message, context, warning=True)
        return

    if update.edited_message:
        print('we received an edited message')
        # TODO: handle edited messages to scan for illegal content and delete if necessary
        return

    if len(update.message.new_chat_members) > 0:
        update.message.delete()
        return

    record_message(update.effective_user, update.effective_message, context)


job_queue.run_repeating(handle_scheduler_queue, 1)
job_queue.run_repeating(handle_send_message_queue, 1)
updater.dispatcher.add_handler(MessageHandler(Filters.update, main_handler))

updater.start_polling()
print("SoupSoldierBot successfully started at " + str(datetime.now()))
updater.idle()
