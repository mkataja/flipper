import datetime
import logging
import math
import urllib.parse
import xml.etree.ElementTree as ET

from lib.http import try_text_request

RETRIES = 5

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


def build_wfs_url(stored_query, params, location_params, extra=None):
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
    return f"{FMI_WFS_BASE}?{urllib.parse.urlencode(url_params)}"


def latlon_params(latlon):
    return {'latlon': f'{latlon[0]},{latlon[1]}'}


def bbox_params(latlon, margin=0.3):
    """Bounding box around coordinates (for APIs that don't support latlon)."""
    lat, lon = latlon
    return {
        'bbox': f'{lon - margin},{lat - margin},{lon + margin},{lat + margin}'
    }


def parse_multipointcoverage(xml_text):
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

    member = root.find(f'{WFS_NS}member')
    if member is None:
        return None

    location_name = None
    region = None
    country = None

    for name_elem in root.iter(f'{GML_NS}name'):
        cs = name_elem.get('codeSpace', '')
        if 'locationcode/name' in cs:
            location_name = name_elem.text
            break

    for elem in root.iter(f'{TARGET_NS}region'):
        region = elem.text.strip() if elem.text else None
    for elem in root.iter(f'{TARGET_NS}country'):
        country = elem.text.strip() if elem.text else None

    lat, lon = None, None
    pos_elem = root.find(f'.//{GML_NS}pos')
    if pos_elem is not None and pos_elem.text:
        parts = pos_elem.text.strip().split()
        if len(parts) >= 2:
            lat, lon = float(parts[0]), float(parts[1])

    timestamps = []
    position_coords = []
    positions_elem = root.find(f'.//{GMLCOV_NS}positions')
    if positions_elem is not None and positions_elem.text:
        for line in positions_elem.text.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) >= 3:
                ts = (datetime.datetime(1970, 1, 1)
                      + datetime.timedelta(seconds=int(parts[2])))
                timestamps.append(ts)
                position_coords.append((float(parts[0]), float(parts[1])))

    param_names = []
    for field in root.iter(f'{SWE_NS}field'):
        name = field.get('name')
        if name:
            param_names.append(name)

    all_values = []
    tuple_list = root.find(f'.//{GML_NS}doubleOrNilReasonTupleList')
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
        if i < len(position_coords) and position_coords[i] == first_coord:
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


def fetch_observations(latlon):
    loc = bbox_params(latlon)
    url = build_wfs_url(
        'fmi::observations::weather::multipointcoverage',
        OBSERVATION_PARAMS, loc,
        {'timestep': '60', 'maxlocations': '1'}
    )
    xml_text = try_text_request(url, retries=RETRIES)
    if xml_text is None:
        return None
    return parse_multipointcoverage(xml_text)


def fetch_forecast(latlon, starttime=None, endtime=None):
    """Fetch hourly forecast. Try Edited Scandinavia first (PoP), fall back to ECMWF.

    starttime/endtime are optional naive UTC datetimes for time range queries.
    """
    loc = latlon_params(latlon)

    extra = {'timestep': '60'}
    if starttime is not None:
        extra['starttime'] = starttime.strftime('%Y-%m-%dT%H:%M:%SZ')
    if endtime is not None:
        extra['endtime'] = endtime.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = build_wfs_url(
        'fmi::forecast::edited::weather::scandinavia::point'
        '::multipointcoverage',
        SCANDINAVIA_FORECAST_PARAMS, loc,
        extra
    )
    xml_text = try_text_request(url, retries=RETRIES)
    if xml_text is not None:
        result = parse_multipointcoverage(xml_text)
        if result is not None:
            result['model'] = 'scandinavia'
            return result

    logging.info("Scandinavia forecast unavailable, trying ECMWF")
    url = build_wfs_url(
        'ecmwf::forecast::surface::point::multipointcoverage',
        ECMWF_FORECAST_PARAMS, loc,
        {'timestep': '360'}
    )
    xml_text = try_text_request(url, retries=RETRIES)
    if xml_text is None:
        return None

    result = parse_multipointcoverage(xml_text)
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
