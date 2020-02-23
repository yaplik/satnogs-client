"""
SatNOGS Client module initialization
"""
from __future__ import absolute_import, division, print_function

import logging
import logging.config
import time

import sentry_sdk
from validators.url import url

from satnogsclient import config, settings
from satnogsclient.locator import locator
from satnogsclient.scheduler.tasks import status_listener


__author__ = config.AUTHOR
__email__ = config.EMAIL
__version__ = config.VERSION

logging.basicConfig(format=settings.LOG_FORMAT, level=getattr(logging, settings.LOG_LEVEL))
LOGGER = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


def main():
    """
    Main function
    """
    try:
        url(settings.SATNOGS_NETWORK_API_URL)
    except ValueError:
        raise Exception('Invalid SATNOGS_NETWORK_API_URL: {0}'.format(settings.SATNOGS_NETWORK_API_URL))

    if not settings.SATNOGS_STATION_ID:
        raise Exception('SATNOGS_STATION_ID not configured.')

    if not (settings.SATNOGS_STATION_LAT or settings.GPSD_ENABLED):
        raise Exception('SATNOGS_STATION_LAT not configured')

    if not (settings.SATNOGS_STATION_LON or settings.GPSD_ENABLED):
        raise Exception('SATNOGS_STATION_LON not configured')

    if settings.SATNOGS_STATION_ELEV is None and settings.settings.GPSD_ENABLED is False:
        raise Exception('SATNOGS_STATION_ELEV not configured')

    if not settings.SATNOGS_API_TOKEN:
        raise Exception('SATNOGS_API_TOKEN not configured')

    LOGGER.info('Starting status listener thread...')
    gps_locator = locator.Locator(120)
    gps_locator.update_location()
    status_listener()
    LOGGER.info('Press Ctrl+C to exit SatNOGS poller')
    while True:
        time.sleep(10)
