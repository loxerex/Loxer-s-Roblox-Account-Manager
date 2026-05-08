from http.client import responses
from pydoc import resolve
from playwright.sync_api import sync_playwright
import os
import sys

from rblib import r_account
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Data.JsonManager as JsonManager
import requests
from Util import Account
from Util.Account import Accounts, Account as ac
import time
import re
from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

firefox_path = BASE_DIR / "ms-playwright" / "firefox-1497" / "firefox" / "firefox.exe"

def open_roblox_account(account: str):
    with sync_playwright() as p:
        browser = p.firefox.launch(
            executable_path=str(firefox_path),
            headless=False,
            firefox_user_prefs={}
        )
        context = browser.new_context()

        cookie = JsonManager.get_cookie(account)
        context.add_cookies([{
            "name": ".ROBLOSECURITY",
            "value": f"{cookie}",
            "domain": ".roblox.com",
            "path": "/",
            "httpOnly": True,
            "secure": True
        }])

        page = context.new_page()
        page.goto("https://www.roblox.com/home", wait_until="domcontentloaded")
        print("Opened Roblox account.")
        print(browser.is_connected())
        while browser.is_connected(): # Use browser.is_connected() to check internal status
            try:
                # Perform a very simple, non-disruptive action
                title = page.title()

                time.sleep(1)
            except Exception as e:
                if "Target page, context or browser has been closed" in str(e):
                    break
            # Handle other potential exceptions



def add_roblox_account(callback):
    with sync_playwright() as p:
        browser = p.firefox.launch(
            executable_path=str(firefox_path),
            headless=False,
            firefox_user_prefs={}
        )
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://www.roblox.com/login", wait_until="domcontentloaded")

        page.wait_for_url("https://www.roblox.com/home")
        print("Logged in to Roblox.")
        # Assuming 'context' is your Playwright BrowserContext
        cookies = context.cookies()
        user = page.locator(".text-overflow.age-bracket-label-username.font-caption-header")

        # Find the .ROBLOSECURITY cookie in the list
        roblosecurity = next((c for c in cookies if c['name'] == '.ROBLOSECURITY'), None)
        if roblosecurity:
            expire = roblosecurity['expires']
            cur_account = ac(roblosecurity['value'])
            print(cur_account)
            print(cur_account.name)
            JsonManager.add_account(account_name=cur_account.name, user_id=cur_account.userId, cookie_expire=expire, cookie=roblosecurity['value'])

        else:
            print("ROBLOSECURITY cookie not found. Check if login was successful.")

        browser.close()
        if cur_account:
            print(cur_account)
            callback(cur_account)
        else:
            callback()
def resolve_url(url: str, acccount: r_account.Account):
     with sync_playwright() as p:
        browser = p.firefox.launch(
            executable_path=str(firefox_path),
            headless=True,
            firefox_user_prefs={}
        )
        context = browser.new_context()
        context.add_cookies([{
            "name": ".ROBLOSECURITY",
            "value": acccount.UserCookie,
            "domain": ".roblox.com",
            "path": "/",
            "httpOnly": True,
            "secure": True
        }])
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_url("**privateServerLinkCode**")
        resolved_url = page.url
        browser.close()
        return resolved_url

def cookie_refersh():
     with sync_playwright() as p:
        browser = p.firefox.launch(
            executable_path=str(firefox_path),
            headless=False,
            firefox_user_prefs={}
        )
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://www.roblox.com/home", wait_until="domcontentloaded")

        print("Logged in to Roblox.")
        # grab cookies
        cookies = context.cookies()
        user = page.locator(".text-overflow.age-bracket-label-username.font-caption-header")

        # Find the .ROBLOSECURITY cookie in the list
        roblosecurity = next((c for c in cookies if c['name'] == '.ROBLOSECURITY'), None)
        if roblosecurity:
            expire = roblosecurity['expires']
            JsonManager.update_account_data(account=user.inner_text(),newinfo=[('cookie', roblosecurity['value']),['cookie_expire',expire]])
        else:
            print("ROBLOSECURITY cookie not found. Check if login was successful.")

        browser.close()
