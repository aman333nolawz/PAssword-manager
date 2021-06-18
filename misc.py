from colorama import Fore, Style, init

init()

def ask(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
    except KeyError:
        print()

    return None

def green(m):
    print(Fore.GREEN, end="")
    print(m)
    print(Style.RESET_ALL, end="")


def red(m):
    print(Fore.RED, end="")
    print(m)
    print(Style.RESET_ALL, end="")


def yellow(m):
    print(Fore.YELLOW, end="")
    print(m)
    print(Style.RESET_ALL, end="")
