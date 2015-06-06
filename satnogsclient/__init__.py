import logging.config
from os import environ

from validators.url import url

from satnogsclient.settings import (API_TOKEN, DEFAULT_LOGGING, GROUND_STATION_ID,
                                    GROUND_STATION_LAT, GROUND_STATION_LON, GROUND_STATION_ELEV,
                                    NETWORK_API_URL)


# Avoid validation when building docs
if not environ.get('READTHEDOCS', False):
    try:
        url(NETWORK_API_URL)
    except:
        raise Exception('Invalid NETWORK_API_URL: {0}'.format(NETWORK_API_URL))

    if not GROUND_STATION_ID:
        raise Exception('GROUND_STATION_ID not configured.')

    if not GROUND_STATION_LAT:
        raise Exception('GROUND_STATION_LAT not configured')

    if not GROUND_STATION_LON:
        raise Exception('GROUND_STATION_LON not configured')

    if GROUND_STATION_ELEV is None:
        raise Exception('GROUND_STATION_ELEV not configured')

    if not API_TOKEN:
        raise Exception('API_TOKEN not configured')

    logging.config.dictConfig(DEFAULT_LOGGING)
