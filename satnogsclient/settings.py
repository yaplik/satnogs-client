"""
SatNOGS Client settings file
"""
from __future__ import absolute_import, division, print_function

import os
from distutils.util import strtobool  # pylint: disable=E0401,E0611
from os import environ

from dotenv import load_dotenv


def _cast_or_none(func, value):
    try:
        return func(value)
    except (ValueError, TypeError):
        return None


load_dotenv()

# Ground station information
SATNOGS_API_TOKEN = environ.get('SATNOGS_API_TOKEN', None)
SATNOGS_PRE_OBSERVATION_SCRIPT = environ.get('SATNOGS_PRE_OBSERVATION_SCRIPT', None)
SATNOGS_POST_OBSERVATION_SCRIPT = environ.get('SATNOGS_POST_OBSERVATION_SCRIPT', None)
SATNOGS_STATION_ID = _cast_or_none(int, environ.get('SATNOGS_STATION_ID', None))
SATNOGS_STATION_LAT = _cast_or_none(float, environ.get('SATNOGS_STATION_LAT', None))
SATNOGS_STATION_LON = _cast_or_none(float, environ.get('SATNOGS_STATION_LON', None))
SATNOGS_STATION_ELEV = _cast_or_none(int, environ.get('SATNOGS_STATION_ELEV', None))
GPSD_ENABLED = bool(strtobool(environ.get('GPSD_ENABLED', 'False')))

# Output paths
SATNOGS_APP_PATH = environ.get('SATNOGS_APP_PATH', '/tmp/.satnogs')
SATNOGS_OUTPUT_PATH = environ.get('SATNOGS_OUTPUT_PATH', '/tmp/.satnogs/data')
SATNOGS_COMPLETE_OUTPUT_PATH = environ.get('SATNOGS_COMPLETE_OUTPUT_PATH', '')
SATNOGS_INCOMPLETE_OUTPUT_PATH = environ.get('SATNOGS_INCOMPLETE_OUTPUT_PATH',
                                             '/tmp/.satnogs/data/incomplete')

for p in [
        SATNOGS_APP_PATH, SATNOGS_OUTPUT_PATH, SATNOGS_COMPLETE_OUTPUT_PATH,
        SATNOGS_INCOMPLETE_OUTPUT_PATH
]:
    if p != "" and not os.path.exists(p):
        os.mkdir(p)

SATNOGS_REMOVE_RAW_FILES = bool(strtobool(environ.get('SATNOGS_REMOVE_RAW_FILES', 'True')))

SATNOGS_VERIFY_SSL = bool(strtobool(environ.get('SATNOGS_VERIFY_SSL', 'True')))

SATNOGS_NETWORK_API_URL = environ.get('SATNOGS_NETWORK_API_URL',
                                      'https://network.satnogs.org/api/')
SATNOGS_NETWORK_API_QUERY_INTERVAL = 1  # In minutes
SATNOGS_NETWORK_API_POST_INTERVAL = 2  # In minutes
GNURADIO_UDP_PORT = 16886
GNURADIO_IP = '127.0.0.1'
GNURADIO_SCRIPT_PATH = ['/usr/bin', '/usr/local/bin']
GNURADIO_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_FM_SCRIPT_FILENAME = 'satnogs_fm_demod.py'
GNURADIO_CW_SCRIPT_FILENAME = 'satnogs_cw_decoder.py'
GNURADIO_APT_SCRIPT_FILENAME = 'satnogs_noaa_apt_decoder.py'
GNURADIO_BPSK_SCRIPT_FILENAME = 'satnogs_bpsk_ax25.py'
GNURADIO_GFSK_RKTR_SCRIPT_FILENAME = 'satnogs_reaktor_hello_world_fsk9600_decoder.py'
GNURADIO_FSK_SCRIPT_FILENAME = 'satnogs_fsk_ax25.py'
GNURADIO_MSK_SCRIPT_FILENAME = 'satnogs_msk_ax25.py'
GNURADIO_AFSK1K2_SCRIPT_FILENAME = 'satnogs_afsk1200_ax25.py'
GNURADIO_AMSAT_DUV_SCRIPT_FILENAME = 'satnogs_amsat_fox_duv_decoder.py'
SATNOGS_RX_DEVICE = environ.get('SATNOGS_RX_DEVICE', 'rtlsdr')

SATNOGS_ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
SATNOGS_ROT_PORT = int(environ.get('SATNOGS_ROT_PORT', 4533))
SATNOGS_RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
SATNOGS_RIG_PORT = int(environ.get('SATNOGS_RIG_PORT', 4532))
SATNOGS_ROT_THRESHOLD = int(environ.get('SATNOGS_ROT_THRESHOLD', 4))
SATNOGS_ROT_FLIP = bool(strtobool(environ.get('SATNOGS_ROT_FLIP', 'False')))
SATNOGS_ROT_FLIP_ANGLE = int(environ.get('SATNOGS_ROT_FLIP_ANGLE', 75))

# Common script parameters

SATNOGS_DOPPLER_CORR_PER_SEC = environ.get('SATNOGS_DOPPLER_CORR_PER_SEC', None)
SATNOGS_LO_OFFSET = environ.get('SATNOGS_LO_OFFSET', None)
SATNOGS_PPM_ERROR = environ.get('SATNOGS_PPM_ERROR', None)
SATNOGS_IF_GAIN = environ.get('SATNOGS_IF_GAIN', None)
SATNOGS_RF_GAIN = environ.get('SATNOGS_RF_GAIN', None)
SATNOGS_BB_GAIN = environ.get('SATNOGS_BB_GAIN', None)
SATNOGS_ANTENNA = environ.get('SATNOGS_ANTENNA', None)
SATNOGS_DEV_ARGS = environ.get('SATNOGS_DEV_ARGS', None)
ENABLE_IQ_DUMP = bool(strtobool(environ.get('ENABLE_IQ_DUMP', 'False')))
IQ_DUMP_FILENAME = environ.get('IQ_DUMP_FILENAME', None)
DISABLE_DECODED_DATA = bool(strtobool(environ.get('DISABLE_DECODED_DATA', 'False')))

# Waterfall settings
SATNOGS_WATERFALL_AUTORANGE = environ.get('SATNOGS_WATERFALL_AUTORANGE', True)
SATNOGS_WATERFALL_MIN_VALUE = environ.get('SATNOGS_WATERFALL_MIN_VALUE', -100)
SATNOGS_WATERFALL_MAX_VALUE = environ.get('SATNOGS_WATERFALL_MAX_VALUE', -50)

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = environ.get('SATNOGS_LOG_LEVEL', 'WARNING')
