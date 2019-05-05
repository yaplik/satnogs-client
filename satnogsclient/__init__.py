"""
SatNOGS Client module initialization
"""
from __future__ import absolute_import, division, print_function

import logging
import logging.config
import threading
import time

from validators.url import url

import satnogsclient.config
from satnogsclient.settings import (SATNOGS_API_TOKEN, DEFAULT_LOGGING, SATNOGS_STATION_ID,
                                    SATNOGS_STATION_LAT, SATNOGS_STATION_LON, SATNOGS_STATION_ELEV,
                                    SATNOGS_NETWORK_API_URL, GPSD_ENABLED)
from satnogsclient.scheduler.tasks import status_listener, exec_rigctld
from satnogsclient.locator import locator

__author__ = satnogsclient.config.AUTHOR
__email__ = satnogsclient.config.EMAIL
__version__ = satnogsclient.config.VERSION

LOGGER = logging.getLogger('satnogsclient')


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

    logging.config.dictConfig(DEFAULT_LOGGING)
    LOGGER.info('Starting status listener thread...')
    gps_locator = locator.Locator(120)
    gps_locator.update_location()
    ser = threading.Thread(target=status_listener, args=())
    ser.daemon = True
    ser.start()
    exec_rigctld()
    LOGGER.info('Press Ctrl+C to exit SatNOGS poller')
    while True:
        time.sleep(10)
