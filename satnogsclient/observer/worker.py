from __future__ import absolute_import, division, print_function

import logging
import math
import os
import signal
import threading
import time
from datetime import datetime, timedelta

import ephem
import pytz

from satnogsclient import settings
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.orbital import pinpoint

LOGGER = logging.getLogger(__name__)


class Worker(object):
    """Class to facilitate as a worker for rotctl/rigctl."""

    # sleep time of loop (in seconds)
    _sleep_time = 0.1

    # loop flag
    _stay_alive = False

    # end when this timestamp is reached
    _observation_end = None

    # frequency of original signal
    _frequency = None

    _azimuth = None
    _altitude = None
    _gnu_proc = None

    observer_dict = {}
    satellite_dict = {}

    def __init__(self, ip, port, time_to_stop=None, frequency=None, proc=None, sleep_time=None):
        """Initialize worker class."""
        self._ip = ip
        self._port = port
        if frequency:
            self._frequency = frequency
        if time_to_stop:
            self._observation_end = time_to_stop
        if proc:
            self._gnu_proc = proc
        if sleep_time:
            self._sleep_time = sleep_time
        self.track = None

    @property
    def is_alive(self):
        """Returns if tracking loop is alive or not."""
        return self._stay_alive

    @is_alive.setter
    def is_alive(self, value):
        """Sets value if tracking loop is alive or not."""
        self._stay_alive = value

    def trackobject(self, observer_dict, satellite_dict):
        """
        Sets tracking object.
        Can also be called while tracking to manipulate observation.
        """
        self.observer_dict = observer_dict
        self.satellite_dict = satellite_dict

    def trackstart(self):
        """
        Starts the thread that communicates tracking info to remote socket.
        Stops by calling trackstop()
        """
        self.is_alive = True
        LOGGER.info('Tracking initiated')
        if not all([self.observer_dict, self.satellite_dict]):
            raise ValueError('Satellite or observer dictionary not defined.')

        self.track = threading.Thread(target=self._communicate_tracking_info)
        self.track.daemon = True
        self.track.start()

        return self.is_alive

    def send_to_socket(self, pin, sock):
        # Needs to be implemented in freq/track workers implicitly
        raise NotImplementedError

    def _communicate_tracking_info(self):
        """
        Runs as a daemon thread, communicating tracking info to remote socket.
        Uses observer and satellite objects set by trackobject().
        Will exit when observation_end timestamp is reached.
        """
        sock = Commsocket(self._ip, self._port)
        sock.connect()

        # track satellite
        while self.is_alive:

            # check if we need to exit
            self.check_observation_end_reached()

            pin = pinpoint(self.observer_dict, self.satellite_dict)
            if pin['ok']:
                self.send_to_socket(pin, sock)
                time.sleep(self._sleep_time)

        sock.disconnect()

    def trackstop(self):
        """
        Sets object flag to false and stops the tracking thread.
        """
        LOGGER.info('Tracking stopped.')
        self.is_alive = False
        if self._gnu_proc:
            os.killpg(os.getpgid(self._gnu_proc.pid), signal.SIGINT)

    def check_observation_end_reached(self):
        if datetime.now(pytz.utc) > self._observation_end:
            self.trackstop()


class WorkerTrack(Worker):
    _midpoint = None
    _flip = False

    @staticmethod
    def find_midpoint(observer_dict, satellite_dict, start):
        # Workaround for https://github.com/brandon-rhodes/pyephem/issues/105
        # pylint: disable=assigning-non-slot
        # Disable until pylint 2.4 is released, see
        # https://github.com/PyCQA/pylint/issues/2807
        start -= timedelta(minutes=1)

        observer = ephem.Observer()
        observer.lon = str(observer_dict["lon"])
        observer.lat = str(observer_dict["lat"])
        observer.elevation = observer_dict["elev"]
        observer.date = ephem.Date(start)

        satellite = ephem.readtle(str(satellite_dict["tle0"]), str(satellite_dict["tle1"]),
                                  str(satellite_dict["tle2"]))

        timestamp_max = pytz.utc.localize(ephem.Date(observer.next_pass(satellite)[2]).datetime())
        pin = pinpoint(observer_dict, satellite_dict, timestamp_max)
        azi_max = pin["az"].conjugate() * 180 / math.pi
        alt_max = pin["alt"].conjugate() * 180 / math.pi

        return (azi_max, alt_max, timestamp_max)

    @staticmethod
    def normalize_angle(num, lower=0, upper=360):
        res = num
        if num > upper or num == lower:
            num = lower + abs(num + upper) % (abs(lower) + abs(upper))
        if num < lower or num == upper:
            num = upper - abs(num - lower) % (abs(lower) + abs(upper))
        res = lower if num == upper else num
        return res

    @staticmethod
    def flip_coordinates(azi, alt, timestamp, midpoint):
        midpoint_azi, midpoint_alt, midpoint_timestamp = midpoint
        if timestamp >= midpoint_timestamp:
            azi = midpoint_azi + (midpoint_azi - azi)
            alt = midpoint_alt + (midpoint_alt - alt)
            return (WorkerTrack.normalize_angle(azi), WorkerTrack.normalize_angle(alt))
        return (azi, alt)

    def trackobject(self, observer_dict, satellite_dict):
        super(WorkerTrack, self).trackobject(observer_dict, satellite_dict)

        if settings.SATNOGS_ROT_FLIP and settings.SATNOGS_ROT_FLIP_ANGLE:
            self._midpoint = WorkerTrack.find_midpoint(observer_dict, satellite_dict,
                                                       datetime.now(pytz.utc))
            LOGGER.info("Antenna midpoint: AZ%.2f EL%.2f %s", *self._midpoint)
            self._flip = (self._midpoint[1] >= settings.SATNOGS_ROT_FLIP_ANGLE)
            LOGGER.info("Antenna flip: %s", self._flip)

    def send_to_socket(self, pin, sock):
        # Read az/alt of sat and convert to radians
        azi = pin['az'].conjugate() * 180 / math.pi
        alt = pin['alt'].conjugate() * 180 / math.pi
        if self._flip:
            azi, alt = WorkerTrack.flip_coordinates(azi, alt, datetime.now(pytz.utc),
                                                    self._midpoint)
        self._azimuth = azi
        self._altitude = alt
        # read current position of rotator, [0] az and [1] el
        position = sock.send("p\n").split('\n')
        # if the need to move exceeds threshold, then do it
        if (position[0].startswith("RPRT")
                or abs(azi - float(position[0])) > settings.SATNOGS_ROT_THRESHOLD
                or abs(alt - float(position[1])) > settings.SATNOGS_ROT_THRESHOLD):
            msg = 'P {0} {1}\n'.format(azi, alt)
            LOGGER.debug('Rotctld msg: %s', msg)
            sock.send(msg)


class WorkerFreq(Worker):
    def send_to_socket(self, pin, sock):
        doppler_calc_freq = self._frequency * (1 - (pin['rng_vlct'] / ephem.c))
        msg = 'F {0}\n'.format(int(doppler_calc_freq))
        LOGGER.debug('Initial frequency: %s', self._frequency)
        LOGGER.debug('Rigctld msg: %s', msg)
        sock.send(msg)
