import re
from urllib.request import urlopen

from bs4 import BeautifulSoup


class UrlActions(object):
    def on_pubmsg(self, connection, event):
        self._post_title(connection, event)
    
    def _post_title(self, connection, event):
        message = event.arguments[0]
        
        url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_regex, message)
        
        for url in urls:
            webpage = BeautifulSoup(urlopen(url, timeout=3))
            title = webpage.title.string
            connection.privmsg(event.target, "-> {}".format(title))
    