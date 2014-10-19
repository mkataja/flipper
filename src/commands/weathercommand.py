'''
Created on 18.10.2013

@author: Matias
'''

from commands.command import Command

import json
import urllib.request, urllib.error
import math
import datetime
import locale

locale.setlocale(locale.LC_ALL, '')

class WeatherCommand(Command):
    KELVINTOCELSIUS = -273.15
    
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
    
    def get_wind_word(self, wind_dir):
        return [ "Pohjois",
                 "Koillis",
                 "Itä",
                 "Kaakkois",
                 "Etelä",
                 "Lounais",
                 "Länsi",
                 "Luoteis"
                 ][int(math.floor((wind_dir + (360 / 8) / 2) % 360) / (360 / 8))] + "tuulta"
    
    def get_clouds_eights(self, clouds_percentage):
        if (datetime.datetime.now().hour == 4 or (datetime.datetime.now().hour == 16)
            and (datetime.datetime.now().minute == 20)):
            return "ERITTÄIN pilvistä"
        else:
            clouds = math.ceil(clouds_percentage / 100.0 * 8)
            if clouds == 8 and clouds_percentage < 100:
                clouds = 7
            return "{}/8".format(clouds)
    
    def get_weather_conditions(self, weather_conditions):
        if weather_conditions != []:
            conditions_string = ', '.join(weather_conditions)
            conditions_string = conditions_string[:1].upper() + conditions_string[1:]
            return conditions_string
        else:
            return "Ei tietoa sääilmiöistä"
    
    def handle(self, message):
        requested_place = None
        if not message.params:
            requested_place = "Espoo"
        else:
            requested_place = message.params
        try:
            reply = urllib.request.urlopen('http://openweathermap.org/data/2.5/weather?q={}'
                                           .format(requested_place)
                                           ).read().decode('utf8')
        except(urllib.error.HTTPError):
            message.reply_to("Sääpalvelua ei löytynyt :(")
            return
        data = json.loads(reply)
        
        if data.get('cod') == "404":
            message.reply_to("Paikkakunnalla {} ei ole säätä".format(requested_place))
            return
        elif 'message' in data:
            message.reply_to("Virhe: ".format(data.get('message')))
            return
        
        temp_min = None
        if data.get('main').get('temp_min'):
            temp_min = locale.format(
                "%.1f", data.get('main').get('temp_min') + self.KELVINTOCELSIUS)
        
        temp_max = None
        if data.get('main').get('temp_max'):
            temp_max = locale.format(
                "%.1f", data.get('main').get('temp_max') + self.KELVINTOCELSIUS)
        
        # TODO Auringonnousu- ja lasku väärin muilla kuin Suomen aikavyöhykkeillä
        sunrise = None
        if data.get('sys').get('sunrise'):
            sunrise = datetime.datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
        
        sunset = None
        if data.get('sys').get('sunset'):
            sunset = datetime.datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
        
        weather_conditions = []
        for w in data.get('weather'):
            condition = self.weather_condition_strings.get(w.get('id'))
            weather_conditions.append(condition)
        
        weather_string = "Sää {} {}. {}. Lämpötila {} °C{}, \
Kosteus {}%, Ilmanpaine {} hPa, {} {} m/s, Pilvisyys: {}.{}".format(
            "{} ({})".format(data['name'], data['sys']['country'])
                if data['name']
                else data['sys']['country'],
            datetime.datetime.fromtimestamp(data['dt']).strftime('%d.%m.%Y %H:%M'),
            self.get_weather_conditions(weather_conditions),
            locale.format("%.1f", data.get('main').get('temp') + self.KELVINTOCELSIUS),
            " ({}-{} °C)".format(temp_min, temp_max)
                if (temp_min and temp_max and temp_min != temp_max)
                else "",
            data.get('main').get('humidity'),
            locale.format("%.0f", data.get('main').get('pressure')),
            self.get_wind_word(wind_dir=data.get('wind').get('deg')),
            locale.format("%.1f", data.get('wind').get('speed')),
            self.get_clouds_eights(clouds_percentage=data.get('clouds').get('all')),
            " Aurinko nousee {} ja laskee {}.".format(sunrise, sunset)
                if (sunrise and sunset)
                else ""
        )
        message.reply_to(weather_string)
