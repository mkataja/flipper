import contextlib
import datetime
import locale
import logging
import re

import pytz

import config
from commands.command import Command
from lib import fmi, geocoding, time_util
from lib.irc_colors import Color, bold, color
from lib.sun import sun_times
from models.user import User

FORECAST_COMMAND = "sää"
RANGE_FORECAST_COMMAND = "ennuste"
OBSERVATION_COMMAND = "havainto"

DEFAULT_FORECAST_INTERVAL_HOURS = 1
MAX_FORECAST_INTERVAL_HOURS = 72
MAX_RANGE_FORECAST_ITEMS = 6
FORECAST_RANGE_BUFFER_HOURS = 6
MAX_FORECAST_RANGE_HOURS = 24 * 15


class FmiWeatherCommand(Command):
    helpstr = ("Ennuste: !sää [aika] [paikka] | !sää <N>h|<N>d [paikka] "
               "(esim. !sää 3h, !sää 1d) | !ennuste = !sää 1h "
               "| Havainto: !havainto [paikka] "
               "| Aseta oletuspaikka !koti-komennolla")

    cmd_pattern = re.compile(
        r"^(?:(?P<hours>\d\d)(?::(?P<minutes>\d\d))?)? ?(?P<location>.+?)?$"
    )
    forecast_range_pattern = re.compile(
        r"^(?P<interval_value>\d+)(?P<interval_unit>[hd]) ?(?P<location>.+?)?$",
        re.IGNORECASE,
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

    fmi_weather_code = {
        1: "selkeää",
        2: "puolipilvistä",
        3: "pilvistä",
        21: "heikkoja sadekuuroja",
        22: "sadekuuroja",
        23: "voimakkaita sadekuuroja",
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

    # Compact WW annotations for range forecast:
    fmi_weather_code_compact = {
        1: None,
        2: None,
        3: None,
        21: "sadekuuroja",
        22: "sadekuuroja",
        23: "kovia sadekuuroja",
        31: None,
        32: None,
        33: "kovaa sadetta",
        41: "lumikuuroja",
        42: "lumikuuroja",
        43: "kovia lumikuuroja",
        51: "lumisadetta",
        52: "lumisadetta",
        53: "kovaa lumisadetta",
        61: "ukkosta",
        62: "voimakasta ukkosta",
        63: "ukkosta",
        64: "voimakasta ukkosta",
        71: "räntäkuuroja",
        72: "räntäkuuroja",
        73: "kovia räntäkuuroja",
        81: "räntää",
        82: "räntää",
        83: "kovaa räntäsadetta",
        91: "utua",
        92: "sumua",
    }

    # Compact emojis for range forecast:
    fmi_weather_code_compact_emojis = {
        1: "🌞",
        2: "🌤 ",
        3: "☁️",
        21: "🌦️",
        22: "🌦️🌦️",
        23: "🌦️🌦️🌦️",
        31: "🌧️",
        32: "🌧️🌧️",
        33: "🌧️🌧️🌧️",
        41: "🌦️❄️",
        42: "🌦️❄️❄️",
        43: "🌦️❄️❄️❄️",
        51: "🌨️❄️",
        52: "🌨️❄️❄️",
        53: "🌨️❄️❄️❄️",
        61: "⛈️⛅️⚡️",
        62: "⛈️⛅️⚡️⚡️⚡️",
        63: "⛈️⚡️",
        64: "⛈️⚡️⚡️⚡️",
        71: "🌦️❄️💧",
        72: "🌦️❄️❄️💧",
        73: "🌦️❄️❄️💧💧",
        81: "🌧️❄️💧",
        82: "🌧️❄️❄️💧",
        83: "🌧️❄️❄️💧💧",
        91: "🌫️ utua",
        92: "🌫️ sumua",
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

    # Meteorological wind direction is where the wind comes from, but arrows points to where the
    # wind is blowing to:
    wind_direction_arrows = {
        "N": "↓",
        "NE": "↙",
        "E": "←",
        "SE": "↖",
        "S": "↑",
        "SW": "↗",
        "W": "→",
        "NW": "↘",
    }

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
        return color(f"{temp:.0f}", temp_color)

    def _color_wind_value(self, speed):
        if speed is None:
            return None
        if speed >= 14:
            speed_color = Color.red
        elif speed >= 8:
            speed_color = Color.yellow
        elif speed >= 5:
            speed_color = Color.white
        else:
            speed_color = None
        return color(f"{speed:.0f}", speed_color)

    def _color_precip_value(self, amount):
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
        return color(f"{amount:.1f}", amount_color)

    def _format_temp_compact(self, temp):
        colored_temp = self._color_temp_value(temp)
        if colored_temp is None:
            return None
        return f"{colored_temp}°C"

    def _format_wind_compact(self, direction_deg, speed, gust=None):
        if speed is None:
            return None
        compass = self._degrees_to_compass(direction_deg)
        direction = color(self.wind_direction_arrows.get(compass, ""), Color.white)
        wind_str = f"{direction}{self._color_wind_value(speed)}"
        if gust is not None and gust > speed + 2:
            wind_str += color(f"-{gust:.0f}", Color.dgrey)
        wind_str += "m/s"
        return wind_str

    def _format_precip_compact(self, amount, pop=None):
        if amount is None or amount < 0.1 or (pop is not None and pop <= 10):
            return None
        unit = color("mm", Color.blue)
        precip_str = f"{self._color_precip_value(amount)}{unit}"
        if pop is not None and 10 < int(pop) < 90:
            precip_str += f" ({int(pop)}%)"
        return precip_str

    def _format_temperature(self, temp, feels_like):
        temp_str = self._format_temp_compact(temp)
        if temp_str is None:
            return None
        parts = f"Lämpötila {temp_str}"
        if feels_like is not None and abs(feels_like - temp) >= 1.0:
            feels_like_str = self._format_temp_compact(feels_like)
            if feels_like_str is not None:
                parts += f" (tuntuu {feels_like_str})"
        return parts

    def _format_humidity(self, rh):
        if rh is None:
            return None
        return f"Kosteus {int(rh)}%"

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
        speed_str = self._color_wind_value(speed)

        result = f"{direction_str}tuulta {speed_str} m/s"
        if gust is not None and gust > speed + 2:
            result += f" (puuska {gust:.0f} m/s)"
        return result

    def _format_precipitation(self, amount, pop=None):
        if amount is None:
            return None
        amount_str = self._color_precip_value(amount)

        if pop is None:
            pop_str = ""
        else:
            pop_rounded = round(int(pop) / 10) * 10
            if pop_rounded < 10:
                pop_text = "<10"
                pop_color = None
            elif pop_rounded > 90:
                pop_text = ">90"
                pop_color = Color.blue
            else:
                pop_text = str(pop_rounded)
                if pop_rounded >= 70:
                    pop_color = Color.blue
                elif pop_rounded >= 30:
                    pop_color = Color.dcyan
                else:
                    pop_color = None
            pop_str = f" (sateen todennäköisyys {color(pop_text, pop_color)} %)"

        return f"Tunnin sademäärä {amount_str} mm{pop_str}"

    def _format_cloud_cover(self, cover):
        if cover is None:
            return None
        cover_int = int(cover)
        if cover_int <= 8:
            return f"Pilvisyys: {cover_int}/8"
        return "Pilvisyys: taivas ei näkyvissä"

    def _format_snow_depth(self, depth):
        if depth is None or depth <= 0:
            return None
        return f"Lumensyvyys {int(depth)} cm"

    @staticmethod
    def _capitalize(s):
        if not s:
            return s
        return s[0].upper() + s[1:]

    # ---- Observation formatting ----

    def _format_observation(self, parsed, resolved_name=None):
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
                conditions = f"Tuntematon sääilmiö ({int(wawa)})"

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
            self._format_location_name(parsed, resolved_name),
            time_str,
            f" {conditions}." if conditions else "",
            " {}.".format(', '.join(weather_data)) if weather_data else ""
        )
        return weather_string

    # ---- Forecast formatting ----

    def _format_location_name(self, parsed, resolved_name=None):
        name = parsed.get('location_name') or "?"
        country = parsed.get('country')
        region = parsed.get('region')

        if region and region != country and region != name:
            location = f"{region}, {name}"
        else:
            location = name

        if country and country != 'Finland':
            # FMI API response placenames are good in finland, but outside Finland it's better to
            # rely on geocoding result's resolved name if available:
            if resolved_name:
                return resolved_name
            else:
                return f"{location} ({country})"
        else:
            return location

    def _format_forecast(self, parsed, forecast_idx, resolved_name=None):
        row = parsed['data'][forecast_idx]
        ts = parsed['timestamps'][forecast_idx]

        local_time = self._utc_to_local(ts)
        time_str = local_time.strftime('%d.%m.%Y %H:%M')
        location = self._format_location_name(parsed, resolved_name)

        conditions = None
        ws3 = row.get('WeatherSymbol3')
        if ws3 is not None:
            ws3_int = int(ws3)
            conditions = self.fmi_weather_code.get(ws3_int)
            if conditions:
                conditions = self._capitalize(conditions)
            else:
                conditions = f"Tuntematon sääilmiö ({ws3_int})"

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
            f" {conditions}." if conditions else "",
            " {}.".format(', '.join(weather_data)) if weather_data else ""
        )
        return weather_string

    # ---- Range forecast formatting ----

    def _format_forecast_hour(self, row, ts, include_date=False, emoji_enabled=True):
        """Format a single forecast hour as a compact IRC fragment."""
        local_time = self._utc_to_local(ts)
        hour_str = local_time.strftime('%H')
        hour_label = bold(color(f"{hour_str}:", Color.white))
        date_prefix = ""
        if include_date:
            date_label = bold(color(f"{local_time.day}.{local_time.month}.", Color.white))
            date_prefix = f"[{date_label}] "

        parts = []

        ws3 = row.get('WeatherSymbol3')
        if ws3 is not None:
            weather_compact = (
                self.fmi_weather_code_compact_emojis
                if emoji_enabled
                else self.fmi_weather_code_compact
            )
            ww = weather_compact.get(int(ws3))
            if ww:
                parts.append(ww)

        temp = row.get('Temperature')
        temp_str = self._format_temp_compact(temp)
        if temp_str is not None:
            parts.append(temp_str)

        wind_speed = row.get('WindSpeedMS')
        wind_dir = row.get('WindDirection')
        wind_str = self._format_wind_compact(
            wind_dir, wind_speed, row.get('HourlyMaximumGust'))
        if wind_str is not None:
            parts.append(wind_str)

        precip = row.get('Precipitation1h')
        pop = row.get('PoP')
        precip_str = self._format_precip_compact(precip, pop)
        if precip_str is not None:
            parts.append(precip_str)

        if not parts:
            return None
        return f"{date_prefix}{hour_label} {' '.join(parts)}"

    @staticmethod
    def _parse_interval_hours(interval_match):
        interval_value = int(interval_match.group('interval_value'))
        interval_unit = interval_match.group('interval_unit').lower()
        if interval_unit == 'd':
            return interval_value * 24
        return interval_value

    @staticmethod
    def _has_forecast_content(row):
        return any(
            row.get(key) is not None
            for key in ('Temperature', 'WindSpeedMS', 'Precipitation1h', 'PoP')
        )

    def _select_range_points(self, parsed, interval_hours, now_utc):
        selected = []
        next_index = 0
        timestamps = parsed['timestamps']
        rows = parsed['data']

        for item_idx in range(MAX_RANGE_FORECAST_ITEMS):
            target_time = now_utc + datetime.timedelta(
                hours=item_idx * interval_hours)
            while (
                next_index < len(timestamps)
                and (
                    timestamps[next_index] < target_time
                    or not self._has_forecast_content(rows[next_index])
                )
            ):
                next_index += 1
            if next_index >= len(timestamps):
                break
            selected.append((timestamps[next_index], rows[next_index]))
            next_index += 1

        return selected

    @staticmethod
    def _other_forecast_model(model):
        if model == 'scandinavia':
            return 'ecmwf'
        if model == 'ecmwf':
            return 'scandinavia'
        return None

    @staticmethod
    def _merge_forecast_data(primary, secondary):
        if secondary is None:
            return primary

        merged = dict(primary)
        combined = {
            ts: row for ts, row in zip(primary['timestamps'], primary['data'],
                                       strict=False)
        }
        for ts, row in zip(secondary['timestamps'], secondary['data'], strict=False):
            combined.setdefault(ts, row)

        sorted_points = sorted(combined.items(), key=lambda item: item[0])
        merged['timestamps'] = [ts for ts, _ in sorted_points]
        merged['data'] = [row for _, row in sorted_points]
        merged['models'] = [primary.get('model'), secondary.get('model')]
        return merged

    def _format_forecast_range(self, parsed, interval_hours, resolved_name=None,
                               now_utc=None, emoji_enabled=True):
        """Assemble up to MAX_RANGE_FORECAST_ITEMS sampled forecast points."""
        location = self._format_location_name(parsed, resolved_name)
        if now_utc is None:
            now_utc = datetime.datetime.utcnow().replace(
                minute=0, second=0, microsecond=0)

        hour_strings = []
        last_date_marker = None
        selected_points = self._select_range_points(parsed, interval_hours, now_utc)
        for ts, row in selected_points:
            point_local_date = self._utc_to_local(ts).date()
            include_date = point_local_date != last_date_marker
            if include_date:
                last_date_marker = point_local_date
            hour_string = self._format_forecast_hour(
                row, ts, include_date=include_date, emoji_enabled=emoji_enabled)
            if hour_string:
                hour_strings.append(hour_string)

        if not hour_strings:
            return None

        hours_joined = '  '.join(hour_strings)
        return f"Ennuste {location} {hours_joined}"

    @staticmethod
    def _is_emoji_enabled(message):
        user = getattr(message, "user", None)
        if user is not None and getattr(user, "emoji_enabled", None) is not None:
            return bool(user.emoji_enabled)

        sender = getattr(message, "sender", None)
        if sender is None:
            return True

        with contextlib.suppress(BaseException):
            db_user = User.get_or_create(sender)
            if getattr(db_user, "emoji_enabled", None) is not None:
                return bool(db_user.emoji_enabled)
        return True

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
            day_seconds = int((sunset - sunrise).total_seconds())
            day_h = day_seconds // 3600
            day_m = (day_seconds % 3600) // 60
            return (f" Aurinko nousee {sr} ja laskee {ss}"
                    f" (päivän pituus {day_h} h {day_m:02d} min).")
        return ""

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

    def _handle_forecast_range(self, message, interval_hours, location_param):
        if interval_hours <= 0:
            message.reply_to("Ennustevälin täytyy olla vähintään 1h")
            return
        if interval_hours > MAX_FORECAST_INTERVAL_HOURS:
            message.reply_to(
                f"Ennusteväli voi olla enintään {MAX_FORECAST_INTERVAL_HOURS}h")
            return
        loc = geocoding.resolve_location(location_param, message.sender)
        if loc is None:
            message.reply_to(
                f"Sijaintia {location_param} ei ole olemassa")
            return

        lat = loc.latitude
        lon = loc.longitude
        resolved_name = loc.resolved_name if loc.source == 'geocode' else None
        logging.info(
            f"Getting interval forecast every {interval_hours}h for ({lat}, {lon})")

        now_utc = datetime.datetime.utcnow().replace(
            minute=0, second=0, microsecond=0)
        # Keep the original default endpoint behavior first.
        parsed = fmi.fetch_forecast((lat, lon))
        if parsed is None:
            message.reply_to(
                "Ei ennustetietoja paikkakunnalle {}".format(
                    location_param or "?"))
            return

        selected_points = self._select_range_points(parsed, interval_hours, now_utc)
        if len(selected_points) < MAX_RANGE_FORECAST_ITEMS:
            range_hours = min(
                (MAX_RANGE_FORECAST_ITEMS - 1) * interval_hours
                + FORECAST_RANGE_BUFFER_HOURS,
                MAX_FORECAST_RANGE_HOURS,
            )
            end_utc = now_utc + datetime.timedelta(hours=range_hours)
            primary_model = parsed.get('model')

            # First try to extend the same model horizon.
            if primary_model is not None:
                extended_primary = fmi.fetch_forecast_for_model(
                    (lat, lon), primary_model, starttime=now_utc, endtime=end_utc)
                parsed = self._merge_forecast_data(parsed, extended_primary)
                selected_points = self._select_range_points(
                    parsed, interval_hours, now_utc)

        if len(selected_points) < MAX_RANGE_FORECAST_ITEMS:
            other_model = self._other_forecast_model(parsed.get('model'))
            if other_model is not None:
                logging.info(
                    f"Primary model returned only {len(selected_points)} points; "
                    f"trying {other_model} as supplementary forecast")
                other_parsed = fmi.fetch_forecast_for_model(
                    (lat, lon), other_model, starttime=now_utc, endtime=end_utc)
                parsed = self._merge_forecast_data(parsed, other_parsed)

        result = self._format_forecast_range(
            parsed,
            interval_hours,
            resolved_name,
            now_utc=now_utc,
            emoji_enabled=self._is_emoji_enabled(message),
        )
        if result is None:
            message.reply_to(
                "Ei ennustetietoja paikkakunnalle {}".format(
                    location_param or "?"))
            return

        message.reply_to(result)

    def handle(self, message):
        params_str = message.params.strip()
        range_match = FmiWeatherCommand.forecast_range_pattern.match(params_str)

        if message.commandword in (FORECAST_COMMAND, RANGE_FORECAST_COMMAND) and range_match:
            interval_hours = self._parse_interval_hours(range_match)
            self._handle_forecast_range(
                message,
                interval_hours,
                range_match.group('location')
            )
            return

        if message.commandword == RANGE_FORECAST_COMMAND:
            # !ennuste defaults to !sää 1h [location], but explicit HH[:MM] still works.
            default_match = FmiWeatherCommand.cmd_pattern.match(params_str)
            if default_match is not None and not default_match.group('hours'):
                self._handle_forecast_range(
                    message,
                    DEFAULT_FORECAST_INTERVAL_HOURS,
                    params_str or None
                )
                return

        matches = FmiWeatherCommand.cmd_pattern.finditer(
            params_str)
        params = [g.groupdict() for g in matches][0]

        loc = geocoding.resolve_location(params['location'], message.sender)
        if loc is None:
            message.reply_to(
                "Sijaintia {} ei ole olemassa".format(params['location']))
            return

        lat = loc.latitude
        lon = loc.longitude
        resolved_name = loc.resolved_name if loc.source == 'geocode' else None
        logging.info(f"Getting weather data for ({lat}, {lon})")

        if message.commandword == OBSERVATION_COMMAND:
            parsed = fmi.fetch_observations((lat, lon))
            weather_string = self._format_observation(parsed, resolved_name) if parsed else None

            if weather_string is None:
                message.reply_to("Ei havaintotietoja paikkakunnalle {}".format(
                    params['location'] or "?"))
                return

            sun_string = ""
            if parsed.get('lat') and parsed.get('lon') \
                    and parsed['timestamps']:
                sun_string = self._format_sun_times(
                    parsed, parsed['timestamps'][-1])

            message.reply_to(f"{weather_string}{sun_string}")

        elif message.commandword in (FORECAST_COMMAND, RANGE_FORECAST_COMMAND):
            parsed = fmi.fetch_forecast((lat, lon))
            if parsed is None:
                message.reply_to(
                    "Ei ennustetietoja paikkakunnalle {}".format(
                        params['location'] or "?"))
                return

            idx = self._find_forecast_index(
                parsed['timestamps'], params)
            weather_string = self._format_forecast(parsed, idx, resolved_name)
            sun_string = self._format_sun_times(
                parsed, parsed['timestamps'][idx])

            message.reply_to(f"{weather_string}{sun_string}")
