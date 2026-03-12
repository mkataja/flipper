import logging


class MessageHandler:
    def __init__(self):
        logging.info(f"Initializing message handler {self.__class__.__name__}")

    def handle(self, message):
        raise NotImplementedError()
