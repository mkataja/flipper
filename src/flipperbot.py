import contextlib
import logging
import signal
import sys
import threading
import time

import irc.client
from irc import bot
from irc.bot import ExponentialBackoff
from jaraco.stream.buffer import LenientDecodingLineBuffer

import config
import modules.modulelist
from lib import irc_helpers, string_helpers
from message import Message
from services import database
from services.accesscontrol import has_admin_access


class FlipperBot(bot.SingleServerIRCBot):
    def __init__(self):
        signal.signal(signal.SIGINT, self._terminate_handler)
        signal.signal(signal.SIGTERM, self._terminate_handler)

        database.initialize()

        self.last_pong = None
        self.requested_nick = config.NICK
        self.nick_tail = ""

        recon_strategy = ExponentialBackoff(
            min_interval=config.RECONNECT_MIN_INTERVAL,
            max_interval=config.RECONNECT_MAX_INTERVAL)

        bot.SingleServerIRCBot.__init__(self,
                                        [(config.SERVER, config.PORT)],
                                        self.requested_nick,
                                        config.REALNAME,
                                        recon=recon_strategy)

        irc.client.ServerConnection.buffer_class = LenientDecodingLineBuffer

        self._registered_modules = {
            m.__name__: m(self) for m in modules.modulelist.MODULES
        }
        self._registered_message_handlers = {
            m.__name__: m() for m in modules.modulelist.MESSAGE_HANDLERS
        }

    def get_module_instance(self, module):
        return self._registered_modules[module.__name__]

    def _terminate_handler(self, _signal, _frame):
        if self.connection.is_connected():
            self.connection.quit(irc_helpers.get_quit_message())
        sys.exit()

    def _dispatcher(self, connection, event):
        super()._dispatcher(connection, event)

        for module in self._registered_modules.values():
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
        logging.debug(f"Last pong at {self.last_pong}, current time {current_time}")
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
            logging.info(f"Trying to change nick from {self.connection.get_nickname()} to {self.requested_nick}")
            self.set_nick(self.requested_nick)

    def _on_disconnect(self, connection, event):
        self.last_pong = None
        self.nick_tail = ""

        logging.info("Disconnected: unloading delayed commands")
        self.reactor.scheduler.queue = []

        super()._on_disconnect(connection, event)

    def on_welcome(self, connection, _event):
        self.reactor.scheduler.execute_every(config.KEEP_ALIVE_FREQUENCY,
                                             self._keep_alive)
        self.reactor.scheduler.execute_every(60, self._keep_nick)

        for channel in config.CHANNELS:
            connection.join(channel)

    def on_pong(self, _connection, _event):
        self.last_pong = time.time()

    def on_nicknameinuse(self, connection, _event):
        self.nick_tail = self.nick_tail + "_"
        connection.nick(self.requested_nick + self.nick_tail)

    def on_privmsg(self, connection, event):
        self._try_handle_message(connection, event, True)

    def on_pubmsg(self, connection, event):
        self._try_handle_message(connection, event, False)

    def on_invite(self, connection, event):
        sender = event.source
        if not has_admin_access(sender):
            return
        channel = event.arguments[0]
        connection.join(channel)

    def _try_handle_message(self, connection, event, is_private_message):
        try:
            self._handle_message(connection, event, is_private_message)
        except Exception as e:
            logging.exception("Fatal error while handling a message:")
            with contextlib.suppress(BaseException):
                # TODO: get proper message length limit
                self.privmsg(config.SUPERUSER_NICK, f'Fatal on {event.target}: "{str(e)[:200]}"')

    def _handle_message(self, connection, event, is_private_message):
        message = Message(self, connection, event, is_private_message)
        logging.info(f"Handling privmsg: {message}")

        if message.command_name in message.channel.disabled_features:
            logging.info(f"Command {message.command_name} is disabled on {message.channel.name}")
        else:
            threading.Thread(target=message.try_run_command, name=message.command_name).start()

        if not message.commandword:
            for handler in self._registered_message_handlers.values():
                name = handler.__class__.__name__
                if name in message.channel.disabled_features:
                    logging.info(f"Module {name} is disabled on {message.channel.name}")
                else:
                    threading.Thread(target=handler.handle, args=(message,), name=name).start()

    def privmsg(self, target, message):
        if not self.connection.is_connected():
            logging.error("Tried to send privmsg while disconnected: aborting")
            return
        self.connection.privmsg(target, string_helpers.sanitize(message))

    def set_nick(self, nick):
        self.requested_nick = nick
        self.nick_tail = ''
        self.connection.nick(self.requested_nick)
