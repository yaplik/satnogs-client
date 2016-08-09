# -*- coding: utf-8 -*-
import os
from distutils.util import strtobool
from os import environ, path


def _cast_or_none(func, value):
    try:
        return func(value)
    except:
        return None

# Ground station information
API_TOKEN = environ.get('SATNOGS_API_TOKEN', None)
GROUND_STATION_ID = _cast_or_none(int, environ.get('SATNOGS_STATION_ID', None))
GROUND_STATION_LAT = _cast_or_none(float, environ.get('SATNOGS_STATION_LAT', None))
GROUND_STATION_LON = _cast_or_none(float, environ.get('SATNOGS_STATION_LON', None))
GROUND_STATION_ELEV = _cast_or_none(float, environ.get('SATNOGS_STATION_ELEV', None))
RF_SW_CMD_OFF_1 = _cast_or_none(int, environ.get('RF_SW_CMD_OFF_1', None))
RF_SW_CMD_OFF_2 = _cast_or_none(int, environ.get('RF_SW_CMD_OFF_2', None))
RF_SW_CMD_OFF_3 = _cast_or_none(int, environ.get('RF_SW_CMD_OFF_3', None))
RF_SW_CMD_OFF_4 = _cast_or_none(int, environ.get('RF_SW_CMD_OFF_4', None))
RF_SW_CMD_ON_1 = _cast_or_none(int, environ.get('RF_SW_CMD_ON_1', None))
RF_SW_CMD_ON_2 = _cast_or_none(int, environ.get('RF_SW_CMD_ON_2', None))
RF_SW_CMD_ON_3 = _cast_or_none(int, environ.get('RF_SW_CMD_ON_3', None))
RF_SW_CMD_ON_4 = _cast_or_none(int, environ.get('RF_SW_CMD_ON_4', None))


# Output paths
APP_PATH = environ.get('SATNOGS_APP_PATH', '/tmp/.satnogs')
OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp/.satnogs/data')
COMPLETE_OUTPUT_PATH = environ.get('SATNOGS_COMPLETE_PATH', '/tmp/.satnogs/data/complete')
INCOMPLETE_OUTPUT_PATH = environ.get('SATNOGS_INCOMPLETE_PATH', '/tmp/.satnogs/data/incomplete')

for p in [APP_PATH, OUTPUT_PATH, COMPLETE_OUTPUT_PATH, INCOMPLETE_OUTPUT_PATH]:
    if not os.path.exists(p):
        os.mkdir(p)

VERIFY_SSL = bool(strtobool(environ.get('SATNOGS_VERIFY_SSL', 'True')))
DEFAULT_SQLITE_PATH = path.join(APP_PATH, 'jobs.sqlite')
SQLITE_URL = environ.get('SATNOGS_SQLITE_URL', 'sqlite:///' + DEFAULT_SQLITE_PATH)
DEMODULATION_COMMAND = environ.get('SATNOGS_DEMODULATION_COMMAND', 'rtl_fm')
ENCODING_COMMAND = environ.get('SATNOGS_ENCODING_COMMAND', 'oggenc')
DECODING_COMMAND = environ.get('SATNOGS_DECODING_COMMAND', 'multimon-ng')

NETWORK_API_URL = environ.get('SATNOGS_API_URL', 'https://network-dev.satnogs.org/api/')
NETWORK_API_QUERY_INTERVAL = 5  # In minutes
NETWORK_API_POST_INTERVAL = 15  # In minutes
DEMODULATOR_INIT_TIME = int(environ.get('SATNOGS_DEMODULATOR_INIT_TIME', 5))  # In seconds
SCHEDULER_SLEEP_TIME = 10  # In seconds
GNURADIO_UDP_PORT = 16886
GNURADIO_IP = '127.0.0.1'
CURRENT_PASS_TCP_PORT = 5005
BACKEND_LISTENER_PORT = 5022
BACKEND_FEEDER_PORT = 5023
CLIENT_LISTENER_UDP_PORT = 5015
TASK_FEEDER_TCP_PORT = 5011
ECSS_FEEDER_UDP_PORT = 5031
STATUS_LISTENER_PORT = 5032
LD_UPLINK_LISTEN_PORT = 5021
LD_UPLINK_TIMEOUT = 2.5
WOD_UDP_PORT = 5023
LD_DOWNLINK_LISTEN_PORT = 5033
LD_DOWNLINK_TIMEOUT = 5
LD_DOWNLINK_SMALL_TIMEOUT = 2
LD_DOWNLINK_RETRIES_LIM = 5

ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
ROT_PORT = int(environ.get('SATNOGS_ROT_PORT', 4533))
RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
RIG_PORT = int(environ.get('SATNOGS_RIG_PORT', 4532))

PPM_ERROR = float(environ.get('SATNOGS_PPM_ERROR', 0))

SERIAL_PORT = environ.get('SERIAL_PORT', None)

# Logging configuration
DEFAULT_LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'clientFormatter'
        }
    },
    'loggers': {
        'satnogsclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'apscheduler.executors.default': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
    'formatters': {
        'clientFormatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
}
