#!/usr/bin/env python

import logging

import flipperbot


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    
    bot = flipperbot.FlipperBot()
    bot.start()

if __name__ == '__main__':
    main()
