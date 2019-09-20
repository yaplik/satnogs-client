"""
SatNOGS Client module initialization
"""
from __future__ import absolute_import, division, print_function

import logging
import logging.config
import time

from validators.url import url

import satnogsclient.config
from satnogsclient.locator import locator
from satnogsclient.scheduler.tasks import status_listener
from satnogsclient.settings import GPSD_ENABLED, LOG_FORMAT, LOG_LEVEL, \
    SATNOGS_API_TOKEN, SATNOGS_NETWORK_API_URL, SATNOGS_STATION_ELEV, \
    SATNOGS_STATION_ID, SATNOGS_STATION_LAT, SATNOGS_STATION_LON

__author__ = satnogsclient.config.AUTHOR
__email__ = satnogsclient.config.EMAIL
__version__ = satnogsclient.config.VERSION

logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger(__name__)


def main():
    """
    Main function
    """
    try:
        url(SATNOGS_NETWORK_API_URL)
    except ValueError:
        raise Exception('Invalid SATNOGS_NETWORK_API_URL: {0}'.format(SATNOGS_NETWORK_API_URL))

    if not SATNOGS_STATION_ID:
        raise Exception('SATNOGS_STATION_ID not configured.')

    if not (SATNOGS_STATION_LAT or GPSD_ENABLED):
        raise Exception('SATNOGS_STATION_LAT not configured')

    if not (SATNOGS_STATION_LON or GPSD_ENABLED):
        raise Exception('SATNOGS_STATION_LON not configured')

    if SATNOGS_STATION_ELEV is None and GPSD_ENABLED is False:
        raise Exception('SATNOGS_STATION_ELEV not configured')

    if not SATNOGS_API_TOKEN:
        raise Exception('SATNOGS_API_TOKEN not configured')

    LOGGER.info('Starting status listener thread...')
    gps_locator = locator.Locator(120)
    gps_locator.update_location()
    status_listener()
    LOGGER.info('Press Ctrl+C to exit SatNOGS poller')
    while True:
        time.sleep(10)
