import shutil
from getpass import getpass

from colorama import Fore, Style, init

from database_sdk import (PASSWORD_CONN, STORAGE_CONN, add_user,
                          change_master_password, check_passwords, delete_all_users,
                          delete_user, get_all_files_stored, get_all_users,
                          get_user, make_password, preview, restore, store, check_passwords,
                          temp_dir, update_user)
from misc import ask
from settings import (ENABLE_AUTOCOMPLETE,
                      ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE,
                      PASSWORD_GENERATION_TYPE, PRINT_INFO_ON_START)
import cmd

init()

if ENABLE_AUTOCOMPLETE:
    import readline

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

if ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE:
    import inquirer

    password_options = [
        inquirer.List(
            "PASSWORD_GENERATION_TYPE",
            message="Which method to generate password?: ",
            choices=["diceware", "random"],
        ),
    ]


msg = Fore.GREEN + """-------------------------------------------
exit: Quit
np: Add a new user
up: Update an existing user
gp: Get the password of a user
gpall: Get all of the passwords you have
dp: Deletes an user
dpall: Deletes all the users
mp: Generate a new strong password for you
cp: Change the master password
check: Check if any of your password has been pwned
store: Store a file from your computer into database
preview: Preview a file from the databse
restore: Restore a file from the database to the computer
help: Print this message
-------------------------------------------""" + Style.RESET_ALL


class PasswordManagerShell(cmd.Cmd):
    prompt = "What do you want to do: "
    doc_header = msg + "\nDocumented commands (type help <topic>):"
    ruler = ""
    if PRINT_INFO_ON_START:
        intro = msg

    def do_np(self, args):
        "Add a new user"
        username = ask("What's the username: ").lower()
        password = getpass("What's the password: ")
        if username is not None and password is not None:
            add_user(username, password)

    def do_up(self, args):
        "Update an existing user"
        username = ask("Type the username you want to update: ")
        if username is not None:
            update_user(username)

    def do_dp(self, args):
        "Deletes an user"
        username = ask("Type the username you want to remove: ")
        if username is not None:
            delete_user(username)

    def do_dpall(self, args):
        "Delete all users and their passwords"
        delete_all_users()

    def do_gp(self, args):
        "Get the password of a user"
        username = ask("Type the username: ")
        if username is not None:
            get_user(username)

    def do_gpall(self, args):
        "Get all of the passwords you have"
        get_all_users()

    def do_mp(self, args):
        "Generate a new strong password for you"
        username = ask("What's the username: ")
        if PASSWORD_GENERATION_TYPE.lower() == "ask":
            if ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE:
                answer = inquirer.prompt(password_options)
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

    def do_cp(self, args):
        "Change the master password"
        change_master_password()

    def do_store(self, args):
        "Store a file from your computer into database"
        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(None)

        filename = ask("Type the filename: ")
        if filename is not None:
            store(filename)

        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(self.complete)

    def do_preview(self, args):
        "Preview a file from the databse"
        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(
                StorageCompleter(get_all_files_stored()).complete
            )

        filename = ask("Type the filename: ")
        if filename is not None:
            preview(filename)

        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(self.complete)

    def do_restore(self, args):
        "Restore a file from the database to the computer"
        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(
                StorageCompleter(get_all_files_stored()).complete
            )

        filename = ask("Type the filename to restore: ")
        if filename is not None:
            restore(filename)

        if ENABLE_AUTOCOMPLETE:
            readline.set_completer(self.complete)

    def do_check(self, args):
        "Check if any of your password has been in breaches"
        check_passwords()

    def do_exit(self, args):
        "Quit the program"
        self.do_EOF(args)
        return True

    def do_EOF(self, args):
        "Quit the program"
        return True

try:
    PasswordManagerShell().cmdloop()
finally:
    shutil.rmtree(temp_dir)
    PASSWORD_CONN.close()
    STORAGE_CONN.close()
