# -*- coding: utf-8 -*-
from os import environ

GROUND_STATION_ID = int(environ.get('SATNOGS_STATION_ID', None))
GROUND_STATION_LAT = float(environ.get('SATNOGS_STATION_LAT', None))
GROUND_STATION_LON = float(environ.get('SATNOGS_STATION_LON', None))
GROUND_STATION_ELEV = float(environ.get('SATNOGS_STATION_ELEV', None))

SQLITE_URL = environ.get('SATNOGS_SQLITE_URL', 'sqlite:///jobs.sqlite')
DEMODULATION_COMMAND = environ.get('SATNOGS_DEMODULATION_COMMAND', 'rtl_fm')
ENCODING_COMMAND = environ.get('SATNOGS_ENCODING_COMMAND', 'oggenc')
DECODING_COMMAND = environ.get('SATNOGS_DECODING_COMMAND', 'multimon-ng')
OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp')
NETWORK_API_URL = environ.get('SATNOGS_API_URL', 'https://dev.satnogs.org/api/')
NETWORK_API_QUERY_INTERVAL = 5  # In minutes
SCHEDULER_SLEEP_TIME = 10  # In seconds

ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
ROT_PORT = environ.get('SATNOGS_ROT_PORT', 5005)
RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
RIG_PORT = environ.get('SATNOGS_RIG_PORT', 6006)
