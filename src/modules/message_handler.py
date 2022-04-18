import logging


class MessageHandler:
    def __init__(self):
        logging.info("Initializing message handler {}".format(self.__class__.__name__))
