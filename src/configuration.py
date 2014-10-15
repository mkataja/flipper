'''
Created on 15.10.2014

@author: Matias
'''

import yaml

class Configuration(object):
    def load(self, conf_filename):
        with open(conf_filename, "r") as conf_file:
            conf_yaml = yaml.load(conf_file)
            self.SERVER = conf_yaml["server"]
            self.PORT = conf_yaml["port"]
            self.NICK = conf_yaml["nick"]
            self.CHANNELS = conf_yaml["channels"]
