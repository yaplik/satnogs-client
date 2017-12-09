"""
SatNOGS Client module initialization
"""
from __future__ import absolute_import

import logging
import logging.config
import threading
import time

from validators.url import url

from satnogsclient.settings import (SATNOGS_API_TOKEN, DEFAULT_LOGGING, SATNOGS_STATION_ID,
                                    SATNOGS_STATION_LAT, SATNOGS_STATION_LON, SATNOGS_STATION_ELEV,
                                    SATNOGS_NETWORK_API_URL)
from satnogsclient.scheduler.tasks import status_listener, exec_rigctld

__author__ = "SatNOGS project"
__email__ = "dev@satnogs.org"
__version__ = "0.3"

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

    if not SATNOGS_STATION_LAT:
        raise Exception('SATNOGS_STATION_LAT not configured')

    if not SATNOGS_STATION_LON:
        raise Exception('SATNOGS_STATION_LON not configured')

    if SATNOGS_STATION_ELEV is None:
        raise Exception('SATNOGS_STATION_ELEV not configured')

    if not SATNOGS_API_TOKEN:
        raise Exception('SATNOGS_API_TOKEN not configured')

    logging.config.dictConfig(DEFAULT_LOGGING)

    LOGGER.info('Starting status listener thread...')
    ser = threading.Thread(target=status_listener, args=())
    ser.daemon = True
    ser.start()
    exec_rigctld()
    LOGGER.info('Press Ctrl+C to exit SatNOGS poller')
    while True:
        time.sleep(10)
