from datetime import datetime, timedelta
import hashlib
import hmac
import os
from database_tools import create_connection
import uuid
from typing import Tuple
import json


def initialize_authorized_users_database():
    conn, c = create_connection('authorized_users')
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, name TEXT, "
              "salt TEXT, salted_hash TEXT, roles TEXT, date_created TEXT);")
    c.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT UNIQUE, expiration TEXT);")
    conn.commit()
    conn.close()


def process_login(data):
    token = None
    username, password = data.split(',')
    conn, c = create_connection('authorized_users')
    data = c.execute("SELECT salt, salted_hash FROM users WHERE username = ?", [username.lower()]).fetchall()
    if len(data) != 0:
        salt = data[0][0]
        salted_hash = data[0][1]
        if is_correct_password(salt, salted_hash, password):
            token = generate_token()
            exp = datetime.now() + timedelta(minutes=10)
            c.execute("INSERT INTO tokens (token, expiration) VALUES (?,?);", [token, exp])
            conn.commit()
    conn.close()
    return token


def process_token(token):
    conn, c = create_connection('authorized_users')
    data = c.execute("SELECT expiration FROM tokens WHERE token = ?",  [token]).fetchall()
    result = False
    if len(data) != 0:
        if datetime.fromisoformat(data[0][0]) > datetime.now():
            expiration = datetime.now() + timedelta(minutes=10)
            c.execute("UPDATE tokens SET expiration = ? WHERE token = ?;", [expiration, token])
            result = True
        else:
            c.execute("DELETE FROM tokens WHERE token = ?;", [token])
        conn.commit()
    conn.close()
    return result


def is_correct_password(salt: bytes, pw_hash: bytes, password: str) -> bool:
    """
    Given a previously-stored salt and hash, and a password provided by a user
    trying to log in, check whether the password is correct.z
    """
    return hmac.compare_digest(pw_hash, hashlib.pbkdf2_hmac('sha512', password.encode(), salt, 100000))


def generate_token():
    token = ""
    for a in range(9):
        token += str(uuid.uuid4()).replace("-", "")
    return token


def save_token(token):
    conn, c = create_connection('authorized_users')
    current_time = datetime.today()
    c.execute("INSERT OR REPLACE INTO tokens (token, exp) VALUES (?,?);",
              [token.replace('"', ""), current_time + timedelta(days=3)])
    conn.commit()
    conn.close()


def log_in(username: str, password: str):
    conn, c = create_connection('authorized_users')
    data = c.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
    conn.close()
    data = data[0]
    salt = data[1]
    pw_hash = data[2]
    result = is_correct_password(salt, pw_hash, password)
    if result:
        token = generate_token()
        return token
    else:
        return False


def hash_new_password(password: str) -> Tuple[bytes, bytes]:
    """
    Hash the provided password with a randomly-generated salt and return the
    salt and hash to store in the database.
    """
    import random
    salt = None
    for a in range(random.randrange(1, 10)):
        salt = os.urandom(32)

    pw_hash = hashlib.pbkdf2_hmac('sha512', password.encode(), salt, 100000)

    return salt, pw_hash


def create_new_user(username, password):
    conn, c = create_connection('authorized_users')

    sql = "SELECT * FROM users WHERE username = ?"
    val = [username]
    c.execute(sql, val)

    if not check_if_user_exists(username):

        salt, salted_hash = hash_new_password(password)

        sql = "INSERT INTO users (username, name, salt, salted_hash, roles, date_created) VALUES (?,?,?,?,?,?);"
        val = [username.lower(), username, salt, salted_hash, json.dumps(['admin']), datetime.now()]
        c.execute(sql, val)
        conn.commit()
        print("User Successfully Added")
    else:
        print("User Already Exists")
    conn.close()


def check_if_user_exists(username):
    conn, c = create_connection('authorized_users')
    data = c.execute("SELECT * FROM users WHERE username = ?", [username.lower()]).fetchall()
    if len(data) == 0:
        return False
    else:
        return True


if __name__ == "__main__":
    initialize_authorized_users_database()
    create_new_user("Jay", "JZv4G7FjuZlY38FekfY2PPo%sf9gc@ut")
