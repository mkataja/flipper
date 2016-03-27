#!/usr/bin/env python

import faulthandler
import logging

import config
import flipperbot
import patch


def setup_logging():
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] "
        "[%(levelname)-5.5s]  %(message)s")
    logging.basicConfig(level=config.LOG_LEVEL)
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def main():
    setup_logging()

    patch.patch_irclib()

    bot = flipperbot.FlipperBot()
    try:
        bot.start()
    except SystemExit:
        logging.info("Bot stopped, shutting down")
        logging.debug("Dumping threads to stderr")
        faulthandler.dump_traceback()
        logging.shutdown()

if __name__ == '__main__':
    main()
