from os import environ

from validators.url import url

from satnogsclient.settings import (NETWORK_API_URL, GROUND_STATION_ID, GROUND_STATION_LAT,
                                    GROUND_STATION_LON, GROUND_STATION_ELEV)


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

    if not GROUND_STATION_ELEV:
        raise Exception('GROUND_STATION_ELEV not configured')
