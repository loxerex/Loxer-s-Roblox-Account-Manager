import sys
import tkinter as tk
import keyring
from pathlib import Path
from threading import Thread
from tkinter import Menu
import time
import customtkinter as ctk

import Data.JsonManager as JsonManager
import Handlers.BrowserHandler as BrowserHandler
import Handlers.TeleportHandlerR as TeleportHandler
import Util.Mutli_Instance as Mutli_Instance

from Util.Account import Account, Accounts, Status

MAIN_SERVICE_NAME = "my-roblox-account-manager-service"

# Resolve base directory (supports PyInstaller)
BASE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent


class RobloxAccountManager:

    def __init__(self):
        self.data = JsonManager.load_data()

        # state
        self.account_dict = {}
        self.table_data = []
        self.rows = []
        self.selected_row = None
        self.selected_user = None
        self.current_page = "Accounts"

        self.setup_window()
        self.load_accounts()
        self.setup_ui()
        if self.data["Settings"]["Auto_Enable_Multi_Instance"]:
            Mutli_Instance.enable_roblox_multi_instance()
        self.window.mainloop()

    # window setup: Geometry, title, icon
    def setup_window(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()
        self.window.title("LXA Account Manager")
        self.window.geometry("1000x500")
        self.window.resizable(False, False)
        self.add_game_frame = None
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(0, weight=1)

        icon = tk.PhotoImage(file=BASE_DIR / "Resources" / "Icon.png")
        self.window.after(200, lambda: self.window.iconphoto(False, icon))

    # ui setup: sidebar, main area, context menu, pages,
    def setup_ui(self):

        self.setup_main_area()
        self.setup_context_menu()

        self.page_frames = {
            "Accounts": self.build_accounts_page(),
            "Game Catalogue": self.build_game_catalogue_page(),
            "Settings": self.build_settings_page()
        }

        self.setup_sidebar()

        for frame in self.page_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.switch_page("Accounts")
        Thread(target=self.status_check,daemon=True).start()

    # sidebar setup
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.window, width=240, fg_color="#0B0B0C")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self._build_logo()
        self._build_nav()

    # adds logo
    def _build_logo(self):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.pack(fill="x", padx=18, pady=(20, 18))

        ctk.CTkLabel(frame, text="LXA",
                     font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w")

        ctk.CTkLabel(frame, text="Roblox Account Manager",
                     text_color="#707070",
                     font=ctk.CTkFont(size=12)).pack(anchor="w")
    # adds navigation buttons for each page in self.page_frames
    def _build_nav(self):
        self.nav_buttons = {}

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=12)

        pages = list(self.page_frames.keys())

        for page in pages:
            btn = ctk.CTkButton(
                nav,
                text=page,
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color="transparent",
                hover_color="#191919",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda p=page: self.switch_page(p)
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[page] = btn

    # main_frame setup
    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self.window, fg_color="#111111")
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.setup_topbar()

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def setup_topbar(self):
        topbar = ctk.CTkFrame(self.main_frame, height=70, fg_color="#111111")
        topbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))

        self.page_title = ctk.CTkLabel(
            topbar,
            text="Accounts",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.page_title.grid(row=0, column=0, sticky="w")

    # page switching: using tkraise for each page frame
    def switch_page(self, page):
        self.current_page = page
        self.page_title.configure(text=page)

        for b in self.nav_buttons.values():
            b.configure(fg_color="transparent")

        self.nav_buttons[page].configure(fg_color="#1D4ED8")

        if page in self.page_frames:
            self.page_frames[page].tkraise()

    # context menu: simple context menu for open,delete,rename
    def setup_context_menu(self):
        self.menu = Menu(
            self.window,
            tearoff=0,
            bg="#111111",
            fg="white",
            activebackground="#1f6aa5",
            activeforeground="white",
            borderwidth=0
        )

        self.menu.add_command(
            label="Open Account",
            command=lambda: Thread(
                target=BrowserHandler.open_roblox_account,
                args=[self.selected_user],
                daemon=True
            ).start()
        )

        self.menu.add_command(label="Rename Account", command=self.change_nickname)
        self.menu.add_separator()
        self.menu.add_command(label="Delete Account", command=self.delete_account)

    # account loading
    def load_accounts(self):
        for account in self.data["Accounts"]:
            try:
                data = self.data["Accounts"][str(account)]

                cookie = keyring.get_password(
                    MAIN_SERVICE_NAME+"_cookie",
                    str(account)
                )

                acc = Account(cookie)
                Accounts.append(acc)

                name = data["username"]
                if data.get("nickname"):
                    name = data["nickname"]

                self.account_dict[account] = acc

                status = Status.Offline

                self.table_data.append([name, account, status])

            except Exception as e:
                print("error loading account:", e)

    # table functionality
    def load_table_data(self, get_acc_obj: Account | None = None):
        self.selected_row = None
        self.selected_user = None

        if get_acc_obj is not None:
            self.update_table_data(get_acc_obj)
        else:
            self.update_table_data()

        for w in self.table_frame.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                w.destroy()

        self.rows.clear()

        for name, userid, status in self.table_data:
            row = ctk.CTkFrame(
                self.table_frame,
                fg_color="#1A1A1A",
                corner_radius=8,
                height=40
            )
            row.pack(fill="x", pady=4, padx=4)

            name_box = ctk.CTkTextbox(
                row,
                width=180,
                height=28,
                fg_color="#1A1A1A",
                text_color="white",
                corner_radius=6,
                border_width=0
            )
            name_box.pack(side="left", padx=(12, 6), pady=6)
            name_box.insert("end", name)
            name_box.configure(state="disabled")

            id_label = ctk.CTkLabel(
                row,
                text=str(userid),
                anchor="w",
                text_color="#A0A0A0",
                width=150
            )
            id_label.pack(side="left", padx=6)

            print(status)
            status_label = ctk.CTkLabel(
                row,
                text=status,
                anchor="w",
                text_color="#6CCF6C" if status == Status.Online or status == Status.Active else "#CFCFCF",
                width=160
            )
            status_label.pack(side="left", padx=6)

            self.rows.append(row)
            self.bind_row_click(row)

    def bind_row_click(self, row):
        row.bind("<Button-1>", lambda e: self.select_row(row))
        row.bind("<Button-3>", lambda e: self.show_menu(e, row))

        for child in row.winfo_children():
            child.bind("<Button-1>", lambda e: self.select_row(row))
            child.bind("<Button-3>", lambda e: self.show_menu(e, row))

    def update_table_data(self, get_acc_obj: Account | None = None):
        if get_acc_obj is None:
            self.table_data.clear()
        json_accounts = JsonManager.load_data()["Accounts"]
        print(f"Size of json accounts: {len(json_accounts)}")
        self.account_count.configure(text=f"{len(json_accounts)} Accounts")
        for account in json_accounts:
            if get_acc_obj is not None and account in self.account_dict:
                continue
            data = json_accounts[str(account)]
            name = data["username"]

            if data.get("nickname"):
                name = data["nickname"]
            else:
                print("No nickname")

            if self.account_dict.get(account) is None:
                self.account_dict[account] = get_acc_obj
                Accounts.append(get_acc_obj)

            account_obj = self.account_dict[account]
            status = Status.Offline

            if [name, account, status] in self.table_data:
                self.table_data.remove([name, account, status])
            self.table_data.append([name, account, status])

    # account actions
    def change_nickname(self):
        if not self.selected_row:
            return

        account_id = self.selected_row.winfo_children()[1].cget("text").strip()
        print("configured")
        self.selected_row.winfo_children()[0].configure(state="normal")
        def update_nickname(new_nickname):
            print("updated nickname")
            self.selected_row.winfo_children()[0].configure(state="disabled")
            JsonManager.change_nickname(account_id, new_nickname)
        self.selected_row.winfo_children()[0].bind("<Return>", lambda e: update_nickname(self.selected_row.winfo_children()[0].get("1.0", "end").strip()))

    def delete_account(self):
        if not self.selected_row:
            return

        account_id = self.selected_row.winfo_children()[1].cget("text").strip()

        acc = self.account_dict.get(account_id)
        if acc:
            Accounts.remove(acc)
            self.account_dict.pop(account_id, None)

        JsonManager.delete_account(account_id)

        self.selected_row.destroy()
        self.selected_row = None

    def threaded_join_game(self):
        print(self.selected_user, self.game_id.get())
        Thread(
            target=self.join_game_logic,
            args=(self.selected_user, self.game_id.get()),
            daemon=True
        ).start()

    # helpers n other functions

    def join_game_logic(self, account, game_id):
        if not game_id:
            return
        try:
            IsPrivate = "share?code" in game_id or "privateServerLinkCode" in game_id
            TeleportHandler.join_game(self.account_dict[account], IsPrivate, game_id)
        except Exception as e:
            print(f"Error joining game: {e}")

    def status_check(self):
        print("Status check started")
        while True:
            p_row = len(self.rows)
            for row in self.rows:
                try:
                    if len(self.rows) != p_row:
                        break

                    row_account = row.winfo_children()[1].cget("text").strip()

                    if self.account_dict.get(row_account):
                        status = self.account_dict.get(row_account).status
                        try:
                            row.winfo_children()[2].configure(text=status, text_color="#6CCF6C" if status.value == 1 or status.value == 2 else "#CFCFCF")
                        except Exception as e:
                            print(f"Error updating status for {row_account}: {e}")
                    else:
                        print(self.account_dict )
                        print("No account found")
                except Exception as e:
                    print(f"Error during status check: {e}")
                    time.sleep(5)
                time.sleep(2)
            time.sleep(3)

    def create_card(self, parent, title, subtitle=None):
        card = ctk.CTkFrame(
            parent,
            fg_color="#171717",
            corner_radius=14,
            border_width=1,
            border_color="#242424"
        )

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))

        ctk.CTkLabel(header, text=title,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(header, text=subtitle,
                         text_color="#777777",
                         font=ctk.CTkFont(size=11)).pack(anchor="w")

        return card
    def select_row(self, row):
        if self.safe_widget(self.selected_row):
            self.selected_row.configure(fg_color="#1A1A1A")

        self.selected_row = row
        self.selected_user = row.winfo_children()[1].cget("text").strip()

        if self.safe_widget(self.selected_row):
            self.selected_row.configure(fg_color="#23222C")

        print(self.selected_user)

    def toggle_setting(self, setting_key):
        setting_value = self.switch_settings[setting_key].get()
        if setting_value == 1:
            setting_value = True
            if setting_key == "Auto_Enable_Multi_Instance":
                Mutli_Instance.enable_roblox_multi_instance()
        else:
            setting_value = False
        JsonManager.update_setting(setting_key, setting_value)


    def show_menu(self, event, row):
        self.select_row(row)
        self.menu.tk_popup(event.x_root, event.y_root)
    def save_game_id(self):
        JsonManager.update_setting(
            "Saved_Game_ID",
            int(self.game_id.get())
            if self.game_id.get().isdigit()
            else None
        )
    @staticmethod
    def safe_widget(widget):
        return widget and widget.winfo_exists()

    # pages
    def build_accounts_page(self):
        container = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )

        container.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        container.grid_columnconfigure(0, weight=4)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        accounts_card = self.create_card(
            container,
            "Accounts",
            "Manage Roblox accounts"
        )

        accounts_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        self.account_count = ctk.CTkLabel(
            accounts_card,
            text="0 Accounts",
            fg_color="#111111",
            corner_radius=8,
            height=28,
            width=100
        )

        self.account_count.pack(
            anchor="e",
            padx=14,
            pady=(0, 8)
        )

        self.table_frame = ctk.CTkScrollableFrame(
            accounts_card,
            fg_color="#101010",
            corner_radius=12
        )

        self.table_frame.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 14)
        )

        # headers
        header = ctk.CTkFrame(
            self.table_frame,
            fg_color="#1A1A1A",
            corner_radius=10,
            height=42
        )

        header.pack(fill="x", pady=(0, 6))

        headers = [
            ("Account", 260),
            ("User ID", 200),
            ("Status", 180)
        ]

        for text, width in headers:
            ctk.CTkLabel(
                header,
                text=text,
                width=width,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=10, pady=10)

        # panel
        action_card = self.create_card(
            container,
            "Quick Actions",
            "Launch and manage"
        )

        action_card.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.game_id = ctk.CTkEntry(
            action_card,
            placeholder_text="Enter Game ID",
            height=38
        )

        self.game_id.pack(
            fill="x",
            padx=14,
            pady=(0, 10)
        )

        saved_game_id = self.data["Settings"]["Saved_Game_ID"]

        if saved_game_id:
            self.game_id.insert(0, str(saved_game_id))

        buttons = [
            ("Launch Game", self.threaded_join_game),
            (
                "Add Account",
                lambda: Thread(
                    target=BrowserHandler.add_roblox_account,
                    args=[self.load_table_data],
                    daemon=True
                ).start()
            ),
            ("Save Game ID", self.save_game_id)
        ]

        for text, command in buttons:
            ctk.CTkButton(
                action_card,
                text=text,
                height=40,
                corner_radius=10,
                command=command
            ).pack(fill="x", padx=14, pady=4)

        self.load_table_data()
        return container

    def build_game_catalogue_page(self):
        card = self.create_card(
            self.content_frame,
            "Game Catalogue",
            "Saved experiences"
        )

        card.grid(row=0, column=0, sticky="nsew")


        ctk.CTkButton(
                card.winfo_children()[0] ,
                text="Add Game",
                width=120,
                height=32,
                corner_radius=8,
                fg_color="#1D4ED8",
                hover_color="#2563EB",
                command=self.open_add_game_menu
            ).pack(side="right", padx=4)

        # game frame
        self.games_frame = ctk.CTkScrollableFrame(
            card,
            fg_color="#101010"
        )
        self.games_frame.pack(fill="both", expand=True, padx=14, pady=(10, 14))

        self.load_games()

        return card

    def load_games(self):
        print("loading games")
        for widget in self.games_frame.winfo_children():
            widget.destroy()

        saved = JsonManager.load_data().get("Saved_Games", {})
        instance = 0
        for title, game_id in saved.items():
            self.create_game_card(title, game_id, instance)
            instance += 1

    def create_game_card(self, game_title, game_id, instance):

        card = ctk.CTkFrame(
            self.games_frame,
            fg_color="#181818",
            corner_radius=12,
            border_width=1,
            border_color="#2a2a2a",
            width=160,
            height=200
        )

        row = instance // 3
        col = instance % 3
        self.games_frame.grid_columnconfigure(col, weight=0)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="n")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            content,
            text=game_title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        label_text = game_id if len(game_id) <= 20 else game_id[:20] + "..."
        ctk.CTkLabel(
            content,
            text=f"ID: {label_text}",
            text_color="#777777",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(side="bottom", pady=10)

        def set_game():
            self.game_id.delete(0, "end")
            self.game_id.insert(0, str(game_id))

        def delete_game():
            JsonManager.remove_saved_game(game_title)
            card.destroy()

        ctk.CTkButton(
            btn_row,
            text="Set",
            width=60,
            height=28,
            fg_color="#1D4ED8",
            hover_color="#2563EB",
            command=set_game
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Del",
            width=60,
            height=28,
            fg_color="#B91C1C",
            hover_color="#DC2626",
            command=delete_game
        ).pack(side="left", padx=5)

    def open_add_game_menu(self):
        if self.add_game_frame is None:
            self.add_game_frame = ctk.CTkFrame(
                self.content_frame,
                fg_color="#101010",
                corner_radius=0
            )

            self.add_game_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.add_game_frame.lift()
        self.add_game_frame.tkraise()

        for w in self.add_game_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.add_game_frame,
            text="Add Game",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(18, 10))

        ctk.CTkLabel(self.add_game_frame, text="Game Name", text_color="#aaa").pack()
        name_entry = ctk.CTkEntry(self.add_game_frame, width=240)
        name_entry.pack(pady=(2, 10))

        ctk.CTkLabel(self.add_game_frame, text="Game ID", text_color="#aaa").pack()
        id_entry = ctk.CTkEntry(self.add_game_frame, width=240)
        id_entry.pack(pady=(2, 15))

        def close():
            self.add_game_frame.lower()

        def submit():
            name = name_entry.get().strip()
            game_id = id_entry.get().strip()

            if not name or not game_id:
                return

            JsonManager.add_saved_game(name, game_id)
            self.load_games()
            close()

        # buttons row
        btn_row = ctk.CTkFrame(self.add_game_frame, fg_color="transparent")
        btn_row.pack(pady=10)

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=100,
            fg_color="#333333",
            hover_color="#444444",
            command=close
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Add",
            width=100,
            fg_color="#1D4ED8",
            hover_color="#2563EB",
            command=submit
        ).pack(side="left", padx=5)
    def build_settings_page(self):
        card = self.create_card(
            self.content_frame,
            "Settings",
            "Application configuration"
        )

        card.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        inner = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        inner.pack(fill="both", expand=True, padx=14, pady=14)

        settings = [
            "Auto_Enable_Multi_Instance",
        ]
        self.switch_settings = {}
        for setting in settings:
            row = ctk.CTkFrame(
                inner,
                fg_color="#1A1A1A",
                corner_radius=10,
                height=48
            )

            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row,
                text=setting,
                font=ctk.CTkFont(size=13)
            ).pack(side="left", padx=14)

            switch = ctk.CTkSwitch(
                row,
                text="",
                command=lambda  setting=setting: self.toggle_setting(setting)
            )
            if self.data["Settings"][setting]:
                switch.select()
            self.switch_settings[setting] = switch
            switch.pack(side="right", padx=14)
        return card


if __name__ == "__main__":
    RobloxAccountManager()
