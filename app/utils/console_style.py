class Colors:
    RESET = "\033[0m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    BOLD = "\033[1m"
    DIM = "\033[2m"

    @classmethod
    def color(cls, text: str, style: str) -> str:
        return f"{style}{text}{cls.RESET}"

""" class Colors:
    RESET = "\033[0m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    BOLD = "\033[1m"
    DIM = "\033[2m"

    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.RESET}"

    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.RESET}"

    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.RESET}"

    @classmethod
    def magenta(cls, text: str) -> str:
        return f"{cls.MAGENTA}{text}{cls.RESET}"

    @classmethod
    def cyan(cls, text: str) -> str:
        return f"{cls.CYAN}{text}{cls.RESET}"

    @classmethod
    def bold(cls, text: str) -> str:
        return f"{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def dim(cls, text: str) -> str:
        return f"{cls.DIM}{text}{cls.RESET}" """
        
# app/utils/console_style.py


# app/utils/console_style.py


