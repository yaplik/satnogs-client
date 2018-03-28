"""
SatNOGS Client settings file
"""
import os
from os import environ, path
from distutils.util import strtobool  # pylint: disable=E0401,E0611


def _cast_or_none(func, value):
    try:
        return func(value)
    except (ValueError, TypeError):
        return None


# Ground station information
SATNOGS_API_TOKEN = environ.get('SATNOGS_API_TOKEN', None)
SATNOGS_PRE_OBSERVATION_SCRIPT = environ.get('SATNOGS_PRE_OBSERVATION_SCRIPT', None)
SATNOGS_POST_OBSERVATION_SCRIPT = environ.get('SATNOGS_POST_OBSERVATION_SCRIPT', None)
SATNOGS_STATION_ID = _cast_or_none(int, environ.get('SATNOGS_STATION_ID', None))
SATNOGS_STATION_LAT = _cast_or_none(float, environ.get('SATNOGS_STATION_LAT', None))
SATNOGS_STATION_LON = _cast_or_none(float, environ.get('SATNOGS_STATION_LON', None))
SATNOGS_STATION_ELEV = _cast_or_none(float, environ.get('SATNOGS_STATION_ELEV', None))

# Output paths
SATNOGS_APP_PATH = environ.get('SATNOGS_APP_PATH', '/tmp/.satnogs')
SATNOGS_OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp/.satnogs/data')
SATNOGS_COMPLETE_OUTPUT_PATH = environ.get('SATNOGS_COMPLETE_OUTPUT_PATH', '')
SATNOGS_INCOMPLETE_OUTPUT_PATH = environ.get('SATNOGS_INCOMPLETE_OUTPUT_PATH',
                                             '/tmp/.satnogs/data/incomplete')

for p in [SATNOGS_APP_PATH,
          SATNOGS_OUTPUT_PATH,
          SATNOGS_COMPLETE_OUTPUT_PATH,
          SATNOGS_INCOMPLETE_OUTPUT_PATH]:
    if p != "" and not os.path.exists(p):
        os.mkdir(p)

SATNOGS_REMOVE_RAW_FILES = bool(strtobool(environ.get('SATNOGS_REMOVE_RAW_FILES', 'True')))

SATNOGS_VERIFY_SSL = bool(strtobool(environ.get('SATNOGS_VERIFY_SSL', 'True')))
DEFAULT_SQLITE_PATH = path.join(SATNOGS_APP_PATH, 'jobs.sqlite')
SATNOGS_SQLITE_URL = environ.get('SATNOGS_SQLITE_URL', 'sqlite:///' + DEFAULT_SQLITE_PATH)

SATNOGS_NETWORK_API_URL = environ.get('SATNOGS_NETWORK_API_URL', 'https://network.satnogs.org/api/')
SATNOGS_NETWORK_API_QUERY_INTERVAL = 1  # In minutes
SATNOGS_NETWORK_API_POST_INTERVAL = 2  # In minutes
GNURADIO_UDP_PORT = 16886
GNURADIO_IP = '127.0.0.1'
GNURADIO_SCRIPT_PATH = ['/usr/bin', '/usr/local/bin']
GNURADIO_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_FM_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_CW_SCRIPT_FILENAME = 'satnogs_cw_decoder.py'
GNURADIO_APT_SCRIPT_FILENAME = 'satnogs_noaa_apt_decoder.py'
GNURADIO_BPSK_SCRIPT_FILENAME = 'satnogs_bpsk_decoder.py'
GNURADIO_FSK9K6_SCRIPT_FILENAME = 'satnogs_fsk9600_g3ruh_ax25.py'
GNURADIO_FSK1K2_SCRIPT_FILENAME = 'satnogs_afsk1200_ax25.py'
GNURADIO_AMSAT_DUV_SCRIPT_FILENAME = 'satnogs_amsat_fox_duv_decoder.py'
SATNOGS_RX_DEVICE = environ.get('SATNOGS_RX_DEVICE', 'rtlsdr')

SATNOGS_ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
SATNOGS_ROT_PORT = int(environ.get('SATNOGS_ROT_PORT', 4533))
SATNOGS_RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
SATNOGS_RIG_PORT = int(environ.get('SATNOGS_RIG_PORT', 4532))
SATNOGS_ROT_THRESHOLD = int(environ.get('SATNOGS_ROT_THRESHOLD', 4))

# Rigctld settings
RIG_MODEL = ""
RIG_FILE = ""
RIG_PTT_FILE = ""
RIG_PTT_TYPE = ""
RIG_SERIAL_SPEED = ""

# Common script parameters

SATNOGS_DOPPLER_CORR_PER_SEC = environ.get('SATNOGS_DOPPLER_CORR_PER_SEC', None)
SATNOGS_LO_OFFSET = environ.get('SATNOGS_LO_OFFSET', None)
SATNOGS_PPM_ERROR = environ.get('SATNOGS_PPM_ERROR', None)
SATNOGS_IF_GAIN = environ.get('SATNOGS_IF_GAIN', None)
SATNOGS_RF_GAIN = environ.get('SATNOGS_RF_GAIN', None)
SATNOGS_BB_GAIN = environ.get('SATNOGS_BB_GAIN', None)
SATNOGS_ANTENNA = environ.get('SATNOGS_ANTENNA', None)
SATNOGS_DEV_ARGS = environ.get('SATNOGS_DEV_ARGS', None)
ENABLE_IQ_DUMP = environ.get('ENABLE_IQ_DUMP', 0)
IQ_DUMP_FILENAME = environ.get('IQ_DUMP_FILENAME', None)
DISABLE_DECODED_DATA = environ.get('DISABLE_DECODED_DATA', 0)

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
            'level': 'INFO',
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
