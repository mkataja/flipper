import logging


class Module(object):
    def __init__(self, bot):
        logging.info("Initializing module {}".format(self.__class__.__name__))
        self._bot = bot
