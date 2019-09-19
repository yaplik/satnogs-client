import logging
import logging.config
import time

import gps

from satnogsclient import settings

LOGGER = logging.getLogger(__name__)


class Locator(object):
    def __init__(self, timeout):
        self.timeout = timeout

    def show_location(self, gpsd):
        print('mode        ', gpsd.fix.mode)
        print('status      ', gpsd.status)
        print('eps         ', gpsd.fix.eps)
        print('epx         ', gpsd.fix.epx)
        print('epv         ', gpsd.fix.epv)
        print('ept         ', gpsd.fix.ept)
        print('climb       ', gpsd.fix.climb)
        print('hdop        ', gpsd.hdop)
        print('timeout     ', self.timeout)

    def update_location(self):
        if settings.GPSD_ENABLED is not True:
            return
        no_timeout = (self.timeout == 0)
        if (settings.SATNOGS_STATION_LAT is None or settings.SATNOGS_STATION_LON is None
                or settings.SATNOGS_STATION_ELEV is None):
            no_timeout = True
            LOGGER.info('No default coordinates, GPS timeout disabled')
        else:
            LOGGER.info('Last coordinates %f %f %d', settings.SATNOGS_STATION_LAT,
                        settings.SATNOGS_STATION_LON, settings.SATNOGS_STATION_ELEV)
        end_time = time.time() + self.timeout

        try:
            gpsd = gps.gps(mode=gps.WATCH_ENABLE)
            gpsd.next()
            LOGGER.info("Waiting for GPS")
            while gpsd.fix.mode != gps.MODE_3D and (time.time() < end_time or no_timeout):
                # self.show_location(gpsd)
                self.timeout -= 1
                gpsd.next()
        except StopIteration:
            LOGGER.info('GPSD connection failed')
            return
        if gpsd.fix.mode == gps.MODE_3D:
            settings.SATNOGS_STATION_LAT = gpsd.fix.latitude
            settings.SATNOGS_STATION_LON = gpsd.fix.longitude
            settings.SATNOGS_STATION_ELEV = gpsd.fix.altitude
            LOGGER.info('Updating coordinates %f %f %d', settings.SATNOGS_STATION_LAT,
                        settings.SATNOGS_STATION_LON, settings.SATNOGS_STATION_ELEV)
        else:
            LOGGER.info("GPS timeout, using last known coordinates")
