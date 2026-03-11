import datetime
import locale
import logging
import math
import re
import urllib.parse
import xml.etree.ElementTree as ET

import pytz

import config
from commands.command import Command
from lib import geocoding, time_util
from lib.http import try_text_request
from lib.irc_colors import Color, color
from lib.sun import sun_times
from models.user import User

RETRIES = 5

FORECAST_COMMAND = "sää"
OBSERVATION_COMMAND = "havainto"

FMI_WFS_BASE = "http://opendata.fmi.fi/wfs"

OBSERVATION_PARAMS = (
    "t2m,ws_10min,wd_10min,wg_10min,rh,r_1h,snow_aws,p_sea,n_man,wawa"
)
SCANDINAVIA_FORECAST_PARAMS = (
    "Temperature,DewPoint,Humidity,WindSpeedMS,WindDirection,"
    "HourlyMaximumGust,Precipitation1h,PoP,WeatherSymbol3,"
    "TotalCloudCover,Pressure"
)
ECMWF_FORECAST_PARAMS = (
    "Temperature,Humidity,Pressure,WindUMS,WindVMS,Precipitation1h"
)

GML_NS = "{http://www.opengis.net/gml/3.2}"
GMLCOV_NS = "{http://www.opengis.net/gmlcov/1.0}"
SWE_NS = "{http://www.opengis.net/swe/2.0}"
WFS_NS = "{http://www.opengis.net/wfs/2.0}"
TARGET_NS = "{http://xml.fmi.fi/namespace/om/atmosphericfeatures/1.1}"


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

    # ---- API helpers ----

    def _build_wfs_url(self, stored_query, params, location_params,
                       extra=None):
        url_params = {
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'getFeature',
            'storedquery_id': stored_query,
            'parameters': params,
        }
        url_params.update(location_params)
        if extra:
            url_params.update(extra)
        return "{}?{}".format(FMI_WFS_BASE, urllib.parse.urlencode(url_params))

    @staticmethod
    def _latlon_params(latlon):
        return {'latlon': '{},{}'.format(latlon[0], latlon[1])}

    @staticmethod
    def _bbox_params(latlon, margin=0.3):
        """Bounding box around coordinates (for APIs that don't support latlon)."""
        lat, lon = latlon
        return {'bbox': '{},{},{},{}'.format(
            lon - margin, lat - margin, lon + margin, lat + margin)}

    def _parse_multipointcoverage(self, xml_text):
        """Parse a WFS multipointcoverage XML response.

        Returns dict with location_name, region, country, lat, lon,
        timestamps (UTC datetimes), params (list), data (list of dicts).
        Returns None on error or empty response.
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logging.exception("Failed to parse WFS XML")
            return None

        if 'ExceptionReport' in root.tag:
            return None

        member = root.find('{}member'.format(WFS_NS))
        if member is None:
            return None

        location_name = None
        region = None
        country = None

        for name_elem in root.iter('{}name'.format(GML_NS)):
            cs = name_elem.get('codeSpace', '')
            if 'locationcode/name' in cs:
                location_name = name_elem.text
                break

        for elem in root.iter('{}region'.format(TARGET_NS)):
            region = elem.text.strip() if elem.text else None
        for elem in root.iter('{}country'.format(TARGET_NS)):
            country = elem.text.strip() if elem.text else None

        lat, lon = None, None
        pos_elem = root.find('.//{}pos'.format(GML_NS))
        if pos_elem is not None and pos_elem.text:
            parts = pos_elem.text.strip().split()
            if len(parts) >= 2:
                lat, lon = float(parts[0]), float(parts[1])

        timestamps = []
        position_coords = []
        positions_elem = root.find('.//{}positions'.format(GMLCOV_NS))
        if positions_elem is not None and positions_elem.text:
            for line in positions_elem.text.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 3:
                    ts = (datetime.datetime(1970, 1, 1)
                          + datetime.timedelta(seconds=int(parts[2])))
                    timestamps.append(ts)
                    position_coords.append(
                        (float(parts[0]), float(parts[1])))

        param_names = []
        for field in root.iter('{}field'.format(SWE_NS)):
            name = field.get('name')
            if name:
                param_names.append(name)

        all_values = []
        tuple_list = root.find(
            './/{}doubleOrNilReasonTupleList'.format(GML_NS))
        if tuple_list is not None and tuple_list.text:
            for line in tuple_list.text.strip().split('\n'):
                values = line.strip().split()
                row = {}
                for i, param in enumerate(param_names):
                    if i < len(values):
                        val = values[i]
                        if val == 'NaN':
                            row[param] = None
                        else:
                            try:
                                row[param] = float(val)
                            except ValueError:
                                row[param] = None
                    else:
                        row[param] = None
                all_values.append(row)

        if not timestamps or not all_values:
            return None

        # With bbox queries, multiple stations may be returned.
        # Filter to only the first station's data (stations are grouped).
        first_coord = position_coords[0] if position_coords else None
        data = []
        filtered_timestamps = []
        for i, row in enumerate(all_values):
            if i < len(position_coords) \
                    and position_coords[i] == first_coord:
                data.append(row)
                filtered_timestamps.append(timestamps[i])
        timestamps = filtered_timestamps or timestamps

        return {
            'location_name': location_name,
            'region': region,
            'country': country,
            'lat': lat,
            'lon': lon,
            'timestamps': timestamps,
            'params': param_names,
            'data': data,
        }

    # ---- Data fetching ----

    def _fetch_observations(self, latlon, place_name=None):
        if place_name:
            loc = {'place': place_name}
        else:
            loc = self._bbox_params(latlon)
        url = self._build_wfs_url(
            'fmi::observations::weather::multipointcoverage',
            OBSERVATION_PARAMS, loc,
            {'timestep': '60', 'maxlocations': '1'}
        )
        xml_text = try_text_request(url, retries=RETRIES)
        if xml_text is None:
            return None
        return self._parse_multipointcoverage(xml_text)

    def _fetch_forecast(self, latlon, place_name=None):
        """Try Edited Scandinavia first (PoP), fall back to ECMWF (global)."""
        if place_name:
            loc = {'place': place_name}
        else:
            loc = self._latlon_params(latlon)
        url = self._build_wfs_url(
            'fmi::forecast::edited::weather::scandinavia::point'
            '::multipointcoverage',
            SCANDINAVIA_FORECAST_PARAMS, loc,
            {'timestep': '60'}
        )
        xml_text = try_text_request(url, retries=RETRIES)
        if xml_text is not None:
            result = self._parse_multipointcoverage(xml_text)
            if result is not None:
                result['model'] = 'scandinavia'
                return result

        logging.info("Scandinavia forecast unavailable, trying ECMWF")
        url = self._build_wfs_url(
            'ecmwf::forecast::surface::point::multipointcoverage',
            ECMWF_FORECAST_PARAMS, loc,
            {'timestep': '360'}
        )
        xml_text = try_text_request(url, retries=RETRIES)
        if xml_text is None:
            return None

        result = self._parse_multipointcoverage(xml_text)
        if result is not None:
            result['model'] = 'ecmwf'
            for row in result['data']:
                u = row.get('WindUMS')
                v = row.get('WindVMS')
                if u is not None and v is not None:
                    row['WindSpeedMS'] = math.sqrt(u ** 2 + v ** 2)
                    row['WindDirection'] = math.degrees(
                        math.atan2(-u, -v)) % 360
                else:
                    row['WindSpeedMS'] = None
                    row['WindDirection'] = None
        return result

    # ---- Computation helpers ----

    @staticmethod
    def _degrees_to_compass(degrees):
        if degrees is None:
            return None
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        return directions[round(degrees / 45) % 8]

    @staticmethod
    def _compute_feels_like(temp, wind_speed, humidity):
        if temp is None or wind_speed is None:
            return None
        wind_kmh = wind_speed * 3.6
        if temp <= 10 and wind_kmh > 4.8:
            return (13.12 + 0.6215 * temp
                    - 11.37 * wind_kmh ** 0.16
                    + 0.3965 * temp * wind_kmh ** 0.16)
        elif temp >= 27 and humidity is not None:
            return (-8.785 + 1.611 * temp + 2.339 * humidity
                    - 0.1461 * temp * humidity - 0.01231 * temp ** 2
                    - 0.01642 * humidity ** 2
                    + 0.002212 * temp ** 2 * humidity
                    + 0.0007255 * temp * humidity ** 2
                    - 0.000003582 * temp ** 2 * humidity ** 2)
        return temp

    def _utc_to_local(self, utc_dt):
        tz = pytz.timezone(config.TIMEZONE)
        return utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)

    # ---- Formatting helpers ----

    def _color_temp_value(self, temp):
        if temp is None:
            return None
        if temp >= 25:
            temp_color = Color.red
        elif temp > 0:
            temp_color = Color.yellow
        else:
            temp_color = Color.blue
        return color("{:.0f}".format(temp), temp_color)

    def _format_temperature(self, temp, feels_like):
        colored_temp = self._color_temp_value(temp)
        if colored_temp is None:
            return None
        parts = "Lämpötila {} °C".format(colored_temp)
        if feels_like is not None and abs(feels_like - temp) >= 1.0:
            parts += " (tuntuu {} °C)".format(self._color_temp_value(feels_like))
        return parts

    def _format_humidity(self, rh):
        if rh is None:
            return None
        return "Kosteus {}%".format(int(rh))

    def _format_pressure(self, pressure):
        if pressure is None:
            return None
        return "Ilmanpaine {} hPa".format(
            locale.format_string("%.0f", pressure))

    def _format_wind(self, direction_deg, speed, gust=None):
        if speed is None:
            return None
        compass = self._degrees_to_compass(direction_deg)
        direction_str = self.wind_directions.get(compass, '')

        if speed >= 14:
            speed_color = Color.red
        elif speed >= 8:
            speed_color = Color.yellow
        elif speed >= 5:
            speed_color = Color.white
        else:
            speed_color = None
        speed_str = color("{:.0f}".format(speed), speed_color)

        result = "{}tuulta {} m/s".format(direction_str, speed_str)
        if gust is not None and gust > speed + 2:
            result += " (puuska {:.0f}) m/s".format(gust)
        return result

    def _format_precipitation(self, amount, pop=None):
        if amount is None:
            return None
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
        amount_str = color("{:.1f}".format(amount), amount_color)

        pop_str = ""
        if pop is not None:
            pop_int = int(pop)
            if pop_int < 10:
                pop_rounded = "<10"
                pop_color = None
            elif pop_int > 90:
                pop_rounded = ">90"
                pop_color = Color.blue
            else:
                pop_rounded = round(pop_int / 10) * 10
                if pop_rounded >= 70:
                    pop_color = Color.blue
                elif pop_rounded >= 30:
                    pop_color = Color.dcyan
                else:
                    pop_color = None
            pop_str = " (sateen todennäköisyys {} %)".format(
                color(pop_rounded, pop_color))

        return "Tunnin sademäärä {} mm{}".format(amount_str, pop_str)

    def _format_cloud_cover(self, cover):
        if cover is None:
            return None
        cover_int = int(cover)
        if cover_int <= 8:
            return "Pilvisyys: {}/8".format(cover_int)
        return "Pilvisyys: taivas ei näkyvissä"

    def _format_snow_depth(self, depth):
        if depth is None or depth <= 0:
            return None
        return "Lumensyvyys {} cm".format(int(depth))

    @staticmethod
    def _capitalize(s):
        if not s:
            return s
        return s[0].upper() + s[1:]

    # ---- Observation formatting ----

    def _format_observation(self, parsed):
        data_rows = parsed['data']
        timestamps = parsed['timestamps']

        # Pick the latest row with a temperature reading
        obs = None
        obs_time = None
        for i in range(len(data_rows) - 1, -1, -1):
            if data_rows[i].get('t2m') is not None:
                obs = data_rows[i]
                obs_time = timestamps[i]
                break
        if obs is None:
            return None

        local_time = self._utc_to_local(obs_time)
        time_str = local_time.strftime('%d.%m.%Y %H:%M')

        wawa = obs.get('wawa')
        conditions = None
        if wawa is not None:
            conditions = self.synop_ww_strings.get(int(wawa))
            if conditions:
                conditions = self._capitalize(conditions)
            elif int(wawa) != 0:
                conditions = "Tuntematon sääilmiö ({})".format(int(wawa))

        weather_data = [
            self._format_temperature(obs.get('t2m'), None),
            self._format_humidity(obs.get('rh')),
            self._format_pressure(obs.get('p_sea')),
            self._format_wind(obs.get('wd_10min'), obs.get('ws_10min'),
                              obs.get('wg_10min')),
            self._format_cloud_cover(obs.get('n_man')),
            self._format_snow_depth(obs.get('snow_aws')),
        ]
        weather_data = [wd for wd in weather_data if wd]

        weather_string = "Havainto {} {}.{}{}".format(
            parsed['location_name'] or "?",
            time_str,
            " {}.".format(conditions) if conditions else "",
            " {}.".format(', '.join(weather_data)) if weather_data else ""
        )
        return weather_string

    # ---- Forecast formatting ----

    def _format_location_name(self, parsed):
        name = parsed.get('location_name') or "?"
        country = parsed.get('country')
        region = parsed.get('region')
        if country and country != 'Finland':
            return "{} ({})".format(name, country)
        if region and region != 'Finland' and region != name:
            return "{} {}".format(region, name)
        return name

    def _format_forecast(self, parsed, forecast_idx):
        row = parsed['data'][forecast_idx]
        ts = parsed['timestamps'][forecast_idx]

        local_time = self._utc_to_local(ts)
        time_str = local_time.strftime('%d.%m.%Y %H:%M')
        location = self._format_location_name(parsed)

        conditions = None
        ws3 = row.get('WeatherSymbol3')
        if ws3 is not None:
            ws3_int = int(ws3)
            conditions = self.weather_symbol_3_strings.get(ws3_int)
            if conditions:
                conditions = self._capitalize(conditions)
            else:
                conditions = "Tuntematon sääilmiö ({})".format(ws3_int)

        temp = row.get('Temperature')
        wind_speed = row.get('WindSpeedMS')
        humidity = row.get('Humidity')
        feels_like = self._compute_feels_like(temp, wind_speed, humidity)

        weather_data = [
            self._format_temperature(temp, feels_like),
            self._format_wind(row.get('WindDirection'), wind_speed,
                              row.get('HourlyMaximumGust')),
            self._format_precipitation(row.get('Precipitation1h'),
                                       row.get('PoP')),
        ]
        weather_data = [wd for wd in weather_data if wd]

        weather_string = "Ennuste {} {}.{}{}".format(
            location, time_str,
            " {}.".format(conditions) if conditions else "",
            " {}.".format(', '.join(weather_data)) if weather_data else ""
        )
        return weather_string

    # ---- Sunrise/sunset ----

    def _format_sun_times(self, parsed, forecast_ts):
        lat = parsed.get('lat')
        lon = parsed.get('lon')
        if lat is None or lon is None:
            return ""

        local_ts = self._utc_to_local(forecast_ts)
        result = sun_times(local_ts.date(), lat, lon)
        sunrise = result.get('sunrise')
        sunset = result.get('sunset')

        if sunrise and sunset:
            sr = self._utc_to_local(sunrise).strftime('%H:%M')
            ss = self._utc_to_local(sunset).strftime('%H:%M')
            return " Aurinko nousee {} ja laskee {}.".format(sr, ss)
        return ""

    # ---- Location resolution ----

    def _get_location(self, location_param, sender):
        """Resolve location to (lat, lon, place_name_or_none) or None."""
        if not location_param:
            user = User.get_or_create(sender)
            if user and user.location:
                loc_str = user.location
            else:
                loc_str = config.LOCATION
            parts = loc_str.split(',')
            return float(parts[0]), float(parts[1]), None

        coordinates = geocoding.geocode(location_param)
        if coordinates is None:
            return None
        return coordinates[0], coordinates[1], location_param

    # ---- Main handler ----

    def _find_forecast_index(self, timestamps, params):
        if params['hours']:
            target_time = datetime.time(
                int(params['hours']), int(params['minutes'] or 0))
            target_dt = time_util.get_next_datetime_for_time(target_time)
            target_utc = time_util.get_utc_datetime(target_dt)
            target_utc = target_utc.replace(tzinfo=None)
            return min(
                range(len(timestamps)),
                key=lambda i: abs(timestamps[i] - target_utc)
            )
        return 0

    def handle(self, message):
        matches = FmiWeatherCommand.cmd_pattern.finditer(
            message.params.strip())
        params = [g.groupdict() for g in matches][0]

        loc = self._get_location(params['location'], message.sender)
        if loc is None:
            message.reply_to(
                "Sijaintia {} ei ole olemassa".format(params['location']))
            return

        lat, lon, place_name = loc
        latlon = (lat, lon)
        logging.info("Getting weather data for ({}, {})".format(lat, lon))

        if message.commandword == OBSERVATION_COMMAND:
            parsed = self._fetch_observations(latlon, place_name)
            if parsed is None:
                message.reply_to("Ei havaintotietoja paikkakunnalle {}".format(
                    params['location'] or "?"))
                return

            weather_string = self._format_observation(parsed)
            if weather_string is None:
                message.reply_to("Ei havaintotietoja paikkakunnalle {}".format(
                    params['location'] or "?"))
                return

            sun_string = ""
            if parsed.get('lat') and parsed.get('lon') \
                    and parsed['timestamps']:
                sun_string = self._format_sun_times(
                    parsed, parsed['timestamps'][-1])

            message.reply_to("{}{}".format(weather_string, sun_string))

        elif message.commandword == FORECAST_COMMAND:
            parsed = self._fetch_forecast(latlon, place_name)
            if parsed is None:
                message.reply_to(
                    "Ei ennustetietoja paikkakunnalle {}".format(
                        params['location'] or "?"))
                return

            idx = self._find_forecast_index(
                parsed['timestamps'], params)
            weather_string = self._format_forecast(parsed, idx)
            sun_string = self._format_sun_times(
                parsed, parsed['timestamps'][idx])

            message.reply_to("{}{}".format(weather_string, sun_string))
