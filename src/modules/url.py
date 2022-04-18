import logging
import re
import threading

from lib import web
from lib.irc_colors import color, Color
from modules.module import Module


class UrlModule(Module):
    def on_pubmsg(self, _connection, event):
        UrlModule.UrlActions(self._bot, event).process_urls()

    class UrlActions(object):
        def __init__(self, bot, event):
            self._bot = bot
            self._event = event

        def process_urls(self):
            message = self._event.arguments[0]

            urls = re.findall(web.url_regex, message)

            for url in urls:
                if not url.startswith("http"):
                    url = "http://" + url
                logging.info("Found url: {}".format(url))
                threading.Thread(target=self._process_url,
                                 args=(url,),
                                 name="UrlProcessor").start()

        def _process_url(self, url):
            title = web.get_title_text(url)
            if title:
                self._bot.privmsg(
                    self._event.target,
                    "{}".format(color(title, Color.dcyan))
                )
