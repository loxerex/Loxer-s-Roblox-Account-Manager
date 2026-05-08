import json
import os
import keyring
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

MAIN_SERVICE_NAME = "my-roblox-account-manager-service"

#json file path
JSON_FILE_PATH = os.path.join(BASE_DIR,"RAM.json")
print(JSON_FILE_PATH)
JSON_FORMAT ={
        "Accounts": {},
        "Saved_Games":{

        },
        "Settings":{
            "Auto_Enable_Multi_Instance": True,
            "Saved_Game_ID": None
        }
    }

JSON_ACCOUNT_FORMAT= { "username": "", "nickname": "", "cookie_expire": "", "password": "" }

def load_data():
    global JSON_DATA
    if not os.path.isfile(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'w') as json_file:
            json.dump(JSON_FORMAT, json_file, indent=4)
            print("created")

    with open(JSON_FILE_PATH, 'r') as f:
        JSON_DATA = json.load(f)
    return JSON_DATA
def save_data(data):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)
def add_saved_game(game_title, game_id):
    data = load_data()
    data["Saved_Games"][game_title] = game_id
    save_data(data)
def remove_saved_game(game_title):
    data = load_data()
    if data["Saved_Games"].get(game_title):
        data["Saved_Games"].pop(game_title)
        save_data(data)
def delete_account(user_id):
    print(user_id)
    data = load_data()
    if data["Accounts"].get(user_id):
        acc = data["Accounts"][user_id]
        print("found")
        data["Accounts"].pop(user_id)
        try:
            keyring.delete_password(
                MAIN_SERVICE_NAME+"_cookie",
                str(user_id)
            )
            keyring.delete_password(
                MAIN_SERVICE_NAME+"_password",
                str(user_id)
            )
        except Exception as e:
            print("Error deleting password/cookie:", e)
        save_data(data)
        return True
    return False
def get_cookie(user_id):
    cooike = None
    data = load_data()
    if data["Accounts"].get(user_id):
        acc = data["Accounts"][user_id]
        try:
            cookie = keyring.get_password(
                MAIN_SERVICE_NAME+"_cookie",
                str(user_id)
            )
            return cookie
        except Exception as e:
            print(e)
    return cooike


def add_account(account_name, user_id, cookie_expire,  password: str | None=None, cookie: str | None=None, ):
    data = load_data()
    print(user_id)
    if len(data["Accounts"])>0:
        if user_id in data["Accounts"]:
            return False

    ACCOUNT = JSON_ACCOUNT_FORMAT.copy()
    ACCOUNT["username"] = account_name
    ACCOUNT["password"] = password
    try:
        if cookie:
            keyring.set_password(
                MAIN_SERVICE_NAME+"_cookie",
                str(user_id),
                cookie
            )

        if password:
            keyring.set_password(
                MAIN_SERVICE_NAME+"_password",
                str(user_id),
                password
            )
    except Exception as e:
        print("yo gang error", e)
        return False
    ACCOUNT['cookie_expire'] = cookie_expire
    data["Accounts"][user_id] = ACCOUNT
    save_data(data)
    return True

def change_nickname(user_id, new_nickname):
    data = load_data()
    if data["Accounts"].get(user_id):
        acc = data["Accounts"][user_id]
        acc['nickname'] = new_nickname
        save_data(data)
        return True
    return False

def update_setting(setting_key, setting_value):
    print(setting_value)
    data = load_data()
    if 'Settings' not in data:
        data['Settings'] = {}
    data['Settings'][setting_key] = setting_value
    save_data(data)
    return True

def update_account_data(user_id, newinfo: tuple):
    cur_data = load_data()
    if cur_data["Accounts"].get(user_id):
        found_account = cur_data["Accounts"][user_id]
        print(*newinfo)
        for change in newinfo:
            try:
                found_account[change[0]] = change[1]
                print(f"Key {change[0]} was turned into {change[1]}")
            except Exception as e:
                print(e)
    save_data(cur_data)
