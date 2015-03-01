import json
import logging
from multiprocessing.pool import ThreadPool
import re
import threading
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from bs4 import BeautifulSoup

import config
from modules.module import Module


class UrlModule(Module):
    def on_pubmsg(self, connection, event):
        UrlModule.UrlActions(connection, event).process_urls()
    
    
    class UrlActions(object):
        def __init__(self, connection, event):
            self._connection = connection
            self._event = event
        
        def process_urls(self):
            message = self._event.arguments[0]
            
            url_regex = '(?:(?:https?:\/\/)|www\.)(?:(?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|(?:[a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+)(?::[0-9]+)?(?:(?:\/|\?)[^ "]*[^ ,;\.:">)])?'
            urls = re.findall(url_regex, message, re.IGNORECASE)
            
            for url in urls:
                if not url.startswith("http"):
                    url = "http://" + url
                logging.debug("found url: {}".format(url))
                threading.Thread(target=self._process_url, args=(url,)).start()
            
        def _process_url(self, url):
            pool = ThreadPool()
            title_async = pool.apply_async(self._get_title, (url,))
            short_async = pool.apply_async(self._get_short_url_text, (url,))
            
            title = title_async.get()
            short = short_async.get()
            
            message = short if short is not None else ""
            if title is not None:
                message += "-> {}".format(title)
            
            if message != "":
                self._connection.privmsg(self._event.target, message) 
        
        def _get_title(self, url):
            try:
                webpage = BeautifulSoup(urlopen(url, timeout=3))
            except:
                # Doesn't really matter what went wrong, abort in any case
                return None
            if webpage is None or webpage.title is None:
                return None;
            title = webpage.title.string
            return re.sub(r"(\r?\n)+", " ", title).strip()
        
        def _get_short_url_text(self, url):
            short = None
            if len(url) > 42:
                short = self._get_short_url(url)
            return short + " " if short is not None else None
        
        def _get_short_url(self, url):
            request_url = ("https://www.googleapis.com/urlshortener/v1/url" +
                "?key=" + config.GOOGLE_API_KEY)
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
            if data is None:
                return None
            
            return data.get('id')
