import codecs
import json
import logging
from multiprocessing.pool import ThreadPool
import re
import threading
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from bs4 import BeautifulSoup

import config
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

            url_regex = ('(?:(?:https?:\/\/)|www\.)'
                         '(?:(?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'
                         '|(?:[a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+)'
                         '(?::[0-9]+)?(?:(?:\/|\?)[^ "]*[^ ,;\.:">)])?')
            urls = re.findall(url_regex, message, re.IGNORECASE)

            for url in urls:
                if not url.startswith("http"):
                    url = "http://" + url
                logging.debug("Found url: {}".format(url))
                threading.Thread(target=self._process_url,
                                 args=(url,),
                                 name="UrlProcessor").start()

        def _process_url(self, url):
            pool = ThreadPool()
            title_async = pool.apply_async(self._get_title_text, (url,))
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

        def _get_title_text(self, url):
            try:
                webpage = BeautifulSoup(urlopen(url, timeout=3))
            except Exception as e:
                # Doesn't really matter what went wrong, abort in any case
                logging.warn("Getting url title failed for {} ({})"
                             .format(url, str(e)))
                return None
            if not webpage or not webpage.title or not webpage.title.string:
                return None
            title = webpage.title.string.strip()
            if re.search('\\\\u\d*', title):
                title = codecs.decode(title, 'unicode_escape')
            return re.sub(r"\s{2,}", " ", title)

        def _get_short_url_text(self, url):
            short = None
            if len(url) > 42:
                short = self._get_short_url(url)
            return short + " " if short is not None else None

        def _get_short_url(self, url):
            request_url = ("https://www.googleapis.com/urlshortener/v1/url"
                           "?key=" + config.GOOGLE_API_KEY)
            request_data = json.dumps({
                'longUrl': url,
            }).encode()

            request = Request(request_url, request_data,
                              {'Content-Type': 'application/json'})

            try:
                response = urlopen(request)
            except HTTPError:
                logging.warn("Getting short url failed for {}".format(url))
                return None

            data = json.loads(response.read().decode())
            if data is None:
                return None

            return data.get('id')
