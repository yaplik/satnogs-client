# -*- coding: utf-8 -*-
from satnogsclient.web.weblogger import WebLogger
import logging
import sys

from datetime import datetime

import ephem
import pytz


logging.setLoggerClass(WebLogger)
logger = logging.getLogger('default')
assert isinstance(logger, WebLogger)


def pinpoint(observer_dict, satellite_dict, timestamp=None):
    """
    Provides azimuth and altitude of tracked object.

    args:
        observer_dict: dictionary with details of observation point.
        satellite_dict: dictionary with details of satellite.
        time: timestamp we want to use for pinpointing the observed object.

        returns:
            Dictionary containing azimuth, altitude and "ok" for error detection.
    """
    # observer object
    if all(map(lambda x: x in observer_dict, ['lat', 'lon', 'elev'])):
        logger.debug('Observer data: {0}'.format(observer_dict))
        observer = ephem.Observer()
        observer.lon = str(observer_dict['lon'])
        observer.lat = str(observer_dict['lat'])
        observer.elevation = float(observer_dict['elev'])
    else:
        logger.error('Something went wrong: {0}'.format(observer_dict))
        return {'ok': False}

    # satellite object
    if all(map(lambda x: x in satellite_dict, ['tle0', 'tle1', 'tle2'])):
        logger.debug('Satellite data: {0}'.format(satellite_dict))
        tle0 = str(satellite_dict['tle0'])
        tle1 = str(satellite_dict['tle1'])
        tle2 = str(satellite_dict['tle2'])
        try:
            satellite = ephem.readtle(tle0, tle1, tle2)
        except:
            logger.error('Something went wrong: {0}'.format(satellite_dict))
            logger.error(sys.exc_info()[0])
            return {'ok': False}
    else:
        return {'ok': False}

    # time of observation
    if not timestamp:
        timestamp = datetime.now(pytz.utc)

    # observation calculation
    observer.date = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
    satellite.compute(observer)
    calculated_data = {
        'alt': satellite.alt,
        'az': satellite.az,
        'rng': satellite.range,
        'rng_vlct': satellite.range_velocity,
        'ok': True
    }

    logger.debug('Calculated data: {0}'.format(calculated_data))
    return calculated_data
