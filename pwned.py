import requests
import hashlib
from misc import red

API_ENDPOINT = "https://api.pwnedpasswords.com/range/"

def check_hash_in_breach(results: str, suffix: str) -> int:
    for line in results.split("\n"):
        suf, count = line.split(":")
        count = int(count)
        if suf.lower() == suffix:
            return count
    return 0

def has_been_pwned(password: str):
    password = hashlib.sha1(password.encode()).hexdigest()
    prefix = password[:5]
    suffix = password[5:]

    try:
        r = requests.get(API_ENDPOINT + prefix)
        return check_hash_in_breach(r.text, suffix.lower())
    except:
        red("Something went wrong")
        return
