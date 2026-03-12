#!/usr/bin/env python3

import argparse
import logging
import sys
from types import SimpleNamespace

import config
from commands.commandlist import ALL_CMDS
from services import database

HARNESS_NICK = "flipper"
HARNESS_SENDER = "user"
HARNESS_CHANNEL = "#test"

# IRC color number -> ANSI foreground escape
_IRC_COLOR_TO_ANSI = {
    "00": "\033[97m",   # white -> bright white
    "01": "\033[30m",   # black
    "02": "\033[34m",   # dark blue
    "03": "\033[32m",   # dark green
    "04": "\033[91m",   # red -> bright red
    "05": "\033[31m",   # dark red
    "06": "\033[35m",   # purple
    "07": "\033[33m",   # orange -> yellow
    "08": "\033[93m",   # yellow -> bright yellow
    "09": "\033[92m",   # green -> bright green
    "10": "\033[36m",   # dark cyan
    "11": "\033[96m",   # cyan -> bright cyan
    "12": "\033[94m",   # blue -> bright blue
    "13": "\033[95m",   # violet -> bright magenta
    "14": "\033[90m",   # dark grey
    "15": "\033[37m",   # grey
}


def setup_logging():
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
    )


def irc_to_ansi(text):
    """Convert IRC formatting codes (color, bold, reset) to ANSI escape codes."""
    result = []
    i = 0
    has_formatting = False

    while i < len(text):
        c = text[i]
        if c == "\x02":  # bold
            result.append("\033[1m")
            has_formatting = True
            i += 1
        elif c == "\x0f":  # reset all
            result.append("\033[0m")
            i += 1
        elif c == "\x03":  # color: \x03[fg[,bg]]
            i += 1
            fg = ""
            while i < len(text) and text[i].isdigit() and len(fg) < 2:
                fg += text[i]
                i += 1
            # Optional background color — parse and discard (terminal bg support is noisy)
            if i < len(text) and text[i] == "," and fg:
                i += 1
                bg = ""
                while i < len(text) and text[i].isdigit() and len(bg) < 2:
                    i += 1
            if fg:
                ansi = _IRC_COLOR_TO_ANSI.get(fg.zfill(2), "")
                result.append(ansi)
                has_formatting = True
            # \x03 with no digits = reset color
            else:
                result.append("\033[0m")
        else:
            result.append(c)
            i += 1

    if has_formatting:
        result.append("\033[0m")

    return "".join(result)


class FakeBot:
    def privmsg(self, target, text):
        print()
        print(irc_to_ansi(text))
        print()

    def get_module_instance(self, module_class):
        return None

    def disconnect(self, message=""):
        print(f"[harness] Bot would disconnect with message: {message!r}")

    def join(self, channel, key=""):
        print(f"[harness] Bot would join: {channel}")

    def part(self, channel, message=""):
        print(f"[harness] Bot would part: {channel}")

    def connection(self):
        return None


class FakeConnection:
    def __init__(self, nick):
        self._nick = nick

    def get_nickname(self):
        return self._nick

    def privmsg(self, target, text):
        pass

    def mode(self, *args):
        pass

    def join(self, *args):
        pass

    def part(self, *args):
        pass

    def nick(self, *args):
        pass


class FakeChannel:
    def __init__(self, name):
        self.name = name
        self.alt_cmd_prefix = None
        self.disabled_features = []


class FakeUser:
    def __init__(self, nick):
        self.nick = nick


class HarnessMessage:
    def __init__(self, commandword, params, sender, channel,
                 is_private_message=False, bot_nick=HARNESS_NICK):
        self.bot = FakeBot()
        self._connection = FakeConnection(bot_nick)

        # Fake IRC event — _event.source is used by the @admin_required decorator
        self._event = SimpleNamespace(
            source=SimpleNamespace(nick=sender, user=f"~{sender}"),
            target=channel,
            arguments=[f"!{commandword} {params}".rstrip()],
        )

        self.sender = sender
        self.sender_user = f"~{sender}"
        self.source = channel
        self.content = self._event.arguments[0]
        self.is_private_message = is_private_message

        # Use fake channel/user to avoid DB dependency for message setup
        self.channel = FakeChannel(channel)
        self.user = FakeUser(sender)

        # Set command fields directly, bypassing _parse_command
        self.commandword = commandword
        self.params = params
        self.command = ALL_CMDS.get(commandword)

    @property
    def command_name(self):
        if self.command:
            return self.command.__name__
        return "UnrecognizedCommand"

    def reply_to(self, replytext):
        if not self.is_private_message:
            replytext = f"{self.sender}: {replytext}"
        self.reply(replytext)

    def reply(self, replytext):
        if self.is_private_message:
            target = self.sender
        else:
            target = self.source
        self.bot.privmsg(target, replytext)


def list_commands():
    print("Available commands:")
    for cmd in sorted(ALL_CMDS.keys()):
        cls = ALL_CMDS[cmd]
        description = getattr(cls, "description", "")
        if description and description != "Tälle komennolle ei ole kuvausta.":
            print(f"  {cmd:<20} {description}")
        else:
            print(f"  {cmd}")


def run_command(commandword, params, sender, channel, is_private_message):
    if commandword not in ALL_CMDS:
        print(f"Unknown command: {commandword!r}", file=sys.stderr)
        print("Run with --list to see available commands.", file=sys.stderr)
        sys.exit(1)

    database.initialize()

    message = HarnessMessage(
        commandword=commandword,
        params=params,
        sender=sender,
        channel=channel,
        is_private_message=is_private_message,
    )
    ALL_CMDS[commandword]().handle(message)


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Run a single IRC command without starting the bot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  cli.py flip yes/no/maybe\n"
               "  cli.py roll 2d6\n"
               "  cli.py memo get sometopic\n"
               "  cli.py help flip --pm\n",
    )
    parser.add_argument("command", nargs="?", help="Command to run (e.g. flip, roll, memo)")
    parser.add_argument("params", nargs="*", help="Parameters to pass to the command")
    parser.add_argument("--sender", default=HARNESS_SENDER,
                        help=f"Sender nick (default: {HARNESS_SENDER})")
    parser.add_argument("--channel", default=HARNESS_CHANNEL,
                        help=f"Source channel (default: {HARNESS_CHANNEL})")
    parser.add_argument("--pm", action="store_true",
                        help="Treat as a private message")
    parser.add_argument("--list", action="store_true",
                        help="List available commands and exit")
    args = parser.parse_args()

    if args.list:
        list_commands()
        return

    if not args.command:
        parser.print_help()
        sys.exit(1)

    params = " ".join(args.params)
    run_command(
        commandword=args.command,
        params=params,
        sender=args.sender,
        channel=args.channel,
        is_private_message=args.pm,
    )


if __name__ == "__main__":
    main()
