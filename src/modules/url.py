import re
from urllib.request import urlopen

from bs4 import BeautifulSoup


class UrlModule(object):
    def on_pubmsg(self, connection, event):
        UrlModule.UrlActions(connection, event).process_urls()
    
    
    class UrlActions:
        def __init__(self, connection, event):
            self._connection = connection
            self._event = event
        
        def process_urls(self):
            message = self._event.arguments[0]
            
            url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_regex, message)
            
            for url in urls:
                self._post_title(url)
        
        def _post_title(self, url):
            webpage = BeautifulSoup(urlopen(url, timeout=3))
            title = webpage.title.string
            self._connection.privmsg(self._event.target, "-> {}".format(title))
