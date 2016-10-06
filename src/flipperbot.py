import logging
import signal
import sys
import threading
import time

from irc import bot
import irc
from irc.bot import ExponentialBackoff
from jaraco.stream.buffer import LenientDecodingLineBuffer

import config
from lib import irc_helpers
from lib import string_helpers
from message import Message
import modules.modulelist
from services import database, http_api
from services.accesscontrol import has_admin_access


class FlipperBot(bot.SingleServerIRCBot):
    def __init__(self):
        signal.signal(signal.SIGINT, self._sigint_handler)

        database.initialize()

        http_api.listen(self)

        self.last_pong = None
        self.nick_tail = ""

        recon_strategy = ExponentialBackoff(
            min_interval=config.RECONNECT_MIN_INTERVAL,
            max_interval=config.RECONNECT_MAX_INTERVAL)

        bot.SingleServerIRCBot.__init__(self,
                                        [(config.SERVER, config.PORT)],
                                        config.NICK,
                                        config.REALNAME,
                                        recon=recon_strategy)

        irc.client.ServerConnection.buffer_class = LenientDecodingLineBuffer

        self._registered_modules = [m(self) for m in modules.modulelist.MODULES]

    def _sigint_handler(self, signal, frame):
        if self.connection.is_connected():
            self.connection.quit(irc_helpers.quit_message())
        sys.exit()

    def _dispatcher(self, connection, event):
        super()._dispatcher(connection, event)

        for module in self._registered_modules:
            method = getattr(module, "on_" + event.type, None)
            if method is not None:
                threading.Thread(target=method,
                                 args=(connection, event),
                                 name=module.__class__.__name__).start()

    def _keep_alive(self):
        if not self.connection.is_connected():
            self.last_pong = None
            return

        current_time = time.time()
        logging.info("Last pong at {}, current time {}"
                     .format(self.last_pong, current_time))
        if (self.last_pong is not None and
                current_time > self.last_pong + config.KEEP_ALIVE_TIMEOUT):
            self.last_pong = None
            self.jump_server("Server timeout")
            return

        self.connection.ping("keep-alive")

    def _keep_nick(self):
        if not self.connection.is_connected():
            self.nick_tail = ""
            return

        if self.nick_tail != "":
            self.nick_tail = ""
            logging.info("Trying to change nick from {} to {}".format(
                self.connection.get_nickname(), config.NICK))
            self.connection.nick(config.NICK)

    def _on_disconnect(self, connection, event):
        self.last_pong = None

        logging.info("Disconnected: unloading delayed commands")
        with self.reactor.mutex:
            self.reactor.delayed_commands = []

        super(FlipperBot, self)._on_disconnect(connection, event)

    def on_welcome(self, connection, event):
        self.reactor.execute_every(config.KEEP_ALIVE_FREQUENCY,
                                   self._keep_alive, ())
        self.reactor.execute_every(60, self._keep_nick, ())

        for channel in config.CHANNELS:
            connection.join(channel)

    def on_pong(self, connection, event):
        self.last_pong = time.time()

    def on_nicknameinuse(self, connection, event):
        self.nick_tail = self.nick_tail + "_"
        connection.nick(config.NICK + self.nick_tail)

    def on_privmsg(self, connection, event):
        self._handle_message(connection, event, True)

    def on_pubmsg(self, connection, event):
        self._handle_message(connection, event, False)

    def on_invite(self, connection, event):
        sender = event.source
        if not has_admin_access(sender):
            return
        channel = event.arguments[0]
        connection.join(channel)

    def _handle_message(self, connection, event, is_private_message):
        message = Message(self, connection, event, is_private_message)
        logging.info("Handling privmsg: {}".format(message))
        threading.Thread(target=message.try_run_command,
                         name=message.command_name).start()

    def privmsg(self, target, message):
        if not self.connection.is_connected():
            logging.error("Tried to send privmsg while disconnected: aborting")
            return
        self.connection.privmsg(target, string_helpers.sanitize(message))
