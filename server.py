from flask import Flask, render_template, request
from database_tools import get_user_list, get_message_list, get_scheduler_list, get_banned_list, delete_scheduled_message
from mod_tools import admin_ban, admin_unban, send_a_message, reset_warnings, reset_unlocks
from auth import initialize_authorized_users_database
import json
from auth import process_login, process_token

app = Flask(__name__)
initialize_authorized_users_database()


@app.route('/')
def home_link():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            return render_template('index.html')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/login', methods=["POST"])
def login():
    data = request.data
    if data != b',' and data != b'':
        token = process_login(data.decode('utf-8'))
        return {"token": token}
    else:
        return render_template('login.html', )


@app.route('/getUserList')
def get_user_list_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            user_list = get_user_list()
            response = {"result": "Success", "data": user_list}
            return json.dumps(response)


@app.route('/getMessageList')
def get_messsage_list_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            message_list = get_message_list()
            response = {"result": "Success", "data": message_list}
            return json.dumps(response)


@app.route('/getSchedulerList')
def get_scheduler_list_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            scheduler_list = get_scheduler_list()
            response = {"result": "Success", "data": scheduler_list}
            return json.dumps(response)


@app.route('/getBannedList')
def get_banned_list_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            banned_list = get_banned_list()
            response = {"result": "Success", "data": banned_list}
            return json.dumps(response)


@app.route('/deleteScheduledMessage', methods=["POST"])
def delete_scheduled_message_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = delete_scheduled_message(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No message IDs were supplied to delete"})


@app.route('/unbanUser', methods=["POST"])
def unban_user_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = admin_unban(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No user IDs were supplied to unban"})


@app.route('/banUser', methods=["POST"])
def ban_user_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = admin_ban(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No user IDs were supplied to ban"})


@app.route('/resetWarnings', methods=["POST"])
def reset_warnings_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = reset_warnings(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No user IDs were supplied to reset warnings"})


@app.route('/resetUnlocks', methods=["POST"])
def reset_unlocks_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = reset_unlocks(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No user IDs were supplied to reset unlocks"})


@app.route('/sendAMessage', methods=["POST"])
def send_message_call():
    token = request.cookies.get('token')
    if token is not None:
        if process_token(token):
            if request.data != bytes():
                result = send_a_message(request.data.decode('utf-8'))
                return json.dumps({"result": result})
            else:
                return json.dumps({"result": "Failed: No message was provided to send"})


if __name__ == '__main__':
    app.run()
