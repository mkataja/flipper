import contextlib
import logging
import os
import signal
import socket
import sys
import threading
import time

import irc.client
from irc import bot, connection
from irc.bot import ExponentialBackoff
from jaraco.stream.buffer import LenientDecodingLineBuffer

import config
import modules.modulelist
from lib import irc_helpers, string_helpers
from message import Message
from services import database
from services.accesscontrol import has_admin_access


CONNECT_TIMEOUT_SECONDS = 30


class TimeoutFactory(connection.Factory):
    """Connection factory that bounds the blocking socket.connect()."""

    def __init__(self, timeout, **kwargs):
        super().__init__(**kwargs)
        self.timeout = timeout

    def connect(self, server_address):
        sock = self.wrapper(socket.socket(self.family, socket.SOCK_STREAM))
        if self.bind_address:
            sock.bind(self.bind_address)
        sock.settimeout(self.timeout)
        sock.connect(server_address)
        sock.settimeout(None)
        return sock

    __call__ = connect


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
                                        recon=recon_strategy,
                                        connect_factory=TimeoutFactory(CONNECT_TIMEOUT_SECONDS))

        irc.client.ServerConnection.buffer_class = LenientDecodingLineBuffer

        self._registered_modules = {
            m.__name__: m(self) for m in modules.modulelist.MODULES
        }
        self._registered_message_handlers = {
            m.__name__: m() for m in modules.modulelist.MESSAGE_HANDLERS
        }

        self._last_seen_connected = time.time()
        threading.Thread(target=self._reconnect_watchdog,
                         daemon=True,
                         name="ReconnectWatchdog").start()

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
                threading.Thread(target=database.with_session_cleanup,
                                 args=(method, connection, event),
                                 name=module.__class__.__name__).start()

    def _reconnect_watchdog(self):
        while True:
            time.sleep(60)
            if self.connection.is_connected():
                self._last_seen_connected = time.time()
                continue
            stuck_for = time.time() - self._last_seen_connected
            if stuck_for > config.RECONNECT_WATCHDOG_TIMEOUT:
                logging.error(
                    "Disconnected for %.0fs (>%ds threshold); exiting for "
                    "restart", stuck_for, config.RECONNECT_WATCHDOG_TIMEOUT)
                logging.shutdown()
                os._exit(1)

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
            threading.Thread(target=database.with_session_cleanup,
                             args=(message.try_run_command,),
                             name=message.command_name).start()

        if not message.commandword:
            for handler in self._registered_message_handlers.values():
                name = handler.__class__.__name__
                if name in message.channel.disabled_features:
                    logging.info(f"Module {name} is disabled on {message.channel.name}")
                else:
                    threading.Thread(target=database.with_session_cleanup,
                                     args=(handler.handle, message),
                                     name=name).start()

    def privmsg(self, target, message):
        if not self.connection.is_connected():
            logging.error("Tried to send privmsg while disconnected: aborting")
            return
        sanitized_message = string_helpers.sanitize(message)
        line_limit_bytes = irc_helpers.get_server_line_limit_bytes(self.connection)
        max_text_bytes = irc_helpers.get_max_privmsg_text_bytes(target, line_limit_bytes)
        max_chunks = max(1, getattr(config, "MAX_PRIVMSG_CHUNKS", 2))
        chunks, was_truncated = irc_helpers.split_privmsg_text_limited(
            sanitized_message, max_text_bytes, max_chunks)
        if was_truncated:
            logging.error(
                "Truncated outgoing message to %d chunk(s) for target %s",
                max_chunks,
                target,
            )
        for chunk in chunks:
            self.connection.privmsg(target, chunk)

    def set_nick(self, nick):
        self.requested_nick = nick
        self.nick_tail = ''
        self.connection.nick(self.requested_nick)
