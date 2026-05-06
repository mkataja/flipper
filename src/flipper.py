#!/usr/bin/env python

import faulthandler
import gzip
import logging
import os
import shutil
from logging.handlers import TimedRotatingFileHandler

import config
import flipperbot


def log_namer(name):
    return name + ".gz"


def log_rotator(source, dest):
    with open(source, 'rb') as f_in, gzip.open(dest, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(source)


def setup_logging():
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] "
        "[%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    file_handler = TimedRotatingFileHandler(config.LOG_FILE, when='d', interval=30, backupCount=120)
    file_handler.rotator = log_rotator
    file_handler.namer = log_namer
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def main():
    setup_logging()

    bot = flipperbot.FlipperBot()
    try:
        bot.start()
    except SystemExit:
        logging.info("Bot stopped, shutting down")
        logging.debug("Dumping threads to stderr")
        faulthandler.dump_traceback()
        logging.debug("Shutting down logging")
        logging.shutdown()


if __name__ == '__main__':
    main()
