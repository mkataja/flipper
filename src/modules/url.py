import logging
import re

from lib import web
from lib.irc_colors import color, Color
from modules.message_handler import MessageHandler


class UrlModule(MessageHandler):
    def handle(self, message):
        self._process_urls(message)

    def _process_urls(self, message):
        urls = re.findall(web.url_regex, message.content)

        for url in urls:
            if not url.startswith("http"):
                url = "http://" + url
            logging.info("Found url: {}".format(url))
            title = web.get_title_text(url)
            if title:
                message.reply("{}".format(color(title, Color.dcyan)))
