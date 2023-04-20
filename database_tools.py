import sqlite3
from datetime import datetime, timedelta
from config import database_dir, group_id, google_form


def create_connection(db_name):
    conn = sqlite3.connect(database_dir + db_name + ".db")
    c = conn.cursor()
    return conn, c


def initialize_all_databases():
    initialize_user_database()
    initialize_message_database()
    initialize_scheduler_database()
    initialize_locked_users_database()
    initialize_send_message_database()
    initialize_campaign_database()


def initialize_message_database():
    conn, c = create_connection('recorded_messages')
    c.execute("CREATE TABLE IF NOT EXISTS messages (user_id TEXT, timestamp TEXT, message_content TEXT);")
    conn.commit()
    conn.close()


def initialize_user_database():
    conn, c = create_connection('recorded_users')
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT UNIQUE, user_name TEXT, first_message_date TEXT, "
              "last_message_date TEXT, warnings TEXT, last_warning_date TEXT, banned TEXT, banned_date TEXT, "
              "last_banned_message_date TEXT, unlock_count TEXT, last_unlock TEXT, pending_unlock TEXT);")
    conn.commit()
    conn.close()


def initialize_admin_database():
    conn, c = create_connection('recorded_admins')
    c.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT, user_name TEXT, admin_role TEXT, added_by TEXT, "
              "last_modified TEXT, last_modifier TEXT);")
    conn.commit()
    conn.close()


def initialize_scheduler_database():
    conn, c = create_connection('scheduler')
    c.execute(
        "CREATE TABLE IF NOT EXISTS queue (message_id INTEGER PRIMARY KEY AUTOINCREMENT, message_content TEXT, first_scheduled_date TEXT, current_scheduled_date TEXT, "
        "interval TEXT, successful_posts TEXT, unsuccessful_posts TEXT, active TEXT);")
    conn.commit()
    conn.close()


def initialize_locked_users_database():
    conn, c = create_connection('locked_users')
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT, captcha TEXT, locked TEXT);")
    conn.commit()
    conn.close()


def initialize_send_message_database():
    conn, c = create_connection('send_message')
    c.execute("CREATE TABLE IF NOT EXISTS queue (message_id INTEGER PRIMARY KEY AUTOINCREMENT, message_content TEXT);")
    conn.commit()
    conn.close()


def initialize_campaign_database():
    conn, c = create_connection('campaign_scheduler')
    c.execute("CREATE TABLE IF NOT EXISTS campaigns (campaign_id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_name TEXT, "
              "campaign_content TEXT, main_contact TEXT, paid TEXT, start_time TEXT, end_time TEXT, lock_chat TEXT, "
              "twitter_post TEXT, twitter_post_content TEXT, continuous_post TEXT, continuous_post_interval TEXT, started TEXT, "
              "completed TEXT);")
    conn.commit()
    conn.close()


def send_banned_message(chat_id, user_id, context):
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT * FROM users WHERE user_id = ?;", [user_id]).fetchall()
    last_banned_message_date = datetime.fromisoformat(data[0][8]) if data[0][8] is not None else datetime.now() - timedelta(minutes=60)
    if last_banned_message_date < datetime.now() - timedelta(minutes=60):
        context.bot.send_message(chat_id,
                                 "<b>WHOOPS</b>\n\nIt looks like you've been banned from Soup's Shill Shack for violating some of our policies.\n\n"
                                 "Unlock your account by sending me a DM with the command /unlockme",
                                 parse_mode="HTML")
        c.execute("UPDATE users SET last_banned_message_date = ? WHERE user_id = ?;", [datetime.now(), user_id])
        conn.commit()
    conn.close()


def record_user(user, message, context, warning=None, chat_type="private"):
    timestamp = str(datetime.now())
    chat_id = group_id
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT * FROM users WHERE user_id = ?;", [user.id]).fetchall()
    if len(data) != 0:
        banned = int(data[0][6]) if data[0][6] is not None else None
        if banned is True:
            if chat_type == "private":
                chat_id = message.chat_id
            send_banned_message(chat_id, user.id, context)
            if chat_type != "private":
                message.delete()
            return

        warning_count = int(data[0][4]) if data[0][4] is not None else 0
        last_warning_date = datetime.fromisoformat(data[0][5]) if data[0][5] is not None else None
        last_banned_date = None

        if warning is not None:
            message.delete()
            if last_warning_date is not None:
                warning_threshold = datetime.now() - timedelta(minutes=60)
                if last_warning_date > warning_threshold:
                    warning_count += 1
                    if warning_count > 50:
                        banned = True
                        last_banned_date = datetime.now()
                        send_banned_message(chat_id, user.id, context)
                else:
                    warning_count = 1
            else:
                warning_count = 1
            last_warning_date = datetime.now()

        c.execute(
            "UPDATE users SET last_message_date = ?, warnings = ?, last_warning_date = ?, banned = ?, banned_date = ? "
            "WHERE user_id = ?;",
            [str(datetime.now()), warning_count, last_warning_date,
             banned, last_banned_date, user.id])

    else:

        warning_count = 0
        last_warning_date = None
        if warning is not None:
            warning_count = 1
            last_warning_date = datetime.now()

        c.execute(
            "INSERT INTO users (user_id, user_name, first_message_date, last_message_date, warnings, last_warning_date) VALUES (?,?,?,?,?,?);",
            [user.id, user.first_name, timestamp, timestamp, warning_count, last_warning_date])

    conn.commit()
    conn.close()


def record_message(user, message, context):
    time_threshold = datetime.now() - timedelta(minutes=60)

    if message.text is not None:
        if len(message.text) > 250:
            record_user(user, message, context, warning=True)
            return

    for entity in message.entities:
        if entity.type == "url":
            record_user(user, message, context, warning=True)
            return

    conn, c = create_connection('recorded_messages')
    data = c.execute(
        'SELECT * FROM messages WHERE timestamp > ? AND user_id = ? ORDER BY CAST(timestamp AS DATE) DESC;',
        [time_threshold, user.id]).fetchall()

    # TODO: build out this process further to handle checking for duplicates, checking for banned content, etc...
    for result in data:
        last_message_content = result[2]
        last_message_date = datetime.fromisoformat(result[1])
        difference = (message.date - last_message_date).seconds / 60

        # deleting messages that are duplicates of other messages that have been received in the last 60 minutes
        if last_message_content == message.text and difference < 60:
            record_user(user, message, context, warning=True)
            return

    record_user(user, message, context)
    c.execute("INSERT INTO messages (user_id, timestamp, message_content) VALUES (?,?,?);",
              [user.id, str(message.date), message.text])
    conn.commit()
    conn.close()


def handle_scheduler_queue(context):
    current_time = datetime.now()
    conn, c = create_connection('scheduler')
    data = c.execute("SELECT * FROM queue").fetchall()
    for item in data:
        message_id = item[0]
        content = item[1]
        run_at = datetime.fromisoformat(item[3])
        if run_at <= current_time:
            context.bot.send_message(group_id, content, parse_mode="HTML")
            interval = int(item[4])
            new_scheduled_date = current_time + timedelta(minutes=interval)
            c.execute("UPDATE queue SET current_scheduled_date = ? WHERE message_id = ?;",
                      [new_scheduled_date, message_id])
            conn.commit()
    conn.close()


def handle_send_message_queue(context):
    conn, c = create_connection('send_message')
    data = c.execute("SELECT * FROM queue").fetchall()
    for item in data:
        message_id = item[0]
        message_content = item[1]
        context.bot.send_message(group_id, message_content, parse_mode="HTML")
        c.execute("DELETE FROM queue WHERE message_id = ?;", [message_id])
        conn.commit()
    conn.close()


def add_dev_scheduled_message():
    conn, c = create_connection('scheduler')
    dev_message = "<b>Welcome to Soup's Shill Shack!</b>\n\n" \
                  "Adhere to the following guidelines to prevent your messages from being deleted:\n\n" \
                  "-- No duplicate messages\n-- No urls (only TG mentions)\n-- No more than 250 characters\n-- " \
                  "No images/gifs/videos/audio/recordings/documents\n\n" \
                  "Be chill and have fun!\n\nTo request premium placement, complete this <a href='" + google_form + \
                  "'>Google form</a>\n\n(<b>LIMITED TIME:</b> Free Premium Placement, first come first served)"
    interval = 60
    c.execute('INSERT INTO queue (message_content, first_scheduled_date, current_scheduled_date, interval, '
              'successful_posts, unsuccessful_posts, active) VALUES (?,?,?,?,?,?,?)',
              [dev_message, str(datetime.now()), str(datetime.now()), interval, None, None, None])
    conn.commit()
    conn.close()


def is_admin(update):
    status = update.message.bot.get_chat_member(group_id, update.effective_user.id)
    if status == "creator" or status == "admin":
        return True
    else:
        return False


def list_scheduled_messages(update, context):
    if is_admin(update):
        conn, c = create_connection('scheduler')
        data = c.execute('SELECT * FROM queue').fetchall()
        outgoing_message = "List of scheduled messages --\n\n"
        for item in data:
            outgoing_message += str(item[0]) + ": " + item[1] + "\n"
        context.bot.send_message(group_id, outgoing_message)


def delete_scheduled_message(message_ids):
    conn, c = create_connection('scheduler')
    try:
        message_ids = message_ids.split(',')
        for message_id in message_ids:
            print(message_id)
            c.execute("DELETE FROM queue WHERE message_id = ?;", [message_id])
        conn.commit()
        result = "Success: deleted all found message IDs"
    except:
        result = "Failed: Something went wrong during message deletion. Check the data and try again."
    conn.close()
    return result


def get_user_list():
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT * FROM users").fetchall()
    conn.close()
    return data


def get_message_list():
    conn, c = create_connection('recorded_messages')
    data = c.execute("SELECT * FROM messages").fetchall()
    conn.close()
    return data


def get_scheduler_list():
    conn, c = create_connection('scheduler')
    data = c.execute("SELECT * FROM queue").fetchall()
    conn.close()
    return data


def get_banned_list():
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT * FROM users WHERE banned = ?", [1]).fetchall()
    conn.close()
    return data


if __name__ == "__main__":
    add_dev_scheduled_message()
