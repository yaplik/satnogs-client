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
SATNOGS_API_TOKEN = environ.get('SATNOGS_API_TOKEN', None)
SATNOGS_STATION_ID = _cast_or_none(int, environ.get('SATNOGS_STATION_ID', None))
SATNOGS_STATION_LAT = _cast_or_none(float, environ.get('SATNOGS_STATION_LAT', None))
SATNOGS_STATION_LON = _cast_or_none(float, environ.get('SATNOGS_STATION_LON', None))
SATNOGS_STATION_ELEV = _cast_or_none(float, environ.get('SATNOGS_STATION_ELEV', None))


# Output paths
SATNOGS_APP_PATH = environ.get('SATNOGS_APP_PATH', '/tmp/.satnogs')
SATNOGS_OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp/.satnogs/data')
SATNOGS_COMPLETE_OUTPUT_PATH = environ.get('SATNOGS_COMPLETE_OUTPUT_PATH', '/tmp/.satnogs/data/complete')
SATNOGS_INCOMPLETE_OUTPUT_PATH = environ.get('SATNOGS_INCOMPLETE_OUTPUT_PATH', '/tmp/.satnogs/data/incomplete')

for p in [SATNOGS_APP_PATH, SATNOGS_OUTPUT_PATH, SATNOGS_COMPLETE_OUTPUT_PATH, SATNOGS_INCOMPLETE_OUTPUT_PATH]:
    if not os.path.exists(p):
        os.mkdir(p)

SATNOGS_REMOVE_RAW_FILES = bool(strtobool(environ.get('SATNOGS_REMOVE_RAW_FILES', 'True')))

SATNOGS_VERIFY_SSL = bool(strtobool(environ.get('SATNOGS_VERIFY_SSL', 'True')))
DEFAULT_SQLITE_PATH = path.join(SATNOGS_APP_PATH, 'jobs.sqlite')
SATNOGS_SQLITE_URL = environ.get('SATNOGS_SQLITE_URL', 'sqlite:///' + DEFAULT_SQLITE_PATH)

SATNOGS_NETWORK_API_URL = environ.get('SATNOGS_NETWORK_API_URL', 'https://network-dev.satnogs.org/api/')
SATNOGS_NETWORK_API_QUERY_INTERVAL = 1  # In minutes
SATNOGS_NETWORK_API_POST_INTERVAL = 2  # In minutes
GNURADIO_UDP_PORT = 16886
GNURADIO_IP = '127.0.0.1'
GNURADIO_SCRIPT_PATH = ['/usr/bin', '/usr/local/bin']
GNURADIO_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_FM_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_CW_SCRIPT_FILENAME = 'satnogs_cw_demod.py'
SATNOGS_RX_DEVICE = environ.get('SATNOGS_RX_DEVICE', 'rtlsdr')
CURRENT_PASS_TCP_PORT = 5005

SATNOGS_ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
SATNOGS_ROT_PORT = int(environ.get('SATNOGS_ROT_PORT', 4533))
SATNOGS_RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
SATNOGS_RIG_PORT = int(environ.get('SATNOGS_RIG_PORT', 4532))

SATNOGS_SERIAL_PORT = environ.get('SATNOGS_SERIAL_PORT', None)

SATNOGS_PPM_ERROR = environ.get('SATNOGS_PPM_ERROR', 0)

# Rigctld settings
RIG_MODEL = ""
RIG_FILE = ""
RIG_PTT_FILE = ""
RIG_PTT_TYPE = ""
RIG_SERIAL_SPEED = ""

# UPSat Specific settings
RF_SW_CMD_OFF_INT = _cast_or_none(int, environ.get('RF_SW_CMD_OFF_INT', None))
RF_SW_CMD_OFF_CHAR_SEQ = environ.get('RF_SW_CMD_OFF_CHAR_SEQ', None)
RF_SW_CMD_ON_INT = _cast_or_none(int, environ.get('RF_SW_CMD_ON_INT', None))
RF_SW_CMD_ON_CHAR_SEQ = environ.get('RF_SW_CMD_ON_CHAR_SEQ', None)
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
