from database_tools import create_connection


def admin_unban(user_ids):
    try:
        user_ids = user_ids.split(',')
        for user_id in user_ids:
            conn, c = create_connection('recorded_users')
            c.execute("UPDATE users SET banned = ? WHERE user_id = ?;", [0, user_id])
            conn.commit()
            conn.close()
        return "Success: Unbanned users"
    except:
        return "Failed: Something went wrong during the unban process. Please check your data and try again."


def admin_ban(user_ids):
    try:
        user_ids = user_ids.split(',')
        for user_id in user_ids:
            conn, c = create_connection('recorded_users')
            c.execute("UPDATE users SET banned = ? WHERE user_id = ?;", [1, user_id])
            conn.commit()
            conn.close()
        return "Success: Banned users"
    except:
        return "Failed: Something went wrong during the ban process. Please check your data and try again."


def send_a_message(message):
    try:
        conn, c = create_connection('send_message')
        c.execute("INSERT INTO queue (message_content) VALUES (?);", [message])
        conn.commit()
        conn.close()
        return "Success: The message was queued"
    except:
        return "Failed: Something went wrong while trying to send the message"


def reset_warnings(user_ids):
    try:
        user_ids = user_ids.split(',')
        for user_id in user_ids:
            conn, c = create_connection('recorded_users')
            c.execute("UPDATE users SET warnings = ? WHERE user_id = ?;", [0, user_id])
            conn.commit()
            conn.close()
        return "Success: Reset user warnings"
    except:
        return "Failed: Something went wrong during the reset_warnings process. Please check your data and try again."


def reset_unlocks(user_ids):
    try:
        user_ids = user_ids.split(',')
        for user_id in user_ids:
            conn, c = create_connection('recorded_users')
            c.execute("UPDATE users SET unlock_count = ? WHERE user_id = ?;", [0, user_id])
            conn.commit()
            conn.close()
        return "Success: Reset user unlocks"
    except:
        return "Failed: Something went wrong during the reset_unlocks process. Please check your data and try again."
