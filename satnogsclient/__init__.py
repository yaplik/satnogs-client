from validators.url import url

from satnogsclient import settings


try:
    url(settings.NETWORK_API_URL)
except:
    raise Exception('Invalid NETWORK_API_URL: {0}'.format(settings.NETWORK_API_URL))

if not settings.GROUND_STATION_ID:
    raise Exception('Missing required GROUND_STATION_ID from settings.')
