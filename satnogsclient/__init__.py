import logging.config
from os import environ

from validators.url import url

from satnogsclient.settings import (SATNOGS_API_TOKEN, DEFAULT_LOGGING, SATNOGS_STATION_ID,
                                    SATNOGS_STATION_LAT, SATNOGS_STATION_LON, SATNOGS_STATION_ELEV,
                                    SATNOGS_NETWORK_API_URL)


# Avoid validation when building docs
if not environ.get('READTHEDOCS', False):
    try:
        url(SATNOGS_NETWORK_API_URL)
    except:
        raise Exception('Invalid SATNOGS_NETWORK_API_URL: {0}'.format(SATNOGS_NETWORK_API_URL))

    if not SATNOGS_STATION_ID:
        raise Exception('SATNOGS_STATION_ID not configured.')

    if not SATNOGS_STATION_LAT:
        raise Exception('SATNOGS_STATION_LAT not configured')

    if not SATNOGS_STATION_LON:
        raise Exception('SATNOGS_STATION_LON not configured')

    if SATNOGS_STATION_ELEV is None:
        raise Exception('SATNOGS_STATION_ELEV not configured')

    if not SATNOGS_API_TOKEN:
        raise Exception('SATNOGS_API_TOKEN not configured')

    logging.config.dictConfig(DEFAULT_LOGGING)
