import json
from multiprocessing.pool import ThreadPool
import re
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from bs4 import BeautifulSoup

import config


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
                self._process_url(url)
            
        def _process_url(self, url):
            pool = ThreadPool()
            title_async = pool.apply_async(self._get_title, (url,))
            short_async = pool.apply_async(self._get_short_url_text, (url,))
            
            title = title_async.get()
            short = short_async.get()
            
            self._connection.privmsg(self._event.target, 
                                     "{}-> {}"
                                     .format(short, title)) 
        
        def _get_title(self, url):
            webpage = BeautifulSoup(urlopen(url, timeout=3))
            return webpage.title.string
        
        def _get_short_url_text(self, url):
            short = None
            if len(url) > 42:
                short = self._get_short_url(url)
            return short + " " if short != None else ""
        
        def _get_short_url(self, url):
            request_url = "https://www.googleapis.com/urlshortener/v1/url" + \
                "?key=" + config.GOOGLE_API_KEY
            request_data = json.dumps({
                'longUrl': url,
            }).encode()
            
            request = Request(request_url, request_data,
                              {'Content-Type': 'application/json'})
            
            try:
                response = urlopen(request)
            except(HTTPError):
                return None
            
            data = json.loads(response.read().decode())
            if data == None:
                return None
            
            return data.get('id')
