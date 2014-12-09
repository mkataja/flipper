'''
Created on 15.10.2014

@author: Matias
'''

import yaml


class Configuration(object):
    def _value_or_default(self, prop_name, default):
        value = self._conf_yaml[prop_name]
        return value if value != None else default
    
    def load(self, conf_filename):
        with open(conf_filename, "r") as conf_file:
            self._conf_yaml = yaml.load(conf_file)
            
            self.server = self._conf_yaml["server"]
            self.port = self._conf_yaml["port"]
            self.nick = self._conf_yaml["nick"]
            self.realname = self._value_or_default("server", self.nick)
            self.channels = self._conf_yaml["channels"]
