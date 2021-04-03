import datetime
import json
import locale
import logging
import socket
from time import sleep
import urllib.request, urllib.error, urllib.parse

from commands.command import Command
from models.user import User
import config
from lib import geocoding
from lib.irc_colors import Color, color


RETRIES = 3

FORECAST_COMMAND = "sää"
OBSERVATION_COMMAND = "havainto"


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

    weather_symbol_3_strings = {
        1: "selkeää",
        2: "puolipilvistä",
        21: "heikkoja sadekuuroja",
        22: "sadekuuroja",
        23: "voimakkaita sadekuuroja",
        3: "pilvistä",
        31: "heikkoa vesisadetta",
        32: "vesisadetta",
        33: "voimakasta vesisadetta",
        41: "heikkoja lumikuuroja",
        42: "lumikuuroja",
        43: "voimakkaita lumikuuroja",
        51: "heikkoa lumisadetta",
        52: "lumisadetta",
        53: "voimakasta lumisadetta",
        61: "ukkoskuuroja",
        62: "voimakkaita ukkoskuuroja",
        63: "ukkosta",
        64: "voimakasta ukkosta",
        71: "heikkoja räntäkuuroja",
        72: "räntäkuuroja",
        73: "voimakkaita räntäkuuroja",
        81: "heikkoa räntäsadetta",
        82: "räntäsadetta",
        83: "voimakasta räntäsadetta",
        91: "utua",
        92: "sumua",
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
        url = ('https://m.fmi.fi/mobile/interfaces/weatherdata.php?locations={}'
               .format(urllib.parse.quote(location)))
        try:
            reply = urllib.request.urlopen(url, timeout=3).read().decode()
            return json.loads(reply)
        except (urllib.error.HTTPError, socket.timeout):
            return None

    def _get_weather_conditions(self, data):
        if data.get('WW_AWS') == 'nan':
            return None
        synop_ww = int(float(data.get('WW_AWS')))
        weather_conditions = self.synop_ww_strings.get(synop_ww)
        if not weather_conditions:
            return "Tuntematon sääilmiö ({})".format(synop_ww)
        else:
            return weather_conditions[:1].upper() + weather_conditions[1:]

    def _get_temperature(self, data):
        if data.get('Temperature') == 'nan':
            return None
        temp = float(data.get('Temperature'))
        if temp >= 25:
            temp_color = Color.red
        elif temp > 0:
            temp_color = Color.yellow
        else:
            temp_color = Color.blue
        temp_string = color(locale.format("%.1f", temp), temp_color)
        return "Lämpötila {} °C".format(temp_string)

    def _get_humidity(self, data):
        if data.get('Humidity') == 'nan':
            return None
        humidity = int(float(data.get('Humidity')))
        return "Kosteus {}%".format(humidity)

    def _get_pressure(self, data):
        if data.get('Pressure') == 'nan':
            return None
        pressure = locale.format("%.0f", float(data.get('Pressure')))
        return "Ilmanpaine {} hPa".format(pressure)

    def _get_wind(self, data):
        if data.get('WindCompass8') == 'nan' or data.get('WindSpeedMS') == 'nan':
            return None
        direction = self.wind_directions.get(data.get('WindCompass8'))
        speed = float(data.get('WindSpeedMS'))
        if speed >= 14:
            speed_color = Color.red
        elif speed >= 8:
            speed_color = Color.yellow
        else:
            speed_color = None
        speed_string = color(locale.format("%.1f", speed), speed_color)
        return "{}tuulta {} m/s".format(direction, speed_string)
    
    def _get_precipitation_1h(self, data):
        if data.get('Precipitation1h') == None:
            return None
        precipitation_1h = float(data.get('Precipitation1h'))
        if data.get('PoP') == None or data.get('PoP') == 'nan':
            probability_str = ""
        else:
            probability = int(data.get('PoP'))
            if probability < 10:
                probability_rounded = "<10"
            elif probability > 90:
                probability_rounded = ">90"
            else:
                probability_rounded = round(probability / 10) * 10
            probability_str = " (sateen todennäköisyys {}%)".format(probability_rounded)
        return "Tunnin sademäärä {}mm{}".format(precipitation_1h, probability_str)

    def _get_cloud_cover(self, data):
        if data.get('TotalCloudCover') == 'nan':
            return None
        cover = int(float(data.get('TotalCloudCover')))
        if cover <= 8:
            return "Pilvisyys: {}/8".format(cover)
        else:
            return "Pilvisyys: taivas ei näkyvissä"

    def _get_weather_from_observations(self, observations):
        stations = list(observations.values())[0]
        synop_stations = [s for s in stations if s.get('WW_AWS') != 'nan']
        if len(synop_stations) > 0:
            station = synop_stations[0]
        else:
            station = stations[0]

        weather_conditions = self._get_weather_conditions(station)
        weather_data = [
            self._get_temperature(station),
            self._get_humidity(station),
            self._get_pressure(station),
            self._get_wind(station),
            self._get_cloud_cover(station),
        ]
        weather_data = [wd for wd in weather_data if wd]
        if len(weather_data) > 0:
            weather_data_string = ', '.join(weather_data)
        else:
            weather_data_string = None

        weather_string = "Havainto {} {}.{}{}".format(
            station.get('stationname'),
            datetime.datetime.strptime(station['time'], '%Y%m%d%H%M')
                             .strftime('%d.%m.%Y %H:%M'),
            " {}.".format(weather_conditions) if weather_conditions else "",
            " {}.".format(weather_data_string) if weather_data_string else ""
        )
        return weather_string

    def _get_weather_from_forecast(self, forecast):
        ws3 = int(forecast.get('WeatherSymbol3'))
        weather_conditions = self.weather_symbol_3_strings.get(ws3)
        if not weather_conditions:
            weather_conditions = "Tuntematon sääilmiö ({})".format(ws3)
        else:
            weather_conditions = weather_conditions[:1].upper() + weather_conditions[1:]

        weather_data = [
            self._get_temperature(forecast),
            self._get_wind(forecast),
            self._get_precipitation_1h(forecast)
        ]
        weather_data = [wd for wd in weather_data if wd]
        if len(weather_data) > 0:
            weather_data_string = ', '.join(weather_data)
        else:
            weather_data_string = None
        
        if forecast.get('country') == "Suomi":
            if forecast.get('region') == "Suomi":
                location = forecast.get('name')
            else:
                location = "{} {}".format(forecast.get('region'), forecast.get('name'))
        else:
            location = "{} ({})".format(
                forecast.get('name'),
                forecast.get('region'),
                forecast.get('country')
            )

        weather_string = "Ennuste {} {}.{}{}".format(
            location,
            datetime.datetime.strptime(forecast['localtime'], '%Y%m%dT%H%M%S')
                             .strftime('%d.%m.%Y %H:%M'),
            " {}.".format(weather_conditions) if weather_conditions else "",
            " {}.".format(weather_data_string) if weather_data_string else ""
        )
        return weather_string

    def _get_suninfo_string(self, data):
        sunrise = None
        sunset = None
        suninfo_data = data.get('suninfo')
        if suninfo_data != []:
            suninfo = list(suninfo_data.values())[0]
            if suninfo.get('sunrisetoday') == '1' and suninfo.get('sunsettoday') == '1':
                sunrise = datetime.datetime.strptime(suninfo['sunrise'],
                                                     '%Y%m%dT%H%M%S')
                sunrise = sunrise.strftime('%H:%M')
                sunset = datetime.datetime.strptime(suninfo['sunset'],
                                                    '%Y%m%dT%H%M%S')
                sunset = sunset.strftime('%H:%M')

        if (sunrise and sunset):
            return " Aurinko nousee {} ja laskee {}.".format(sunrise, sunset)
        else:
            return None
    
    def _get_weather_string(self, commandword, data):
        if commandword == FORECAST_COMMAND:
            forecasts = data.get('forecasts')
            if len(forecasts) == 0:
                return None
            newest_forecast = forecasts[0].get('forecast')[0]
            return self._get_weather_from_forecast(newest_forecast)
        elif commandword == OBSERVATION_COMMAND:
            observations = data.get('observations')
            if (observations and len(observations) > 0 and False not in observations.values()):
                return self._get_weather_from_observations(observations)
            else:
                return None

    def handle(self, message):
        if not message.params:
            user = User.get_or_create(message.sender)
            if user and user.location:
                location = user.location
            else:
                location = config.LOCATION
        else:
            address = message.params
            coordinates = geocoding.geocode(address)
            if coordinates is None:
                message.reply_to("Sijaintia {} ei ole olemassa"
                                 .format(address))
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
            message.reply_to("Kysely epäonnistui: {}"
                             .format(data.get('message')))
            return

        weather_string = self._get_weather_string(message.commandword, data)
        suninfo_string = self._get_suninfo_string(data)
        if weather_string:
            message.reply_to("{}{}".format(weather_string, suninfo_string))
        else:
            message.reply_to("Ei säätietoja paikkakunnalle {}".format(address))
