#!/usr/bin/env python

import logging

import flipperbot
import patch


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    
    patch.patch_irclib()
    
    bot = flipperbot.FlipperBot()
    bot.start()

if __name__ == '__main__':
    main()
