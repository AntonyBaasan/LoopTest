RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
WHITE = "\033[97m"


def c(text, *codes) -> str:
    """Wrap text with ANSI codes, always appending RESET at the end."""
    return "".join(codes) + str(text) + RESET
