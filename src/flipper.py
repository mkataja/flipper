#!/usr/bin/python
'''
Created on Jul 4, 2012

@author: Matias
'''

import logging

import configuration
import flipperbot


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    
    conf = configuration.Configuration()
    conf.load("../config/flipper.conf")
    
    bot = flipperbot.FlipperBot(conf)
    bot.start()

if __name__ == '__main__':
    main()
