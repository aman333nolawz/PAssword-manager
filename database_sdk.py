import base64
import io
import json
import pickle
import random
import secrets
import sqlite3
import tempfile
import webbrowser
from getpass import getpass
from os import path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image

from misc import ask, green, red
from settings import (DICEWARE_WORDLIST, PASSWORD_GENERATOR_CHARS,
                      PASSWORDS_FILE, SALT, STORAGE_FILE)


def fernet(password, salt=SALT):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)


current_path = path.dirname(path.abspath(__file__))
PASSWORD_CONN = sqlite3.connect(path.join(current_path, PASSWORDS_FILE))
PASSWORD_CURSOR = PASSWORD_CONN.cursor()
STORAGE_CONN = sqlite3.connect(STORAGE_FILE)
STORAGE_CURSOR = STORAGE_CONN.cursor()
IMAGES_EXTENSIONS = [".PPM", ".PNG", ".JPEG", ".JPG", ".GIF", ".TIFF", ".BMP"]

with PASSWORD_CONN:
    PASSWORD_CURSOR.execute(
        """CREATE TABLE IF NOT EXISTS manager(
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                      );"""
    )

with STORAGE_CONN:
    STORAGE_CURSOR.execute(
        """CREATE TABLE IF NOT EXISTS storage(
                        filename TEXT NOT NULL UNIQUE,
                        data BLOB NOT NULL
                      );"""
    )


master_password = getpass("Master password (Characters won't be visible): ")

f = fernet(master_password)


def encrypt(password: str, fer=f, encode=True) -> str:
    if encode:
        return fer.encrypt(password.encode()).decode()
    return fer.encrypt(password)


def decrypt(encrypted_password: str, fer=f, encode=True) -> str:
    if encode:
        return fer.decrypt(encrypted_password.encode()).decode()
    return fer.decrypt(encrypted_password)


def load_diceware():
    with open(path.join(current_path, DICEWARE_WORDLIST), "r") as f:
        diceware_words = json.load(f)
    return diceware_words


def make_password(length, method="random"):
    password = ""
    if method == "random":
        password = "".join(
            secrets.choice(PASSWORD_GENERATOR_CHARS) for _ in range(length)
        )
    elif method == "diceware":
        diceware_words = load_diceware()
        RNG = random.SystemRandom()
        choices = [[str(RNG.randint(1, 6)) for _ in range(5)] for _ in range(length)]
        for choice in choices:
            key = "".join(choice)
            word = diceware_words[key]
            password += word[0].upper() + diceware_words[key][1:]
    return password


def check_master_password(exit_=False):
    password_is_wrong = (
        get_all_users(True) == True or get_all_files_stored(True) == True
    )
    if password_is_wrong:
        red("Wrong master password.")
        if exit_:
            exit(1)
        return False
    return True


def change_master_password():
    global f, master_password

    new_password = getpass("New Password: ")
    confirm_password = getpass("Confirm New Password: ")

    if confirm_password != new_password:
        red("You mistyped confirm password. Sorry.")
        return

    new_fer = fernet(new_password)
    PASSWORD_CURSOR.execute("SELECT * FROM manager")
    for username, old_encrypted_password in PASSWORD_CURSOR.fetchall():
        new_encrypted_password = encrypt(
            decrypt(
                old_encrypted_password,
                fer=f,
            ),
            fer=new_fer,
        )
        with PASSWORD_CONN:
            PASSWORD_CURSOR.execute(
                "UPDATE manager SET password = ? WHERE username = ?",
                (new_encrypted_password, username),
            )

    STORAGE_CURSOR.execute("SELECT * FROM storage")
    for filename, old_encrypted_data in STORAGE_CURSOR.fetchall():
        data = pickle.dumps(decrypt(old_encrypted_data, fer=f, encode=False))
        new_encrypted_data = encrypt(data, new_fer, encode=False)
        with STORAGE_CONN:
            STORAGE_CURSOR.execute(
                "UPDATE storage SET data = ? WHERE filename = ?",
                (new_encrypted_data, filename),
            )
            STORAGE_CONN.commit()

    f = new_fer
    green(
        f'Succesfully Changed master password to "{new_password}" from "{master_password}"'
    )
    master_password = new_password


def update_user(username, password=None):
    username = username.lower().rstrip()
    PASSWORD_CURSOR.execute("SELECT * FROM manager WHERE username = ?", (username,))
    if PASSWORD_CURSOR.fetchone() is not None:
        if password is None:
            password = getpass("Type the new password: ")  # The new password
        with PASSWORD_CONN:
            PASSWORD_CURSOR.execute(
                "UPDATE manager SET password = ? WHERE username = ?",
                (encrypt(password, f), username),
            )
            green(
                f'Succesfully Updated Username: {username}\'s password to: "{password}"'
            )
    else:
        red("There is no such user.")


def add_user(username, password):
    username = username.lower().rstrip()
    with PASSWORD_CONN:
        PASSWORD_CURSOR.execute("SELECT * FROM manager WHERE username = ?", (username,))
        result = PASSWORD_CURSOR.fetchone()
        if result is None:
            PASSWORD_CURSOR.execute(
                "INSERT INTO manager VALUES(?, ?)", (username, encrypt(password, f))
            )
            green(f'Succesfully Added Username: "{username}" & password: "{password}"')
        else:
            to_update = ask(
                "That username already exists. Do you meant to update the password of the username? (y)es, (n)o: "
            ).lower()
            if to_update in ["yes", "y"]:
                update_user(username, password)


def delete_user(username):
    username = username.lower().rstrip()
    try:
        with PASSWORD_CONN:
            PASSWORD_CURSOR.execute("DELETE FROM manager WHERE username = ?", (username,))
            green(f'Succesfully Removed Username: "{username}"')
    except Exception as e:
        red(f"There was an error:\n{e}")


def delete_all_users():
    try:
        with PASSWORD_CONN:
            PASSWORD_CURSOR.execute("DELETE FROM manager")
            green("Successully deleted all users & passwords")
    except Exception as e:
        red(f"There was an error:\n{e}")


def get_user(username):
    username = username.lower().rstrip()
    PASSWORD_CURSOR.execute("SELECT * FROM manager WHERE username = ?", (username,))
    out = PASSWORD_CURSOR.fetchone()
    if out is not None:
        print(f'Username: "{out[0]}" | Password: "{decrypt(out[1], f)}"')
    else:
        red("There is no such user.")


def get_all_users(debug=False):
    PASSWORD_CURSOR.execute("SELECT * FROM manager")
    users = PASSWORD_CURSOR.fetchall()
    try:
        for user in users:
            if not debug:
                print(f'Username: "{user[0]}" | Password: "{decrypt(user[1], f)}"')
            else:
                _ = f"| {decrypt(user[1], f)}"
                break
    except InvalidToken:
        return True  # Says to exit


def store(filename):
    if path.exists(filename):
        with open(filename, "rb") as file:
            data = file.read()

        data = pickle.dumps(data)
        data = encrypt(data, encode=False)
        with STORAGE_CONN:
            filename, ext = path.splitext(path.basename(filename))
            filename = filename + ext
            try:
                STORAGE_CURSOR.execute(
                    "INSERT INTO storage VALUES(?, ?)", (filename, data)
                )
            except sqlite3.IntegrityError:
                red(
                    "There is already an image with that name in the database. Try renaming the file to add to database"
                )
    else:
        red(f"There is no such file as {filename}")


def preview(filename):
    STORAGE_CURSOR.execute("SELECT * FROM storage WHERE filename = ?", (filename,))
    result = STORAGE_CURSOR.fetchone()
    if result is not None:
        _, file_ext = path.splitext(result[0])
        file_ext = file_ext.upper()
        data = result[1]
        data = pickle.loads(decrypt(data, f, encode=False))
        if file_ext in IMAGES_EXTENSIONS:
            data = Image.open(io.BytesIO(data))
            data.show()

        else:
            try:
                with open(f"{temp_dir}/{filename}", "wb") as tmp:
                    tmp.write(data)
                    webbrowser.open(tmp.name)
                green(f"Succesfully opened {filename}")
            except:
                red(f"Cannot open {filename}.")
    else:
        red(f"There is no such file as {filename} in the database")


def restore(filename):
    STORAGE_CURSOR.execute("SELECT * FROM storage WHERE filename = ?", (filename,))
    result = STORAGE_CURSOR.fetchone()
    if result is not None:
        path_to_save = ask("Type the path(with filename) to restore the file: ")
        data = decrypt(result[1], f, encode=False)
        data = pickle.loads(data)
        with open(path_to_save, "wb") as file:
            file.write(data)
    else:
        red(f"There is no such file as {filename} in the database")


def get_all_files_stored(debug=False):
    STORAGE_CURSOR.execute("SELECT * FROM storage")
    result = STORAGE_CURSOR.fetchall()
    out = []
    for filename, password in result:
        if debug:
            try:
                _ = pickle.loads(decrypt(password, encode=False))
            except InvalidToken as e:
                return True
        else:
            out.append(filename)
    return out


check_master_password(exit_=True)

temp_dir = tempfile.mkdtemp(prefix="PA_")
