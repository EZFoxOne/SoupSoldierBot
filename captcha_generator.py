import string
import random
from database_tools import create_connection
from datetime import datetime


def generate_captcha():

    letters = ""
    for i in range(6):
        letters += random.choice(string.ascii_letters)

    wrapper_length = random.randrange(1, 4, 1)
    char = random.choice(["!", "@", "#", "$", "%", "&", "*"])
    chars = ""

    for i in range(wrapper_length):
        chars += char

    return chars + letters + chars


def generate_captcha_phrase(captcha):

    captcha_phrase = "Your %%placeholder%% captcha %%placeholder%% has %%placeholder%% been %%placeholder%% injected " \
                     "%%placeholder%% somewhere %%placeholder%% in %%placeholder%% this %%placeholder%% message.\n\n" \
                     "The %%placeholder%% location %%placeholder%% should %%placeholder%% become %%placeholder%% " \
                     "somewhat %%placeholder%% obvious, %%placeholder%% fairly %%placeholder%% quickly.\n\n" \
                     "Take %%placeholder%% your %%placeholder%% time, %%placeholder%% read %%placeholder%% the " \
                     "%%placeholder%% entire %%placeholder%% message, and %%placeholder%% reply %%placeholder%% " \
                     "with %%placeholder%% the %%placeholder%% correct %%placeholder%% answer %%placeholder%% to " \
                     "%%placeholder%% unlock %%placeholder%% your %%placeholder%% account."

    replacement_word = "%%placeholder%%"
    while replacement_word == "%%placeholder%%":
        replacement_word = random.choice(captcha_phrase.split())

    captcha_phrase = captcha_phrase.replace(replacement_word, "<b><i><u>" + captcha + "</u></i></b>")

    while captcha_phrase.find("%%placeholder%%") != -1:
        random_char = random.choice([" | ", " ' ", " / ", " . ", " - ", " _ ", " + ",  " = "])
        formatting = random.choice([True, False])
        if formatting:
            random_char = random.choice(["<b>" + random_char + "</b>",
                                         "<i>" + random_char + "</i>",
                                         "<b><i>" + random_char + "</i></b>",
                                         "<b><i><u>" + random_char + "</u></i></b>",
                                         "<b><u>" + random_char + "</u></b>"])
        captcha_phrase = captcha_phrase.replace(" %%placeholder%% ", random.choice([' ', random_char]), 1)

    return captcha_phrase


def store_captcha(captcha, user_id):
    conn, c = create_connection("locked_users")
    c.execute("INSERT INTO users (user_id, captcha, locked) VALUES (?,?,?);", [user_id, captcha, True])
    conn.commit()
    conn.close()


def delete_captcha(user_id, captcha):
    conn, c = create_connection("locked_users")
    c.execute("DELETE FROM users WHERE user_id = ? AND captcha = ?;", [user_id, captcha])
    conn.commit()
    conn.close()


def set_pending_unlock(user_id):
    conn, c = create_connection('recorded_users')
    c.execute("UPDATE users SET pending_unlock = ? WHERE user_id = ?;", [True, user_id])
    conn.commit()
    conn.close()


def is_pending_unlock(user_id, context):
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT pending_unlock FROM users WHERE user_id = ?;", [user_id]).fetchall()
    if len(data) != 0:
        return int(data[0][0])
    else:
        return None


def is_banned(user_id):
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT banned FROM users WHERE user_id = ?;", [user_id]).fetchall()
    if len(data) != 0:
        return int(data[0][0]) if data[0][0] is not None else 0
    else:
        return None


def is_permanent_banned(user_id):
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT unlock_count FROM users WHERE user_id = ?;", [user_id]).fetchall()
    if len(data) != 0:
        unlock_count = int(data[0][0]) if data[0][0] is not None else 0
        if unlock_count > 10:
            return True


def verify_captcha(user_id, captcha):
    conn, c = create_connection('locked_users')
    data = c.execute("SELECT captcha FROM users WHERE user_id = ?;", [user_id]).fetchall()
    if len(data) != 0:
        if captcha == data[0][0]:
            delete_captcha(user_id, captcha)
            return True
        else:
            return False
    else:
        return None


def unlock_user(user_id, context):
    conn, c = create_connection('recorded_users')
    data = c.execute("SELECT unlock_count FROM users WHERE user_id = ?;", [user_id]).fetchall()
    if data[0][0] is not None:
        unlock_count = int(data[0][0]) + 1
    else:
        unlock_count = 1
    if unlock_count > 10:
        context.bot.send_message(user_id, "You have been permanently banned. No further unlocks are possible.\n\n"
                                          "If you believe this is an error, please reach out to an admin in Soup's Shill Shack."
                                          " Allow up to 90 days to receive a response on this particular issue.")
        return
    else:
        c.execute("UPDATE users SET warnings = ?, unlock_count = ?, last_unlock = ?, banned = ?, pending_unlock = ? WHERE user_id = ?;",
                  [0, unlock_count, datetime.now(), False, False, user_id])
        conn.commit()
    conn.close()
    context.bot.send_message(user_id, "You have successfully unlocked this account. Please review our policies in "
                                      "Soup's Shill Shack to prevent this from happening again.\n\nExcessive bans will "
                                      "result in a permanent ban.")


def get_existing_captcha(user_id):
    conn, c = create_connection('locked_users')
    data = c.execute("SELECT * FROM users WHERE user_id = ? AND locked = ?;", [user_id, True]).fetchall()
    if len(data) != 0:
        return data[0][1]
    else:
        return None


def start_unlock_process(user_id, context):
    captcha = get_existing_captcha(user_id)
    if captcha is None:
        captcha = generate_captcha()
        store_captcha(captcha, user_id)
    captcha_phrase = generate_captcha_phrase(captcha)
    set_pending_unlock(user_id)
    context.bot.send_message(user_id, captcha_phrase, parse_mode="HTML")


if __name__ == "__main__":
    print("\n\n" + generate_captcha_phrase(generate_captcha()))
