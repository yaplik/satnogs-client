"""
SatNOGS Client settings file
"""
from __future__ import absolute_import, division, print_function

import os
from distutils.util import strtobool  # pylint: disable=E0401,E0611
from os import environ

from dotenv import load_dotenv
from validators.url import url


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
SATNOGS_GPSD_CLIENT_ENABLED = bool(strtobool(environ.get('SATNOGS_GPSD_CLIENT_ENABLED', 'False')))
SATNOGS_GPSD_HOST = environ.get('SATNOGS_GPSD_HOST', "127.0.0.1")
SATNOGS_GPSD_PORT = _cast_or_none(int, environ.get('SATNOGS_GPSD_PORT', 2947))
SATNOGS_GPSD_TIMEOUT = _cast_or_none(int, environ.get('SATNOGS_GPSD_TIMEOUT', 0))

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
SATNOGS_NETWORK_API_TIMEOUT = 1800  # In seconds
GNURADIO_UDP_PORT = 16886
GNURADIO_IP = '127.0.0.1'
GNURADIO_SCRIPT_PATH = ['/usr/bin', '/usr/local/bin']
GNURADIO_SCRIPT_FILENAME = 'satnogs_fsk_ax25.py'
GNURADIO_CW_SCRIPT_FILENAME = 'satnogs_cw_decoder.py'
GNURADIO_APT_SCRIPT_FILENAME = 'satnogs_noaa_apt_decoder.py'
GNURADIO_BPSK_SCRIPT_FILENAME = 'satnogs_bpsk_ax25.py'
GNURADIO_GFSK_RKTR_SCRIPT_FILENAME = 'satnogs_reaktor_hello_world_fsk9600_decoder.py'
GNURADIO_FSK_SCRIPT_FILENAME = 'satnogs_fsk_ax25.py'
GNURADIO_AFSK1K2_SCRIPT_FILENAME = 'satnogs_afsk1200_ax25.py'
GNURADIO_AFSK_SALSAT_SCRIPT_FILENAME = 'satnogs_afsk_salsat.py'
GNURADIO_AFSK_SNET_SCRIPT_FILENAME = 'satnogs_afsk_snet.py'
GNURADIO_AMSAT_DUV_SCRIPT_FILENAME = 'satnogs_amsat_fox_duv_decoder.py'
GNURADIO_SSTV_SCRIPT_FILENAME = 'satnogs_sstv_pd120_demod.py'

SATNOGS_ROT_IP = environ.get('SATNOGS_ROT_IP', '127.0.0.1')
SATNOGS_ROT_MODEL = environ.get('SATNOGS_ROT_MODEL', 'ROT_MODEL_DUMMY')
SATNOGS_ROT_BAUD = int(environ.get('SATNOGS_ROT_BAUD', 19200))
SATNOGS_ROT_PORT = environ.get('SATNOGS_ROT_PORT', '/dev/ttyUSB0')
SATNOGS_RIG_IP = environ.get('SATNOGS_RIG_IP', '127.0.0.1')
SATNOGS_RIG_PORT = int(environ.get('SATNOGS_RIG_PORT', 4532))
SATNOGS_ROT_THRESHOLD = int(environ.get('SATNOGS_ROT_THRESHOLD', 4))
SATNOGS_ROT_FLIP = bool(strtobool(environ.get('SATNOGS_ROT_FLIP', 'False')))
SATNOGS_ROT_FLIP_ANGLE = int(environ.get('SATNOGS_ROT_FLIP_ANGLE', 75))

# Common script parameters
SATNOGS_SOAPY_RX_DEVICE = environ.get('SATNOGS_SOAPY_RX_DEVICE', None)
SATNOGS_RX_SAMP_RATE = environ.get('SATNOGS_RX_SAMP_RATE', None)
SATNOGS_RX_BANDWIDTH = environ.get('SATNOGS_RX_BANDWIDTH', None)
SATNOGS_DOPPLER_CORR_PER_SEC = environ.get('SATNOGS_DOPPLER_CORR_PER_SEC', None)
SATNOGS_LO_OFFSET = environ.get('SATNOGS_LO_OFFSET', None)
SATNOGS_PPM_ERROR = environ.get('SATNOGS_PPM_ERROR', None)
SATNOGS_GAIN_MODE = environ.get('SATNOGS_GAIN_MODE', 'Overall')
SATNOGS_RF_GAIN = environ.get('SATNOGS_RF_GAIN', None)
SATNOGS_ANTENNA = environ.get('SATNOGS_ANTENNA', None)
SATNOGS_DEV_ARGS = environ.get('SATNOGS_DEV_ARGS', None)
SATNOGS_STREAM_ARGS = environ.get('SATNOGS_STREAM_ARGS', None)
SATNOGS_TUNE_ARGS = environ.get('SATNOGS_TUNE_ARGS', None)
SATNOGS_OTHER_SETTINGS = environ.get('SATNOGS_OTHER_SETTINGS', None)
SATNOGS_DC_REMOVAL = environ.get('SATNOGS_DC_REMOVAL', None)
SATNOGS_BB_FREQ = environ.get('SATNOGS_BB_FREQ', None)

ENABLE_IQ_DUMP = bool(strtobool(environ.get('ENABLE_IQ_DUMP', 'False')))
IQ_DUMP_FILENAME = environ.get('IQ_DUMP_FILENAME', None)
DISABLE_DECODED_DATA = bool(strtobool(environ.get('DISABLE_DECODED_DATA', 'False')))

# Waterfall settings
SATNOGS_WATERFALL_AUTORANGE = bool(strtobool(environ.get('SATNOGS_WATERFALL_AUTORANGE', 'True')))
SATNOGS_WATERFALL_MIN_VALUE = int(environ.get('SATNOGS_WATERFALL_MIN_VALUE', -100))
SATNOGS_WATERFALL_MAX_VALUE = int(environ.get('SATNOGS_WATERFALL_MAX_VALUE', -50))

# Logging configuration
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = environ.get('SATNOGS_LOG_LEVEL', 'WARNING')
SCHEDULER_LOG_LEVEL = environ.get('SATNOGS_SCHEDULER_LOG_LEVEL', 'WARNING')

# Sentry
SENTRY_DSN = environ.get('SENTRY_DSN', '')

REQUIRED_VARIABLES = [
    'SATNOGS_API_TOKEN', 'SATNOGS_STATION_ID', 'SATNOGS_STATION_LAT', 'SATNOGS_STATION_LON',
    'SATNOGS_STATION_ELEV', 'SATNOGS_SOAPY_RX_DEVICE', 'SATNOGS_RX_SAMP_RATE', 'SATNOGS_ANTENNA'
]


def validate(logger):
    """
    Validate the provided settings:
    - Check for the existance of all required variables
    - Validate format of the provided value for some required variables

    Since this module has to be loaded before the logger has been initialized,
    this method requires a configured logger to be passed.

    Arguments:
    logger -- the output logger
    """
    settings_valid = True

    # Get all variable in global scobe (this includes all global variables from this module)
    settings = globals()

    for variable_name in REQUIRED_VARIABLES:
        # Check the value of the variable defined in settings
        if not settings[variable_name]:
            logger.error('%s not configured but required', variable_name)
            settings_valid = False

    try:
        url(SATNOGS_NETWORK_API_URL)
    except ValueError:
        logger.error('Invalid SATNOGS_NETWORK_API_URL: %s', SATNOGS_NETWORK_API_URL)
        settings_valid = False

    if not (SATNOGS_STATION_LAT or SATNOGS_GPSD_CLIENT_ENABLED):
        logger.error('SATNOGS_STATION_LAT not configured')
        settings_valid = False

    if not (SATNOGS_STATION_LON or SATNOGS_GPSD_CLIENT_ENABLED):
        logger.error('SATNOGS_STATION_LON not configured')
        settings_valid = False

    if SATNOGS_STATION_ELEV is None and SATNOGS_GPSD_CLIENT_ENABLED is False:
        logger.error('SATNOGS_STATION_ELEV not configured')
        settings_valid = False

    return settings_valid
