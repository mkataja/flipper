import logging


class Module:
    def __init__(self, bot):
        logging.info(f"Initializing module {self.__class__.__name__}")
        self._bot = bot
