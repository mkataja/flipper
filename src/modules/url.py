import logging
from multiprocessing.pool import ThreadPool
import re
import threading

from lib import web
from lib.irc_colors import color, Color
from modules.module import Module


class UrlModule(Module):
    def on_pubmsg(self, connection, event):
        UrlModule.UrlActions(self._bot, event).process_urls()

    class UrlActions(object):
        def __init__(self, bot, event):
            self._bot = bot
            self._event = event

        def process_urls(self):
            message = self._event.arguments[0]

            urls = re.findall(web.url_regex, message, re.IGNORECASE)

            for url in urls:
                if not url.startswith("http"):
                    url = "http://" + url
                logging.debug("Found url: {}".format(url))
                threading.Thread(target=self._process_url,
                                 args=(url,),
                                 name="UrlProcessor").start()

        def _process_url(self, url):
            pool = ThreadPool()
            title_async = pool.apply_async(web.get_title_text, (url,))
            short_async = pool.apply_async(self._get_short_url_text, (url,))

            title = title_async.get()
            short = short_async.get()

            if title and title.lower() in url.lower():
                title = None

            message = color(short, Color.dgrey) if short else ""

            if title:
                message += "{}".format(color(title, Color.dcyan))

            if message != "":
                self._bot.privmsg(self._event.target, message)

        def _get_short_url_text(self, url):
            short = None
            if len(url) > 42:
                short = web.get_short_url(url)
            return short + " " if short is not None else None
