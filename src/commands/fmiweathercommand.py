import datetime
import json
import locale
import logging
import socket
from time import sleep
import urllib.request, urllib.error, urllib.parse

from commands.command import Command
import config
from lib import geocoding


RETRIES = 3

class FmiWeatherCommand(Command):
    synop_ww_strings = {
        0: "selkeää",
        4: "auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys vähintään 1 km",
        5: "auerta, savua tai ilmassa leijuvaa pölyä ja näkyvyys alle 1 km",
        10: "utua",
        
        20: "sumua edellisen tunnin aikana",
        21: "sadetta edellisen tunnin aikana",
        22: "tihkua tai lumijyväsiä edellisen tunnin aikana",
        23: "vesisadetta edellisen tunnin aikana",
        24: "lumisadetta edellisen tunnin aikana",
        25: "jäätävää vesisadetta tai jäätävää tihkua edellisen tunnin aikana",
        
        30: "sumua",
        31: "sumuhattaroita",
        32: "sumua (ohentunut edellisen tunnin aikana)",
        33: "sumua (pysynyt samana edellisen tunnin aikana)",
        34: "sumua (muodostunut tai saennut edellisen tunnin aikana)",
        40: "sadetta",
        41: "heikkoa tai kohtalaista sadetta",
        42: "kovaa sadetta",
        50: "heikkoa tihkua",
        51: "heikkoa tihkua",
        52: "kohtalaista tihkua",
        53: "kovaa tihkua",
        54: "jäätävää heikkoa tihkua",
        55: "jäätävää kohtalaista tihkua",
        56: "jäätävää kovaa tihkua",
        60: "heikkoa vesisadetta",
        61: "heikkoa vesisadetta",
        62: "kohtalaista vesisadetta",
        63: "kovaa vesisadetta",
        64: "jäätävää heikkoa vesisadetta",
        65: "jäätävää kohtalaista vesisadetta",
        66: "jäätävää kovaa vesisadetta",
        67: "heikkoa räntäsadetta",
        68: "kohtalaista tai kovaa räntäsadetta",
        70: "lumisadetta",
        71: "heikkoa lumisadetta",
        72: "kohtalaista lumisadetta",
        73: "tiheää lumisadetta",
        74: "heikkoa jääjyvässadetta",
        75: "kohtalaista jääjyväsadetta",
        76: "kovaa jääjyväsadetta",
        77: "lumijyväsiä",
        78: "jääkiteitä",
        80: "heikkoja kuuroja tai ajoittaista vesisadetta",
        81: "heikkoja vesikuuroja",
        82: "kohtalaisia vesikuuroja",
        83: "kovia vesikuuroja",
        84: "ankaria vesikuuroja",
        85: "heikkoja lumikuuroja",
        86: "kohtalaisia lumikuuroja",
        87: "kovia lumikuuroja",
        89: "raekuuroja mahdollisesti yhdessä vesi- tai räntäsateen kanssa",
    }
    
    wind_directions = {
         "N": "Pohjois",
         "NE": "Koillis",
         "E": "Itä",
         "SE": "Kaakkois",
         "S": "Etelä",
         "SW": "Lounais",
         "W": "Länsi",
         "NW": "Luoteis",
     }
    
    def _get_weather_data(self, location):
        url = ('http://m.fmi.fi/mobile/interfaces/weatherdata.php?locations={}'
            .format(urllib.parse.quote(location)))
        try:
            reply = urllib.request.urlopen(url, timeout=3).read().decode()
            return json.loads(reply)
        except (urllib.error.HTTPError, socket.timeout):
            return None
    
    def _get_weather_string(self, data):
        suninfo = list(data.get('suninfo').values())[0]
        sunrise = None
        sunset = None
        if suninfo.get('sunrisetoday') == '1' and suninfo.get('sunsettoday') == '1':
            sunrise = datetime.datetime.strptime(suninfo['sunrise'],
                                                 '%Y%m%dT%H%M%S')
            sunrise = sunrise.strftime('%H:%M')
            sunset = datetime.datetime.strptime(suninfo['sunset'],
                                                '%Y%m%dT%H%M%S')
            sunset = sunset.strftime('%H:%M')
        
        observations = data.get('observations')
        if (observations is None 
            or len(observations) == 0
            or False in observations.values()):
            return "Ei havaintoja"
        closest = (list(observations.values())[0])[0]
        
        synop_ww = int(float(closest.get('WW_AWS')))
        weather_conditions = self.synop_ww_strings.get(synop_ww)
        if weather_conditions == None:
            weather_conditions = "Tuntematon sääilmiö ({})".format(synop_ww)
        else:
            weather_conditions = weather_conditions[:1].upper() + weather_conditions[1:]
        
        weather_string = "Sää {} {}. {}. Lämpötila {} °C, \
Kosteus {}%, Ilmanpaine {} hPa, {}tuulta {} m/s, Pilvisyys: {}/8.{}".format(
            closest.get('stationname'),
            datetime.datetime.strptime(closest['time'], '%Y%m%d%H%M')
                .strftime('%d.%m.%Y %H:%M'),
            weather_conditions,
            locale.format("%.1f", float(closest.get('Temperature'))),
            int(float(closest.get('Humidity'))),
            locale.format("%.0f", float(closest.get('Pressure'))),
            self.wind_directions.get(closest.get('WindCompass8')),
            locale.format("%.1f", float(closest.get('WindSpeedMS'))),
            int(float(closest.get('TotalCloudCover'))),
            " Aurinko nousee {} ja laskee {}.".format(sunrise, sunset)
                if (sunrise and sunset)
                else ""
        )
        
        return weather_string
    
    def handle(self, message):
        if not message.params:
            location = config.LOCATION
        else:
            address = message.params
            coordinates = geocoding.geocode(address)
            if coordinates is None:
                message.reply_to("Sijaintia {} ei ole olemassa".format(address))
                return
            location = ",".join(str(c) for c in coordinates)
        logging.info("Getting weather data in '{}'".format(location))
        for _ in range(RETRIES):
            data = self._get_weather_data(location)
            if data is not None:
                break
            sleep(0.2)
        
        if data is None:
            message.reply_to("Sääpalvelua ei löytynyt :(")
            return
        
        if data.get('status') != "ok":
            message.reply_to("Kysely epäonnistui: {}".format(data.get('message')))
            return
        
        weather_string = self._get_weather_string(data)
        message.reply_to(weather_string)
