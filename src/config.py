'''
The purpose of this file is to supply default configuration settings.
Do not change this file to configure a bot instance. To override 
these settings, create config_local.py and make any configuration
changes there. 
'''

SERVER = ""
PORT = 6667
RECONNECTION_INTERVAL = 30

KEEP_ALIVE_FREQUENCY = 20
KEEP_ALIVE_TIMEOUT = 60

NICK = ""
REALNAME = NICK

CHANNELS = []

CMD_PREFIX = "!"

SUPERUSER_NAME = ""
SUPERUSER_NICK = ""

TIMEZONE = "UTC"
# TIMEZONE = "Europe/Helsinki"

LOCATION = "0,0"

GOOGLE_API_KEY = ""

# Import config_local.py
try:
    from config_local import *  # @UnusedWildImport
except ImportError:
    # No local config found
    pass

