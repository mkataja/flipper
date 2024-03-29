import datetime
import locale
import logging
import math
import urllib.parse

import pytz

import config
from commands.command import Command
from lib import time_util
from lib.http import try_json_request

KELVINTOCELSIUS = -273.15
RETRIES = 5


class OpenWeatherMapCommand(Command):
    weather_condition_strings = {
        200: "ukkosta ja heikkoa sadetta",
        201: "ukkosta ja sadetta",
        202: "ukkosta ja runsasta sadetta",
        210: "heikkoa ukkosta",
        211: "ukkosta",
        212: "voimakasta ukkosta",
        221: "ukkoskuuroja",
        230: "ukkosta ja heikkoa tihkua",
        231: "ukkosta ja tihkua",
        232: "ukkosta ja runsasta tihkua",

        300: "heikkoa tihkua",
        301: "tihkua",
        302: "runsasta tihkua",
        310: "heikkoa tihkua ja sadetta",
        311: "tihkua ja sadetta",
        312: "runsasta tihkua ja sadetta",
        313: "sadekuuroja ja tihkua",
        314: "runsaita sadekuuroja ja tihkua",
        321: "kuuroittaista tihkua",

        500: "heikkoa sadetta",
        501: "sadetta",
        502: "runsasta sadetta",
        503: "erittäin runsasta sadetta",
        504: "uskomattoman runsasta sadetta",
        511: "jäätävää sadetta",
        520: "heikkoja sadekuuroja",
        521: "sadekuuroja",
        522: "runsaita sadekuuroja",
        531: "ajoittaisia kuurosateita",

        600: "heikkoa lumisadetta",
        601: "lumisadetta",
        602: "runsasta lumisadetta",
        611: "räntää",
        612: "räntäkuuroja",
        615: "heikkoa sadetta ja lumisadetta",
        616: "sadetta ja lumisadetta",
        620: "heikkoja lumikuuroja",
        621: "lumikuuroja",
        622: "sakeita lumikuuroja",

        701: "utua",
        711: "savua",
        721: "auerta",
        731: "hiekka- tai pölypyörteitä",
        741: "sumua",
        751: "hiekkaa",
        761: "pölyä",
        762: "vulkaanista tuhkaa",
        771: "tuulenpuuskia",
        781: "tornado",

        800: "selkeää",
        801: "melkein selkeää",
        802: "puolipilvistä",
        803: "melkein pilvistä",
        804: "pilvistä",

        900: "tornado",
        901: "trooppinen hirmumyrsky",
        902: "hurrikaani",
        903: "kylmää",
        904: "hellettä",
        905: "tuulista",
        906: "rakeita",

        950: "asettuvaa",
        951: "tyyntä",
        952: "heikkoa tuulta",
        953: "heikkoa tuulta",
        954: "kohtalaista tuulta",
        955: "kohtalaista tuulta",
        956: "navakkaa tuulta",
        957: "kovaa tuulta",
        958: "erittäin kovaa tuulta",
        959: "myrskyä",
        960: "kovaa myrskyä",
        961: "ankaraa myrskyä",
        962: "hirmumyrskyä",
    }

    def _get_wind_word(self, wind_dir):
        return [
                   "Pohjois",
                   "Koillis",
                   "Itä",
                   "Kaakkois",
                   "Etelä",
                   "Lounais",
                   "Länsi",
                   "Luoteis"
               ][int(math.floor((wind_dir + (360 / 8) / 2) % 360) / (360 / 8))] + "tuulta"

    def _get_clouds_eights(self, clouds_percentage):
        hour = datetime.datetime.now().hour
        minute = datetime.datetime.now().minute
        if (hour == 4 or hour == 16) and minute == 20:
            return "ERITTÄIN pilvistä"
        else:
            clouds = math.ceil(clouds_percentage / 100.0 * 8)
            if clouds == 8 and clouds_percentage < 100:
                clouds = 7
            return "{}/8".format(clouds)

    def _get_weather_conditions(self, weather_conditions):
        if weather_conditions:
            conditions_string = ', '.join(weather_conditions)
            conditions_string = (conditions_string[:1].upper() +
                                 conditions_string[1:])
            return conditions_string
        else:
            return "Ei tietoa sääilmiöistä"

    def _get_temp_diff(self, data):
        temp = data.get('main').get('temp')
        temp_min = data.get('main').get('temp_min')
        temp_max = data.get('main').get('temp_max')

        if temp and temp_min and temp_max and temp_min != temp_max:
            diff_to_min = temp - temp_min
            diff_to_max = temp_max - temp
            temp_diff = locale.format_string("%.1f", max(diff_to_min, diff_to_max))
            temp_diff_string = " (±{} °C)".format(temp_diff)
        else:
            temp_diff_string = ""

        return temp_diff_string

    def _get_weather_data(self, requested_place):
        url = ('http://openweathermap.org/data/2.5/weather?q={}&appid={}'
               .format(urllib.parse.quote(requested_place), config.OPEN_WEATHER_API_KEY))
        return try_json_request(url, retries=RETRIES)

    def _get_weather_string(self, data):
        sunrise = None
        sunset = None
        if data.get('sys').get('sunrise') and data.get('sys').get('sunset'):
            sunrise = datetime.datetime.fromtimestamp(data['sys']['sunrise'],
                                                      tz=pytz.utc)
            sunset = datetime.datetime.fromtimestamp(data['sys']['sunset'],
                                                     tz=pytz.utc)
            latitude = data.get('coord').get('lat')
            longitude = data.get('coord').get('lon')
            timezone_id = time_util.get_geographic_timezone(latitude, longitude)
            sunrise = time_util.get_time_in_timezone(sunrise, timezone_id)
            sunset = time_util.get_time_in_timezone(sunset, timezone_id)

        weather_conditions = []
        for w in data.get('weather'):
            condition = self.weather_condition_strings.get(w.get('id'))
            weather_conditions.append(condition)

        weather_string = (
            "Sää {} {}. {}. Lämpötila {} °C{}, Kosteus {}%, "
            "Ilmanpaine {} hPa, {} {} m/s, Pilvisyys: {}.{}".format(
                "{} ({})".format(data['name'], data['sys']['country'])
                if data['name']
                else data['sys']['country'],
                datetime.datetime.fromtimestamp(data['dt']).strftime('%d.%m.%Y %H:%M'),
                self._get_weather_conditions(weather_conditions),
                locale.format_string("%.1f", data.get('main').get('temp') + KELVINTOCELSIUS),
                self._get_temp_diff(data),
                data.get('main').get('humidity'),
                locale.format_string("%.0f", data.get('main').get('pressure')),
                self._get_wind_word(wind_dir=data.get('wind').get('deg')),
                locale.format_string("%.1f", data.get('wind').get('speed')),
                self._get_clouds_eights(clouds_percentage=data.get('clouds').get('all')),
                " Aurinko nousee {} ja laskee {}.".format(sunrise.strftime('%H:%M'),
                                                          sunset.strftime('%H:%M'))
                if (sunrise and sunset)
                else ""
            ))

        return weather_string

    def handle(self, message):
        if not message.params:
            requested_place = "Espoo"
        else:
            requested_place = message.params

        data = self._get_weather_data(requested_place)
        if data is None:
            message.reply_to("Sääpalvelua ei löytynyt :(")
            return

        if data.get('cod') == "404":
            message.reply_to("Paikkakunnalla {} ei ole säätä"
                             .format(requested_place))
            return
        elif 'message' in data:
            logging.error(f"Openweather error: {data.get('message')}")
            message.reply_to("Virhe :(")
            return

        weather_string = self._get_weather_string(data)
        message.reply_to(weather_string)
