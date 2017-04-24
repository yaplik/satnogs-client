# -*- coding: utf-8 -*-
from satnogsclient.web.weblogger import WebLogger
import logging
import math
import threading
import time
import json
import os
import signal

from datetime import datetime

import ephem
import pytz

from flask_socketio import SocketIO
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.orbital import pinpoint


logging.setLoggerClass(WebLogger)
logger = logging.getLogger('default')
assert isinstance(logger, WebLogger)
socketio = SocketIO(message_queue='redis://')


class Worker:

    """Class to facilitate as a worker for rotctl/rigctl."""

    # sleep time of loop (in seconds)
    SLEEP_TIME = 0.1

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

    def __init__(self, ip, port, time_to_stop=None, frequency=None, proc=None):
        """Initialize worker class."""
        self._IP = ip
        self._PORT = port
        if frequency:
            self._frequency = frequency
        if time_to_stop:
            self._observation_end = time_to_stop
        if proc:
            self._gnu_proc = proc

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

    def trackstart(self, port, start_thread):
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

        if start_thread:
            self.r = threading.Thread(
                target=self._status_interface, args=(port,))
            self.r.daemon = True
            self.r.start()

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
                dict = {'azimuth': p['az'].conjugate() * 180 / math.pi,
                        'altitude': p['alt'].conjugate() * 180 / math.pi,
                        'frequency': self._frequency * (1 - (p['rng_vlct'] / ephem.c)),
                        'tle0': self.satellite_dict['tle0'],
                        'tle1': self.satellite_dict['tle1'],
                        'tle2': self.satellite_dict['tle2']}
                socketio.emit('update_rotator', dict, namespace='/update_status')
                self.send_to_socket(p, sock)
                time.sleep(self.SLEEP_TIME)

        sock.disconnect()

    def _status_interface(self, port):
        sock = Commsocket('127.0.0.1', port)
        # sock.get_sock().bind(('127.0.0.1',port))
        sock.bind()
        sock.listen()
        while self.is_alive:
            conn = sock.accept()
            if conn:
                conn.recv(sock.buffer_size)
                dict = {'azimuth': "{0:.2f}".format(self._azimuth),
                        'altitude': "{0:.2f}".format(self._altitude),
                        'frequency': self._frequency,
                        'tle0': self.satellite_dict['tle0'],
                        'tle1': self.satellite_dict['tle1'],
                        'tle2': self.satellite_dict['tle2']}
                conn.send(json.dumps(dict))
                conn.close()

    def trackstop(self):
        """
        Sets object flag to false and stops the tracking thread.
        """
        logger.info('Tracking stopped.')
        self.is_alive = False
        if self._gnu_proc:
            os.killpg(os.getpgid(self._gnu_proc.pid), signal.SIGKILL)

    def check_observation_end_reached(self):
        if datetime.now(pytz.utc) > self._observation_end:
            self.trackstop()


class WorkerTrack(Worker):

    def send_to_socket(self, p, sock):
        # Read az/alt and convert to radians
        az = p['az'].conjugate() * 180 / math.pi
        alt = p['alt'].conjugate() * 180 / math.pi
        self._azimuth = az
        self._altitude = alt
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
