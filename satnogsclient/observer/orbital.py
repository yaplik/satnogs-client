# -*- coding: utf-8 -*-
import sys

from datetime import datetime

import ephem
import pytz


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
        observer = ephem.Observer()
        observer.lon = str(observer_dict['lon'])
        observer.lat = str(observer_dict['lat'])
        observer.elevation = float(observer_dict['elev'])
    else:
        return {'ok': False}

    # satellite object
    if all(map(lambda x: x in satellite_dict, ['tle0', 'tle1', 'tle2'])):
        tle0 = str(satellite_dict['tle0'])
        tle1 = str(satellite_dict['tle1'])
        tle2 = str(satellite_dict['tle2'])
        try:
            satellite = ephem.readtle(tle0, tle1, tle2)
        except ValueError:
            print(('error:', 'ephem object', 'tle values', sys.exc_info()[0]))
            return {'ok': False}
        except:
            print(('error:', 'ephem object', sys.exc_info()[0]))
            return {'ok': False}
    else:
        return {'ok': False}

    # time of observation
    if not timestamp:
        timestamp = datetime.now(pytz.utc)

    # observation calculation
    observer.date = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
    satellite.compute(observer)
    return {'alt': satellite.alt, 'az': satellite.az,
            'rng': satellite.range, 'rng_vlct': satellite.range_velocity,
            'ok': True}
