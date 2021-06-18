import shutil
from getpass import getpass
import sqlite3

from colorama import Fore, Style, init
from misc import ask

from database_sdk import (
    PASSWORD_CONN,
    STORAGE_CONN,
    add_user,
    change_master_password,
    delete_all_users,
    delete_user,
    get_all_files_stored,
    get_all_users,
    get_user,
    make_password,
    preview,
    restore,
    store,
    temp_dir,
    update_user,
)
from settings import (
    ENABLE_AUTOCOMPLETE,
    ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE,
    PASSWORD_GENERATION_TYPE,
    PRINT_INFO_ON_START,
)

init()


def info():
    print(Fore.GREEN)
    print("-------------------------------------------")
    print("q/exit/quit/stop: Quit")
    print("np: Add a new user")
    print("up: Update an existing user")
    print("gp: Get the password of a user")
    print("gpall: Get all of the passwords you have")
    print("dp: Deletes an user")
    print("dpall: Deletes all the users")
    print("mp: Generate a new strong password for you")
    print("cp: Change the master password")
    print("store: Store a file from your computer into database")
    print("preview: Preview a file from the databse")
    print("restore: Restore a file from the database to the computer")
    print("info/help: Print this message")
    print("-------------------------------------------")
    print(Style.RESET_ALL)


if PRINT_INFO_ON_START:
    info()

modes = {
    "exit": ["q", "exit", "quit", "stop"],
    "add_user": ["np"],
    "update_user": ["up"],
    "get_user": ["gp"],
    "get_all_users": ["gpall"],
    "delete_user": ["dp"],
    "delete_all_users": ["dpall"],
    "make_password": ["mp"],
    "change_master_password": ["cp"],
    "store": ["store"],
    "preview": ["preview"],
    "restore": ["restore"],
    "info": ["info", "help"],
}


if ENABLE_AUTOCOMPLETE:
    import readline

    class AutoCompleter:
        def __init__(self, options):
            self.options = sorted(options)

        def complete(self, text, state):
            response = None
            if state == 0:
                # This is the first time for this text, so build a match list.
                if text:
                    self.matches = [s for s in self.options if s and s.startswith(text)]
                else:
                    self.matches = self.options[:]

            # Return the state'th item from the match list,
            # if we have that many.
            try:
                response = self.matches[state]
            except IndexError:
                response = None
            return response

    class StorageCompleter:
        def __init__(self, options):
            self.options = sorted(options)

        def complete(self, text, state):
            response = None
            if state == 0:
                # This is the first time for this text, so build a match list.
                if text:
                    self.matches = [s for s in self.options if s and s.startswith(text)]
                else:
                    self.matches = self.options[:]

            # Return the state'th item from the match list,
            # if we have that many.
            try:
                response = self.matches[state]
            except IndexError:
                response = None
            return response

    modes_list = [val for key in modes for val in modes[key]]

    readline.set_completer(AutoCompleter(modes_list).complete)
    readline.parse_and_bind("tab: complete")

try:

    while True:
        mode = ask("What do you want to do?: ")
        if mode is None:
            continue

        mode = mode.rstrip()

        if mode in modes["exit"]:
            break

        if mode in modes["add_user"]:
            username = ask("What's the username: ").lower()
            password = getpass("What's the password: ")
            if username is not None and password is not None:
                add_user(username, password)

        elif mode in modes["delete_user"]:
            username = ask("Type the username you want to remove: ")
            if username is not None:
                delete_user(username)

        elif mode in modes["update_user"]:
            username = ask("Type the username you want to update: ")
            if username is not None:
                update_user(username)

        elif mode in modes["get_user"]:
            username = ask("Type the username: ")
            if username is not None:
                get_user(username)

        elif mode in modes["get_all_users"]:
            users = get_all_users()

        elif mode in modes["delete_all_users"]:
            delete_all_users()

        elif mode in modes["make_password"]:  # Make or generate password
            username = ask("What's the username: ")
            if PASSWORD_GENERATION_TYPE.lower() == "ask":
                if ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE:
                    import inquirer

                    options = [
                        inquirer.List(
                            "PASSWORD_GENERATION_TYPE",
                            message="Which method to generate password?: ",
                            choices=["diceware", "random"],
                        ),
                    ]
                    answer = inquirer.prompt(options)
                    password_method = answer["PASSWORD_GENERATION_TYPE"]
                else:
                    password_method = ask(
                        "Type the method to generate passsword:\n(d)iceware, (r)andom. Default is diceware: "
                    )
                    if password_method in ["r", "random"]:
                        password_method = "random"
                    else:
                        password_method = "diceware"
            else:
                password_method = PASSWORD_GENERATION_TYPE
            length = eval(ask("Type the length of the password: "))
            add_user(username, make_password(length, password_method.lower()))

        elif mode in modes["change_master_password"]:
            change_master_password()

        elif mode in modes["store"]:
            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(None)

            filename = ask("Type the filename: ")
            if filename is not None:
                store(filename)

            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(AutoCompleter(modes_list).complete)

        elif mode in modes["preview"]:
            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(
                    StorageCompleter(get_all_files_stored()).complete
                )

            filename = ask("Type the filename: ")
            if filename is not None:
                preview(filename)

            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(AutoCompleter(modes_list).complete)

        elif mode in modes["restore"]:
            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(
                    StorageCompleter(get_all_files_stored()).complete
                )

            filename = ask("Type the filename to restore: ")
            if filename is not None:
                restore(filename)

            if ENABLE_AUTOCOMPLETE:
                readline.set_completer(AutoCompleter(modes_list).complete)

        elif mode in modes["info"]:
            info()

    shutil.rmtree(temp_dir)
    PASSWORD_CONN.close()
    STORAGE_CONN.close()
except Exception as e:
    print(e)
    shutil.rmtree(temp_dir)
    PASSWORD_CONN.close()
    STORAGE_CONN.close()
