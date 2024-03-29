import datetime
import locale
import logging
import re
import urllib.parse

import config
from commands.command import Command
from lib import geocoding, time_util
from lib.http import try_json_request
from lib.irc_colors import Color, color
from models.user import User

RETRIES = 5

FORECAST_COMMAND = "sää"
OBSERVATION_COMMAND = "havainto"


class FmiWeatherCommand(Command):
    helpstr = ("Ennuste: !sää [aika] [paikka] (oletuksena lähin ennuste) "
               "| Havainto: !havainto [paikka] "
               "| Aseta oletuspaikka !koti-komennolla")

    cmd_pattern = re.compile(
        r"^(?:(?P<hours>\d\d)(?::(?P<minutes>\d\d))?)? ?(?P<location>.+?)?$"
    )

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

    warning_texts = {
        'forestfire': 'metsäpalovaroitus',
        'freeze': 'pakkasvaroitus',
        'grassfire': 'ruohikkopalovaara',
        'icing': 'jäätämisvaroitus',
        'heat': 'hellevaroitus',
        'pedestrian': 'jalankulkusää',
        'wind': 'tuulivaroitus',
        'rain': 'sadevaroitus',
        'thunder': 'ukkosvaroitus',
        'traffic': 'liikennesää',
        'ultraviolet': 'UV-varoitus',
        'waterlevel': 'merivedenkorkeusvaroitus',
        'waveheight': 'aallokkovaroitus',
    }

    def _get_weather_data(self, location):
        url = ('https://m.fmi.fi/mobile/interfaces/weatherdata.php?locations={}'
               .format(urllib.parse.quote(location)))
        return try_json_request(url, retries=RETRIES)

    def _get_weather_conditions(self, data):
        if data.get('WW_AWS') == 'nan':
            return None
        synop_ww = int(float(data.get('WW_AWS')))
        weather_conditions = self.synop_ww_strings.get(synop_ww)
        if not weather_conditions:
            return "Tuntematon sääilmiö ({})".format(synop_ww)
        else:
            return weather_conditions[:1].upper() + weather_conditions[1:]

    def _color_temperature(self, data, field):
        if not data.get(field) or data.get(field) == 'nan':
            return None
        temp = float(data.get(field))
        if temp >= 25:
            temp_color = Color.red
        elif temp > 0:
            temp_color = Color.yellow
        else:
            temp_color = Color.blue
        return color(data.get(field), temp_color)

    def _get_temperature(self, data):
        temp = self._color_temperature(data, 'Temperature')
        if not temp:
            return None

        feels_like = self._color_temperature(data, 'FeelsLike')
        if feels_like:
            feels_like_string = " (tuntuu {} °C)".format(feels_like)
        else:
            feels_like_string = ""

        return "Lämpötila {} °C{}".format(temp, feels_like_string)

    def _get_humidity(self, data):
        if data.get('Humidity') == 'nan':
            return None
        humidity = int(float(data.get('Humidity')))
        return "Kosteus {}%".format(humidity)

    def _get_pressure(self, data):
        if data.get('Pressure') == 'nan':
            return None
        pressure = locale.format_string("%.0f", float(data.get('Pressure')))
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
        elif speed >= 5:
            speed_color = Color.white
        else:
            speed_color = None
        speed_string = color(data.get('WindSpeedMS'), speed_color)
        return "{}tuulta {} m/s".format(direction, speed_string)

    def _get_precipitation_1h(self, data):
        if data.get('Precipitation1h') is None:
            return None

        amount = float(data.get('Precipitation1h'))
        if amount >= 6:
            amount_color = Color.red
        elif amount >= 3:
            amount_color = Color.yellow
        elif amount >= 1.5:
            amount_color = Color.dblue
        elif amount >= 0.8:
            amount_color = Color.blue
        elif amount >= 0.2:
            amount_color = Color.dcyan
        else:
            amount_color = None
        amount_str = color(amount, amount_color)

        if data.get('PoP') is None or data.get('PoP') == 'nan':
            probability_str = ""
        else:
            probability = int(data.get('PoP'))
            if probability < 10:
                probability_rounded = "<10"
                probability_color = None
            elif probability > 90:
                probability_rounded = ">90"
                probability_color = Color.blue
            else:
                probability_rounded = round(probability / 10) * 10
                if probability_rounded >= 70:
                    probability_color = Color.blue
                elif probability_rounded >= 30:
                    probability_color = Color.dcyan
                else:
                    probability_color = None

            probability_str = " (sateen todennäköisyys {} %)".format(
                color(probability_rounded, probability_color))

        return "Tunnin sademäärä {} mm{}".format(
            amount_str,
            probability_str)

    def _get_cloud_cover(self, data):
        if data.get('TotalCloudCover') == 'nan':
            return None
        cover = int(float(data.get('TotalCloudCover')))
        if cover <= 8:
            return "Pilvisyys: {}/8".format(cover)
        else:
            return "Pilvisyys: taivas ei näkyvissä"

    def _get_snow_depth(self, data):
        if data.get('SnowDepth') == 'nan':
            return None
        snow_depth = int(float(data.get('SnowDepth')))
        return "Lumensyvyys {} cm".format(snow_depth)

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
            self._get_snow_depth(station)
        ]
        weather_data = [wd for wd in weather_data if wd]
        if len(weather_data) > 0:
            weather_data_string = ', '.join(weather_data)
        else:
            weather_data_string = None

        weather_string = "Havainto {} {}.{}{}".format(
            station.get('stationname'),
            datetime.datetime
                .strptime(station['time'], '%Y%m%d%H%M')
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
            weather_conditions = weather_conditions[:1].upper(
            ) + weather_conditions[1:]

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
                location = "{} {}".format(
                    forecast.get('region'), forecast.get('name'))
        else:
            location = "{} ({})".format(
                forecast.get('name'),
                forecast.get('region'),
                forecast.get('country')
            )

        weather_string = "Ennuste {} {}.{}{}".format(
            location,
            datetime.datetime
                .strptime(forecast['localtime'], '%Y%m%dT%H%M%S')
                .strftime('%d.%m.%Y %H:%M'),
            " {}.".format(weather_conditions) if weather_conditions else "",
            " {}.".format(weather_data_string) if weather_data_string else ""
        )
        return weather_string

    def _get_suninfo_string(self, data):
        sunrise = None
        sunset = None
        suninfo_data = data.get('suninfo')
        if suninfo_data:
            suninfo = list(suninfo_data.values())[0]
            if suninfo.get('sunrisetoday') == '1' and suninfo.get('sunsettoday') == '1':
                sunrise = datetime.datetime.strptime(suninfo['sunrise'],
                                                     '%Y%m%dT%H%M%S')
                sunrise = sunrise.strftime('%H:%M')
                sunset = datetime.datetime.strptime(suninfo['sunset'],
                                                    '%Y%m%dT%H%M%S')
                sunset = sunset.strftime('%H:%M')

        if sunrise and sunset:
            return " Aurinko nousee {} ja laskee {}.".format(sunrise, sunset)
        else:
            return None

    def _get_warnings_string(self, data):
        if not data['warnings'] or not data['warnings'].values():
            return ""
        warnings = next(iter(data['warnings'].values()))
        if not warnings:
            return ""
        warning_texts = [FmiWeatherCommand.warning_texts[w]
                         for w, present in warnings.items() if present]
        if not warning_texts:
            return ""
        else:
            return " Varoituksia: {}".format(", ".join(warning_texts))

    def _get_forecast_for_time(self, dt, forecasts):
        return min(
            forecasts,
            key=lambda f: abs(datetime.datetime.strptime(f['localtime'], '%Y%m%dT%H%M%S') - dt)
        )

    def _get_weather_string(self, command, params, data):
        if command == FORECAST_COMMAND:
            if len(data.get('forecasts')) == 0:
                return None
            forecasts = data.get('forecasts')[0].get('forecast')

            if params['hours']:
                time = datetime.time(int(params['hours']),
                                     int(params['minutes'] or 0))
                dt = time_util.get_next_datetime_for_time(time)
                forecast = self._get_forecast_for_time(dt, forecasts)
            else:
                forecast = forecasts[0]
            return self._get_weather_from_forecast(forecast)
        elif command == OBSERVATION_COMMAND:
            observations = data.get('observations')
            if observations and len(observations) > 0 and False not in observations.values():
                return self._get_weather_from_observations(observations)
            else:
                return None

    def _get_location(self, location_param, sender):
        if not location_param:
            user = User.get_or_create(sender)
            if user and user.location:
                return user.location
            else:
                return config.LOCATION
        else:
            address = location_param
            coordinates = geocoding.geocode(address)
            if coordinates is None:
                return None
            return ",".join(str(c) for c in coordinates)

    def handle(self, message):
        params = [g.groupdict() for g in FmiWeatherCommand.cmd_pattern.finditer(
            message.params.strip())][0]

        location = self._get_location(params['location'], message.sender)
        if location is None:
            message.reply_to(
                "Sijaintia {} ei ole olemassa".format(params['location']))
            return

        logging.info("Getting weather data in '{}'".format(location))
        data = self._get_weather_data(location)

        if data is None or data.get('status') != "ok":
            message.reply_to("Sääpalvelu ei vastaa :(")
            if data:
                logging.error(data.get('message'))

        weather_string = self._get_weather_string(
            message.commandword, params, data)
        suninfo_string = self._get_suninfo_string(data)
        warnings_string = self._get_warnings_string(data)

        if weather_string:
            message.reply_to("{}{}{}".format(
                weather_string, suninfo_string, warnings_string))
        else:
            message.reply_to(
                "Ei säätietoja paikkakunnalle {}".format(params['location']))
