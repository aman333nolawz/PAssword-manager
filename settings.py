# Salt for the PBKDF2HMAC algorithm
SALT = b"SomeTextGoesHere"

# Path to where the passwords should be stored
PASSWORDS_FILE = "passwords.db"

# PAth to where the storage file should be.
STORAGE_FILE = "a.db"

# Whether or not to print the info page on start
PRINT_INFO_ON_START = True

# Whether turn on autocomplete for commands.
# Turn it off if you are not on linux. Else you will get errors
ENABLE_AUTOCOMPLETE = True

# Whether or not to add the support of selecting
# choices for the password generation type
ENABLE_INQUIRER_FOR_PASSWORD_GENERATION_TYPE = True

# Whether to use diceware or random string type
# For generating passwords.
# Available types are diceware, random & ask
# diceware -> Make passwords from a jsonfile
# random -> Make passwords from a chars or words provided to PASSWORD_GENERATOR_CHARS
# ask -> Will ask whether to take diceware or random
PASSWORD_GENERATION_TYPE = "ask"

# Characters to generate the passsword when in random mode
PASSWORD_GENERATOR_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)

# Name of the diceware file
DICEWARE_WORDLIST = "diceware-words.json"
