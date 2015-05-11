import json
import logging
import urllib.request, urllib.error

import config
from models.address_cache_entry import AddressCacheEntry 
from services import database


def geocode(address):
    address = address.strip().lower()
    
    try:
        with database.get_session() as session:
            cache_entry = session.query(AddressCacheEntry).filter_by(address=address).first()
            if cache_entry:
                logging.info("Found address in cache: '{}'".format(address))
                return (cache_entry.latitude, cache_entry.longitude)
    except:
        # Database not available - no matter
        pass
    
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
    
    try:
        with database.get_session() as session:
            cache_entry = AddressCacheEntry()
            cache_entry.address = address
            cache_entry.latitude = latitude
            cache_entry.longitude = longitude
            session.add(cache_entry)
            session.commit()
    except:
        # Database not available - still no matter
        pass
    
    return (latitude, longitude)
