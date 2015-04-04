import json
import logging
import urllib.request, urllib.error

import config


def geocode(address):
    logging.info("Geocoding '{}'".format(address))
    
    url = ('https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'
        .format(urllib.parse.quote(address), config.GOOGLE_API_KEY))
    try:
        reply = urllib.request.urlopen(url, timeout=3).read().decode()
    except urllib.error.HTTPError:
        return None
    
    data = json.loads(reply)
    if data is None:
        return None
    
    results = data.get('results')
    if results is None or len(results) == 0:
        return None
    
    location = results[0].get('geometry').get('location')
    latitude = location.get('lat')
    longitude = location.get('lng')
    
    return (latitude, longitude)
