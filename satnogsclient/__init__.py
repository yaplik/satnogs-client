from validators.url import url

from satnogsclient import settings


try:
    url(settings.NETWORK_API_URL)
except:
    raise Exception('Invalid NETWORK_API_URL: {0}'.format(settings.NETWORK_API_URL))

if not settings.GROUND_STATION_ID:
    raise Exception('GROUND_STATION_ID not configured.')

if not settings.GROUND_STATION_LAT:
    raise Exception('GROUND_STATION_LAT not configured')

if not settings.GROUND_STATION_LON:
    raise Exception('GROUND_STATION_LON not configured')

if not settings.GROUND_STATION_ELEV:
    raise Exception('GROUND_STATION_ELEV not configured')
