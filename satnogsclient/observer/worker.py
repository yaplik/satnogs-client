# -*- coding: utf-8 -*-
import threading
import time

from datetime import datetime

import pytz

from satnogsclient import settings
from satnogsclient.observer.commsocket import Commsocket
from satnogsclient.observer.orbital import pinpoint


class Worker:
    """Class to facilitate as a worker for rotctl/rigctl."""

    # socket to connect to
    _IP = None
    _PORT = None

    # sleep time of loop
    SLEEP_TIME = 0.1  # in seconds

    # loop flag
    _stay_alive = False

    # debug flag
    _debugmode = False

    # end when this timestamp is reached
    _observation_end = None

    # frequency of original signal
    _frequency = None

    observer_dict = {}
    satellite_dict = {}

    def __init__(self, ip=None, port=None, frequency=None, time_to_stop=None):
        if ip:
            self._IP = ip
        if port:
            self._PORT = port
        if frequency:
            self._frequency = frequency
        if time_to_stop:
            self._observation_end = time_to_stop

    def isalive(self):
        """Returns if tracking loop is alive or not."""
        return self._stay_alive

    def trackobject(self, observer_dict, satellite_dict):
        """
        Sets tracking object.
        Can also be called while tracking, to manipulate observation.
        """
        self.observer_dict = observer_dict
        self.satellite_dict = satellite_dict

    def trackstart(self):
        """
        Starts the thread that communicates tracking info to remote socket.
        Stops by calling trackstop()
        """
        self._stay_alive = True

        if not all([self.observer_dict, self.satellite_dict]):
            raise ValueError('Satellite or observer dictionary not defined.')

        t = threading.Thread(target=self._communicate_tracking_info)
        t.daemon = True
        t.start()

        return True

    def send_to_socket(self):
        # Need to be implemented in freq/track workers implicitly
        pass

    def _communicate_tracking_info(self):
        """
        Runs as a daemon thread, communicating tracking info to remote socket.
        Uses observer and satellite objects set by trackobject().
        Will exit when observation_end timestamp is reached.
        """
        if self._debugmode:
            print(('alive:', self._stay_alive))
        else:
            sock = Commsocket()
            sock.connect(self._IP, self._PORT)  # change to correct address

        # track satellite
        while self._stay_alive:

            # check if we need to exit
            self.check_observation_end_reached()

            if self._debugmode:
                print(('Tracking', self.satellite_dict['tle0']))
                print('from', self.observer_dict['elev'])
            else:
                p = pinpoint(self.observer_dict, self.satellite_dict)
                if p['ok']:
                    self.send_to_socket(p, sock)
                    time.sleep(self.SLEEP_TIME)

        if self._debugmode:
            print('Worker thread exited.')
        else:
            sock.disconnect()

    def trackstop(self):
        """ Sets object flag to false and stops the tracking thread.
        """
        self._stay_alive = False

    def check_observation_end_reached(self):
        if datetime.now(pytz.utc) > self._observation_end:
            self.trackstop()


class WorkerTrack(Worker):
    _IP = settings.ROT_IP
    _PORT = settings.ROT_PORT

    def send_to_socket(self, p, sock):
        az = p['az'].conjugate()
        alt = p['alt'].conjugate()
        msg = 'P {0} {1}\n'.format(az, alt)
        sock.send(msg)


class WorkerFreq(Worker):
    _IP = settings.RIG_IP
    _PORT = settings.RIG_PORT

    def send_to_socket(self, p, sock):
        msg = 'F{0}\n'.format(self._frequency)
        sock.send(msg)
