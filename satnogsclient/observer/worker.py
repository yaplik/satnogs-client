from __future__ import absolute_import, division, print_function

import logging
import math
import threading
import time
from datetime import datetime, timedelta

import ephem
import Hamlib
import pytz

from satnogsclient import settings
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.orbital import pinpoint
from satnogsclient.radio import Radio
from satnogsclient.rotator import Rotator

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

            pin = pinpoint(self.observer_dict, self.satellite_dict)
            if pin['ok']:
                self.send_to_socket(pin, sock)
                time.sleep(self._sleep_time)

        sock.disconnect()

    def trackstop(self):
        """
        Sets object flag to false and stops the tracking thread.
        """
        self.is_alive = False
        self.track.join()
        LOGGER.info('Tracking stopped.')


class WorkerTrack(Worker):
    _midpoint = None
    _flip = False

    def _communicate_tracking_info(self):
        """
        Runs as a daemon thread, communicating tracking info to remote socket.
        Uses observer and satellite objects set by trackobject().
        Will exit when observation_end timestamp is reached.
        """
        rotator = Rotator(settings.SATNOGS_ROT_MODEL, settings.SATNOGS_ROT_BAUD,
                          settings.SATNOGS_ROT_PORT)
        rotator.open()

        # track satellite
        while self.is_alive:

            pin = pinpoint(self.observer_dict, self.satellite_dict)
            if pin['ok']:
                self.send_to_socket(pin, rotator)
                time.sleep(self._sleep_time)

        rotator.close()

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
        # Read az/alt of sat and convert to degrees
        azi = pin['az'].conjugate() * 180 / math.pi
        alt = pin['alt'].conjugate() * 180 / math.pi
        if self._flip:
            azi, alt = WorkerTrack.flip_coordinates(azi, alt, datetime.now(pytz.utc),
                                                    self._midpoint)
        self._azimuth = azi
        self._altitude = alt
        # read current position of rotator in degrees
        (cur_azi, cur_alt) = sock.position
        # if the need to move exceeds threshold, then do it
        # Take the 360 modulus of the azimuth position, to handle rotators that report
        # positions in overwind regions as values outside the range 0-360.
        if (abs(azi - cur_azi % 360.0) > settings.SATNOGS_ROT_THRESHOLD
                or abs(alt - cur_alt) > settings.SATNOGS_ROT_THRESHOLD):
            msg = (azi, alt)
            LOGGER.debug('Rotctld msg: %s', msg)
            sock.position = msg


class WorkerFreq(Worker):
    def _communicate_tracking_info(self):
        """
        Runs as a daemon thread, communicating tracking info to remote socket.
        Uses observer and satellite objects set by trackobject().
        Will exit when observation_end timestamp is reached.
        """
        radio = Radio(Hamlib.RIG_MODEL_NETRIGCTL, "{}:{}".format(self._ip, self._port))
        radio.open()

        # track satellite
        while self.is_alive:

            pin = pinpoint(self.observer_dict, self.satellite_dict)
            if pin['ok']:
                self.send_to_socket(pin, radio)
                time.sleep(self._sleep_time)

        radio.close()

    def send_to_socket(self, pin, sock):
        doppler_calc_freq = self._frequency * (1 - (pin['rng_vlct'] / ephem.c))
        msg = int(doppler_calc_freq)
        LOGGER.debug('Initial frequency: %s', self._frequency)
        LOGGER.debug('Rigctld msg: %s', msg)
        sock.frequency = msg
