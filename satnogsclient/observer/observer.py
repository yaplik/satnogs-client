# -*- coding: utf-8 -*-
from satnogsclient import settings
from satnogclient.observer.worker import WorkerFreq, WorkerTrack


class Observer:

    _location = None
    _tle = None
    _observation_end = None
    _frequency = None

    _rot_ip = settings.ROT_IP
    _rot_port = settings.ROT_PORT

    _rig_ip = settings.RIG_IP
    _rig_port = settings.RIG_PORT

    @property
    def location(self, location):
        if location:
            self._location = location
        return location

    @property
    def tle(self, tle):
        if tle:
            self._tle = tle
        return self._tle

    @property
    def rot_ip(self, ip):
        if ip:
            self._rot_ip = ip
        return self._rot_ip

    @property
    def rot_port(self, port):
        if port:
            self._rot_port = port
        return self._rot_port

    @property
    def rig_ip(self, ip):
        if ip:
            self._rig_ip = ip
        return self._rig_ip

    @property
    def rig_port(self, port):
        if port:
            self._rig_port = port
        return self._rig_port

    @property
    def observation_end(self, timestamp):
        if timestamp:
            self._observation_end = timestamp
        return self._observation_end

    @property
    def frequency(self, frequency):
        if frequency:
            self._frequency = frequency
        return self._frequency

    def setup(self, tle, observation_end, frequency):
        """
        Sets up required internal variables.
        returns True if setup is ok
        returns False if setup had problems
        """
        checks = [tle == self.tle(tle),
                  observation_end == self.observation_end(observation_end),
                  frequency == self.frequency(frequency)]

        return all(checks)

    def observe(self):
        """Starts threads for rotcrl and rigctl."""

        # start thread for rotctl
        self.run_rot()

        # start thread for rigctl
        self.run_rig()

    def run_rot(self):
        self.tracker_rot = WorkerTrack(time_to_stop=self._observation_end)
        self.tracker_rot.trackobject(self._location, self._tle)
        self.tracker_rot.trackstart()

    def run_rig(self):
        self.tracker_freq = WorkerFreq(frequency=self._frequency,
                                       time_to_stop=self._observation_end)
        self.tracker_freq.trackobject(self._location, self._tle)
        self.tracker_freq.trackstart()
