import logging
import math
import threading
import time
import os
import signal

from datetime import datetime

import ephem
import pytz

from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.orbital import pinpoint

from satnogsclient import settings


logger = logging.getLogger('default')


class Worker:

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

    _post_exec_script = None

    observer_dict = {}
    satellite_dict = {}

    def __init__(self, ip, port, time_to_stop=None, frequency=None, proc=None,
                 sleep_time=None, _post_exec_script=None):
        """Initialize worker class."""
        self._IP = ip
        self._PORT = port
        if frequency:
            self._frequency = frequency
        if time_to_stop:
            self._observation_end = time_to_stop
        if proc:
            self._gnu_proc = proc
        if sleep_time:
            self._sleep_time = sleep_time
        if _post_exec_script is not None:
            self._post_exec_script = _post_exec_script

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
        logger.info('Tracking initiated')
        if not all([self.observer_dict, self.satellite_dict]):
            raise ValueError('Satellite or observer dictionary not defined.')

        self.t = threading.Thread(target=self._communicate_tracking_info)
        self.t.daemon = True
        self.t.start()

        return self.is_alive

    def send_to_socket(self):
        # Needs to be implemented in freq/track workers implicitly
        raise NotImplementedError

    def _communicate_tracking_info(self):
        """
        Runs as a daemon thread, communicating tracking info to remote socket.
        Uses observer and satellite objects set by trackobject().
        Will exit when observation_end timestamp is reached.
        """
        sock = Commsocket(self._IP, self._PORT)
        sock.connect()

        # track satellite
        while self.is_alive:

            # check if we need to exit
            self.check_observation_end_reached()

            p = pinpoint(self.observer_dict, self.satellite_dict)
            if p['ok']:
                self.send_to_socket(p, sock)
                time.sleep(self._sleep_time)

        sock.disconnect()

    def trackstop(self):
        """
        Sets object flag to false and stops the tracking thread.
        """
        logger.info('Tracking stopped.')
        self.is_alive = False
        if self._gnu_proc:
            os.killpg(os.getpgid(self._gnu_proc.pid), signal.SIGINT)
        if self._post_exec_script is not None:
            logger.info('Executing post-observation script.')
            os.system(self._post_exec_script)

    def check_observation_end_reached(self):
        if datetime.now(pytz.utc) > self._observation_end:
            self.trackstop()


class WorkerTrack(Worker):

    def send_to_socket(self, p, sock):
        # Read az/alt of sat and convert to radians
        az = p['az'].conjugate() * 180 / math.pi
        alt = p['alt'].conjugate() * 180 / math.pi
        self._azimuth = az
        self._altitude = alt
        # read current position of rotator, [0] az and [1] el
        position = sock.send("p\n").split('\n')
        # if the need to move exceeds threshold, then do it
        if (position[0].startswith("RPRT") or
            abs(az - float(position[0])) > settings.SATNOGS_ROT_THRESHOLD or
                abs(alt - float(position[1])) > settings.SATNOGS_ROT_THRESHOLD):
                    msg = 'P {0} {1}\n'.format(az, alt)
                    logger.debug('Rotctld msg: {0}'.format(msg))
                    sock.send(msg)


class WorkerFreq(Worker):

    def send_to_socket(self, p, sock):
        doppler_calc_freq = self._frequency * (1 - (p['rng_vlct'] / ephem.c))
        msg = 'F {0}\n'.format(int(doppler_calc_freq))
        logger.debug('Initial frequency: {0}'.format(self._frequency))
        logger.debug('Rigctld msg: {0}'.format(msg))
        sock.send(msg)
